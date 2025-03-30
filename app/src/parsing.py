import json, time
from datetime import datetime

from app.src.classes import HL7Segment, HL7Message
from app.src.constants import segments, ignored_subfield_ids
from app.src.utils import clean_null_entries, create_message_summaries, adjust_datetime, replace_deidentified_fields, update_summary

# from classes import HL7Message, HL7Segment
# from constants import segments, ignored_subfield_ids
# from utils import clean_null_entries, create_message_summaries, adjust_datetime, replace_deidentified_fields, update_summary

def redact_phi_value(value):
    """Redact a value by replacing its characters with asterisks."""
    return '*' * len(value) if value else value

def convert_to_age(birthdate_str):
    """Convert birthdate to age. If age is greater than 89, group as '90+'."""
    if birthdate_str:
        birthdate = datetime.strptime(birthdate_str, "%Y%m%d")
        today = datetime.today()
        age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
        return "90+" if age >= 90 else str(age)
    return age

def redact_and_store_subfields(field_value, field_id, phi_data, redact):
    """Redact each subfield value if redact flag is True, unless the subfield is in ignored_subfield_ids."""
    
    if field_value:
        subfields = field_value.split("^")
        redacted_subfields = []
        
        for i, subfield in enumerate(subfields):
            subfield_id = f"{field_id}.{i+1}"
            
            if redact and subfield and len(subfield) > 0 and (subfield_id not in ignored_subfield_ids):
                phi_data.append(subfield)
                redacted_subfields.append(redact_phi_value(subfield))

            else: redacted_subfields.append(subfield)

        return "^".join(redacted_subfields)
    return field_value


def parse_message(hl7_message, redact_phi=False, deidentify=True):
    message_obj = HL7Message()
    lines = hl7_message.split("\n")
    phi_data = []

    for line in lines:
        if not line.strip():
            continue

        segments_data = line.split("\r")

        for segment_line in segments_data:
            segment_type = segment_line[:3]

            if segment_type in segments:
                current_segment = HL7Segment(segment_type)

                if segment_type != "MSH":
                    fields = segment_line.split("|")[1:]
                else:
                    field_separator = segment_line[3]
                    delimiters = segment_line[4:8]

                    current_segment.add_field("MSH-1", "Field Separator", field_separator)
                    current_segment.add_field("MSH-2", "Encoding Characters", delimiters)

                    fields = segment_line.split("|")[2:]

                expected_fields = segments[current_segment.segment_name].keys()

                for i, field in enumerate(fields):
                    field_name = f"{current_segment.segment_name}-{i+3}" if current_segment.segment_name == "MSH" else f"{current_segment.segment_name}-{i+1}"

                    if field_name in expected_fields:
                        field_description = segments[current_segment.segment_name].get(field_name, "No Description")

                        PID_REDACT = ["PID-5", "PID-7", "PID-11", "PID-13", "PID-14", "PID-18", "PID-19"]

                        if field_name in PID_REDACT: field = redact_and_store_subfields(field,field_name,phi_data, redact_phi)

                        current_segment.add_field(field_name, field_description, field)

                message_obj.add_segment(current_segment.segment_name, current_segment)

    if redact_phi:
        for segment_name, segment in message_obj.segments.items():
            for field_name, field_details in segment.fields.items():
                subfields = field_details.get("Subfields", {})

                # Ensure subfields is a dictionary
                if isinstance(subfields, dict):
                    for subfield_key, subfield_value in subfields.items():
                        for original_value in phi_data:
                            if original_value in subfield_value:
                                subfields[subfield_key] = redact_phi_value(original_value)

    return message_obj, phi_data


def parse_lines(lines, deidentify=True, redact_phi=False):
    parsed_messages = {}
    current_message = []
    raw_messages = {}
    phi_data_all = {}  # To store the PHI data for each message

    for line in lines:
        if line.startswith("MSH"):
            if current_message:
                full_message = "\n".join(current_message)

                # Capture both parsed message and redacted PHI data
                parsed_message, phi_data = parse_message(full_message, redact_phi=False, deidentify=deidentify)
                message_id = parsed_message.get_message_control_id() or f"message_{len(parsed_messages) + 1}"
                raw_messages[message_id] = full_message
                parsed_messages[message_id] = parsed_message.to_dict()
                phi_data_all[message_id] = phi_data
            current_message = [line.strip()]
        else:
            current_message.append(line.strip())

    if current_message:
        full_message = "\n".join(current_message)

        # Capture both parsed message and redacted PHI data
        parsed_message, phi_data = parse_message(full_message, redact_phi=False, deidentify=deidentify)
        message_id = parsed_message.get_message_control_id() or f"message_{len(parsed_messages) + 1}"
        parsed_messages[message_id] = parsed_message.to_dict()
        phi_data_all[message_id] = phi_data

    raw_messages[message_id] = current_message

    # Clean and adjust messages
    parsed_messages = {message_id: clean_null_entries(message) for message_id, message in parsed_messages.items()}
    parsed_messages = create_message_summaries(parsed_messages)
    parsed_messages = adjust_datetime(parsed_messages)
    if deidentify:
        parsed_messages = {message_id: replace_deidentified_fields(message) for message_id, message in parsed_messages.items()}
        parsed_messages = {message_id: update_summary(id=message_id, message=message) for message_id, message in parsed_messages.items()}

    return parsed_messages, raw_messages, phi_data_all  # Return PHI data as well

