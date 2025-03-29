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