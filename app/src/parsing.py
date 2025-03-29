import json
import time

from constants import segments

class HL7Segment:
    def __init__(self, segment_name):
        self.segment_name = segment_name
        self.fields = {}

    def add_field(self, field_name, description, value=None):
        if field_name == "MSH-2":
            self.fields[field_name] = {
                "Field Description": description,
                "Field Value": value if value else None,
                "Subfields": None
            }
            return

        subfields = {}
        if value:
            subfields_values = value.split('^')
            for i, subfield in enumerate(subfields_values, 1):
                subfield_key = f"{field_name}.{i}"
                repeating_values = subfield.split('~')
                subfields[subfield_key] = repeating_values if len(repeating_values) > 1 else subfield
        else:
            subfields = None

        self.fields[field_name] = {
            "Field Description": description,
            "Field Value": value if value else None,
            "Subfields": subfields if subfields else None
        }

    def __repr__(self):
        return f"Segment: {self.segment_name}, Fields: {self.fields}"

    def to_dict(self):
        return {
            "name": self.segment_name,
            "fields": self.fields
        }

class HL7Message:
    def __init__(self):
        self.segments = {}

    def add_segment(self, segment_name, segment):
        self.segments[segment_name] = segment

    def __repr__(self):
        return f"HL7Message: {self.segments}"

    def to_dict(self):
        return {segment_name: segment.to_dict() for segment_name, segment in self.segments.items()}


    def get_message_control_id(self):
        # Extract Message Control ID from MSH-10 if available
        if "MSH" in self.segments and "MSH-10" in self.segments["MSH"].fields:
            return self.segments["MSH"].fields["MSH-10"]["Field Value"]
        return None

def parse_hl7_message(hl7_message):
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

def parse_hl7_file(file_path):
    # To store all parsed HL7 messages with their IDs
    parsed_messages = {}

    with open(file_path, 'r') as hl7_file:
        current_message = []
        for line in hl7_file:
            # Start of a new message
            if line.startswith("MSH"):
                if current_message:
                    # Join and parse the current message if there's any content
                    full_message = "\n".join(current_message)
                    parsed_message = parse_hl7_message(full_message)
                    
                    # Use the Message Control ID or a fallback ID
                    message_id = parsed_message.get_message_control_id() or f"message_{len(parsed_messages)+1}"
                    parsed_messages[message_id] = parsed_message.to_dict()

                # Start a new message
                current_message = [line.strip()]
            else:
                current_message.append(line.strip())
        
        # Handle the last message after the loop
        if current_message:
            full_message = "\n".join(current_message)
            parsed_message = parse_hl7_message(full_message)
            message_id = parsed_message.get_message_control_id() or f"message_{len(parsed_messages)+1}"
            parsed_messages[message_id] = parsed_message.to_dict()

    return parsed_messages

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
parsed_hl7_messages = parse_hl7_file('data/source_hl7_messages_v2.hl7')
print("Parsing completed in", time.time() - start_time, "seconds.", flush=True)

# Write to JSON file with IDs as keys
start_time = time.time()
print("Writing parsed HL7 messages to JSON...", flush=True)
with open('data/parsed_hl7_messages.json', 'w') as json_file:
    json.dump(parsed_hl7_messages, json_file, indent=2)
print("Writing completed in", time.time() - start_time, "seconds.", flush=True)