def parse_file(file_path, deidentify=True, redact=True):
    with open(file_path, 'r') as hl7_file:
        lines = hl7_file.readlines()
    return parse_lines(lines, deidentify=deidentify, redact_phi=redact)

def parse_content(file_content: str, deidentify=True, redact=True):
    lines = file_content.splitlines()
    return parse_lines(lines, deidentify=deidentify, redact_phi=redact)



# -------------------------------------------------------------------

### for generating sorted messages
def sort_messages_datetime(file_path):
    parsed, full, phi_data_all = parse_file(file_path)

    # print(len(parsed))
    # print(len(full), flush=True)

    def get_msg_datetime(msg):
        try:
            msg_datetime_str = msg['summary'].get('MSG_DATETIME', None)
            if msg_datetime_str:
                return datetime.strptime(msg_datetime_str, "%Y-%m-%d %H:%M")  # Adjust format as needed
        except (ValueError, KeyError) as e:
            print(f"Error parsing datetime for message: {e}", flush=True)
        
        return datetime.min

    sorted_messages = sorted(parsed.items(), key=lambda item: get_msg_datetime(item[1]))
    in_order = [msg_id for msg_id, msg in sorted_messages]
    sorted_full = {msg_id: full[msg_id] for msg_id in in_order if msg_id in full}

    print(len(sorted_full))

    with open('app/data/messages_redacted.txt', 'w') as sorted_file:
        for msg_id, msg in sorted_full.items():
            if isinstance(msg, list):
                message_str = "\r".join(msg)
            else:
                message_str = msg 

            sorted_file.write(message_str)
            sorted_file.write("\n") 

    # Optionally return or log PHI data
    print(json.dumps(phi_data_all, indent=2), flush=True)


# for initial redact
def redact_hpi(file_path):
    parsed, full, phi_data_all = parse_file(file_path)

    # print(len(parsed))
    # print(len(full), flush=True)

    # Iterate over each message id in phi_data_all
    for message_id, phi_data in phi_data_all.items():
        if message_id in full:
            # Get the raw message
            message = full[message_id]

            # Loop through each value in phi_data and redact it in the message
            for phi_value in phi_data:
                if phi_value in message:
                    # Perform the string replacement (redact by replacing with asterisks)
                    message = message.replace(phi_value, redact_phi_value(phi_value))

            # Update the full dictionary with the redacted message
            full[message_id] = message

    # After redacting, you can now save the redacted messages or process them further
    with open('app/data/messages_redacted.txt', 'w') as redacted_file:
        for msg_id, msg in full.items():
            if isinstance(msg, list):
                message_str = "\r".join(msg)
            else:
                message_str = msg
            redacted_file.write(message_str + "\n")
    
    # print(f"Redaction complete. {len(full)} messages processed.")
    return

def deidentify_hpi(file_path):

    # Iterate over each message id in phi_data_all
    from parsing import parse_file
    from utils import replace_deidentified_fields, update_summary

    parsed_messages, full , phi_data = parse_file(file_path=file_path)

    for message_id, message in parsed_messages.items():
        parsed_messages[message_id] = replace_deidentified_fields(message)
        parsed_messages[message_id]['summary'] = update_summary(parsed_messages[message_id]['summary'])

    # with open('app/data/messages_deidentified.txt', 'w') as deidentified_file:
    #     for msg_id, msg in full.items():
    #         if isinstance(msg, list):
    #             message_str = "\r".join(msg)
    #         elif isinstance(msg, dict):
    #             message_str = json.dumps(msg, indent=2)
    #         else:
    #             message_str = msg
    #         deidentified_file.write(message_str + "\n")

    with open('app/data/messages_deidentified.json', 'w') as deidentified_json_file:
        json.dump(parsed_messages, deidentified_json_file, indent=2)

# Now parsed_messages contains the messages with the deidentified fields replaced.


# sort_messages_datetime('app/data/big.hl7')
# redact_hpi('app/data/big.hl7')
# deidentify_hpi('app/data/big.hl7')