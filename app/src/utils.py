def clean_null_entries(message):
    """Recursively clean a JSON object by removing entries with null/empty Field Value, Subfields,
       Field Value with only '^', and finally remove the Field Value after cleaning subfields."""

    copymsg = message.copy()

    # Iterate over the segments and fields
    for segment, fields in copymsg.items():
        # Use list(fields["fields"].items()) to safely iterate while modifying
        for field, details in list(fields["fields"].items()):
            field_value = details["Field Value"]
            
            # Check if the Field Value is None, empty, or consists entirely of '^' characters
            if field_value is None or field_value == "" or set(field_value) == {"^"}:
                # Remove the field if any of the above conditions are true
                del fields["fields"][field]
            elif isinstance(details["Subfields"], dict):
                # Iterate over the subfields in a similar manner
                for subfield, subfield_value in list(details["Subfields"].items()):
                    if subfield_value is None or subfield_value == "" or (isinstance(subfield_value, list) and not subfield_value):
                        # Remove subfields that are None, empty strings, or empty lists
                        del details["Subfields"][subfield]

            # After cleaning, remove 'Field Value' since it's already parsed into subfields
            if 'Field Value' in details:
                del details['Field Value']

    return message
