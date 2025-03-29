import json

class HL7Segment:
    def __init__(self, segment_name):
        self.segment_name = segment_name
        self.fields = {}

    def add_field(self, field_name, description, value=None):
        # Initialize the subfields and repeating fields
        subfields = {}
        repeating_data = []

        # Check if value exists
        if value:
            # Split by ^ to get subfields
            subfields_values = value.split('^')
            for i, subfield in enumerate(subfields_values, 1):
                subfield_key = f"{field_name}.{i}"  # Create a unique identifier for subfields (e.g., 5.1, 5.2)
                subfields[subfield_key] = subfield

            # If there is repeating data (separated by ~), split the field into a list
            repeating_data = [item for item in value.split('~')]

        else:
            subfields = None

        # Store the main field value, subfields, and repeating data
        self.fields[field_name] = {
            "Field Description": description,
            "Field Value": value if value else None,
            "Subfields": subfields if subfields else None,
            "Repeating Data": repeating_data if repeating_data else None
        }

    def __repr__(self):
        return f"Segment: {self.segment_name}, Fields: {self.fields}"

    def to_dict(self):
        # Convert HL7Segment to a dictionary to make it serializable
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

# Define the segments and fields with descriptions
segments = {
    "MSH": {
        "MSH-1": "Field Separator",
        "MSH-2": "Encoding Characters",
        "MSH-3": "Sending Application",
        "MSH-4": "Sending Facility",
        "MSH-5": "Receiving Application",
        "MSH-6": "Receiving Facility",
        "MSH-7": "Date/Time of Message",
        "MSH-8": "Security",
        "MSH-9": "Message Type",
        "MSH-10": "Message Control ID",
        "MSH-11": "Processing ID",
        "MSH-12": "Version ID",
    },
    "EVN": {
        "EVN-1": "Event Type Code",
        "EVN-2": "Recorded Date/Time",
        "EVN-3": "Date/Time Planned Event",
        "EVN-4": "Event Reason Code",
        "EVN-5": "Operator ID",
        "EVN-6": "Event Occurred",
    },
    "PID": {
        "PID-1": "Set ID - PID",
        "PID-2": "Patient ID",
        "PID-3": "Patient Identifier List",
        "PID-4": "Alternate Patient ID - PID",
        "PID-5": "Patient Name",
        "PID-6": "Mother's Maiden Name",
        "PID-7": "Date/Time of Birth",
        "PID-8": "Administrative Sex",
        "PID-9": "Patient Alias",
        "PID-10": "Race",
        "PID-11": "Patient Address",
        "PID-12": "County Code",
        "PID-13": "Phone Number - Home",
        "PID-14": "Phone Number - Business",
        "PID-15": "Primary Language",
        "PID-16": "Marital Status",
        "PID-17": "Religion",
        "PID-18": "Patient Account Number",
    },
    # You can define other segments like PV1, OBX, etc. similarly...
}

# Parse a message and map it to the predefined structure
def parse_hl7_message(hl7_message):
    # Create a new HL7Message object
    message_obj = HL7Message()

    # Split the message by lines (using '\n' as delimiter)
    lines = hl7_message.split("\n")

    # Initialize current segment name
    current_segment_name = None
    current_segment = None

    for line in lines:
        # Skip empty lines
        if not line.strip():
            continue

        # Split the line by '\r' to separate segments in each line
        segments_data = line.split("\r")

        for segment_line in segments_data:
            # Get the segment type (first three characters)
            segment_type = segment_line[:3]

            # Check if this line is a new segment
            if segment_type in segments:
                # Create a new HL7Segment for this segment
                current_segment_name = segment_type
                current_segment = HL7Segment(segment_type)

                # Add fields to this segment based on the predefined structure
                fields = segment_line.split("|")
                for i, field in enumerate(fields):
                    field_name = f"{current_segment_name}-{i+1}"
                    if field_name in segments[current_segment_name]:
                        field_description = segments[current_segment_name][field_name]
                        current_segment.add_field(field_name, field_description, field)

                # Add the segment to the message
                message_obj.add_segment(current_segment_name, current_segment)

    return message_obj

# Sample HL7 message (using '\n' to separate lines and '\r' for segment separation)
hl7_message = """MSH|^~\&||HOSP_WS|||202502261022||ORU^R01^NURAS|508065.6796364|D|2.1\rEVN|A01|202502260903|||EFD.AJ^JORGENSEN^AMANDA^^^^|202502260903\rPID|1||W000033049|W23038|mairi^ghita^26^^^^L||19900505|F|^^^^^||^^^^^^^^|||||||W00000331191"""

# Parse the message
message_obj = parse_hl7_message(hl7_message)

def custom_dumps(obj, indent=4):
    # Helper function to handle nested dictionaries and HL7Segment objects
    def recursive_dict(obj):
        if isinstance(obj, dict):
            return {key: recursive_dict(value) if isinstance(value, (dict, HL7Segment)) else value
                    for key, value in obj.items()}
        elif isinstance(obj, HL7Segment):
            return obj.to_dict()  # Convert HL7Segment to dict for serialization
        return obj

    # Recursively process the dictionary and serialize
    return json.dumps(recursive_dict(obj), indent=indent)

# Example usage
print(custom_dumps(message_obj.__dict__, indent=4))
