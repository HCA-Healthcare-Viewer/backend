import json, time

# from app.src.classes import HL7Segment, HL7Message
# from app.src.constants import segments
# from app.src.utils import clean_null_entries

from classes import HL7Message, HL7Segment
from constants import segments
from utils import clean_null_entries, create_message_summaries, adjust_datetime


def parse_message(hl7_message):
    message_obj = HL7Message()
    lines = hl7_message.split("\n")

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
                        current_segment.add_field(field_name, field_description, field)

                message_obj.add_segment(current_segment.segment_name, current_segment)

    return message_obj


def parse_lines(lines):
    parsed_messages = {}
    current_message = []
    
    for line in lines:
        if line.startswith("MSH"):
            if current_message:
                full_message = "\n".join(current_message)
                parsed_message = parse_message(full_message)
                message_id = parsed_message.get_message_control_id() or f"message_{len(parsed_messages) + 1}"
                parsed_messages[message_id] = parsed_message.to_dict()
            current_message = [line.strip()]
        else:
            current_message.append(line.strip())
    
    if current_message:
        full_message = "\n".join(current_message)
        parsed_message = parse_message(full_message)
        message_id = parsed_message.get_message_control_id() or f"message_{len(parsed_messages) + 1}"
        parsed_messages[message_id] = parsed_message.to_dict()
    
        parsed_messages = {message_id: clean_null_entries(message) for message_id, message in parsed_messages.items()}
        parsed_messages = create_message_summaries(parsed_messages)
        parsed_messages = adjust_datetime(parsed_messages)
    return parsed_messages

def parse_file(file_path):
    with open(file_path, 'r') as hl7_file:
        lines = hl7_file.readlines()
    return parse_lines(lines)

def parse_content(file_content: str):
    lines = file_content.splitlines()
    return parse_lines(lines)


def custom_dumps(obj, indent=4):
    def recursive_dict(obj):
        if isinstance(obj, dict):
            return {key: recursive_dict(value) if isinstance(value, (dict, HL7Segment)) else value
                    for key, value in obj.items()}
        elif isinstance(obj, HL7Segment):
            return obj.to_dict()
        return obj

    return json.dumps(recursive_dict(obj), indent=indent)



start_time = time.time()
print("Parsing HL7 messages...", flush=True)
parsed_hl7_messages = parse_file('app/data/big.hl7')
print("Parsing completed in", time.time() - start_time, "seconds.", flush=True)

# Write to JSON file with IDs as keys
start_time = time.time()
print("Writing parsed HL7 messages to JSON...", flush=True)
with open('app/data/big_parsed_messages.json', 'w') as json_file:
    json.dump(parsed_hl7_messages, json_file, indent=2)
print("Writing completed in", time.time() - start_time, "seconds.", flush=True)
