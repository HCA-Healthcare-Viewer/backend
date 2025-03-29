from app.src.classes import HL7Message, HL7Segment
from app.src.constants import segments
import json
# from constants import segments
# from classes import HL7Message, HL7Segment


def clean_null_entries(message):
    """Recursively clean a JSON object by removing entries with null/empty Field Value or Subfields."""
    
    def clean_subfields(subfields):
        """Clean Subfields dictionary by removing empty or null values."""
        if isinstance(subfields, dict):
            return {k: v for k, v in subfields.items() if v}
        return subfields
    
    if isinstance(message, dict):
        cleaned_data = {}
        for key, value in message.items():
            if isinstance(value, dict):
                # Recursively clean nested dictionaries
                value['Subfields'] = clean_subfields(value.get('Subfields'))
                
                # Only keep entries where Field Value or Subfields are not null or empty
                if value.get('Field Value') or value.get('Subfields'):
                    cleaned_data[key] = clean_null_entries(value)
            else:
                # Keep non-dict entries as-is
                cleaned_data[key] = value
        return cleaned_data
    return message
