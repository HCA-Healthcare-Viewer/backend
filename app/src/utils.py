from datetime import datetime

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

    return copymsg


def create_message_summaries(messages):
    for message_id, message in messages.items():
        summary = {
            "MCID": message_id,
            "MRN": message["PID"]["fields"].get("PID-3", {}).get("Subfields", {}).get("PID-3.1", None),
            "PLN": message["PID"]["fields"].get("PID-5", {}).get("Subfields", {}).get("PID-5.1", None),
            "MSG_TYPE": message["MSH"]["fields"].get("MSH-9", {}).get("Subfields", {}).get("MSH-9.1", None),
            "MSG_DATETIME": message["MSH"]["fields"].get("MSH-7", {}).get("Subfields", {}).get("MSH-7.1", None),
        }
        summary['MSG_DATETIME'] = adjust_datetime_str(summary['MSG_DATETIME']) if summary['MSG_DATETIME'] else None

        messages[message_id]['summary'] = summary

        #reorder the segments to have 'summary' at the front
        segments = list(messages[message_id].keys())
        segments.remove('summary')
        segments.insert(0, 'summary')
        messages[message_id] = {segment: messages[message_id][segment] for segment in segments}

    return messages


def adjust_datetime(messages):
    for message_id, message in messages.items():
        for segment_name, segment in message.items():
            # Skip the 'summary' segment if present
            if 'summary' in segment_name.lower():
                continue

            for field_name, field_details in segment["fields"].items():
                # Check the Field Description for date/time reference
                field_description = field_details.get("Field Description", "").lower()
                if 'date/time' in field_description or 'datetime' in field_description:
                    field_subfields = field_details.get("Subfields", {})

                    # Attempt to get the first subfield value (e.g., OBR-6.1)
                    try:
                        # Look for a subfield ending in ".1" if available
                        value = field_subfields.get(f"{field_name}.1") or next(
                            (v for k, v in field_subfields.items() if ".1" in k), None)

                        # Skip parsing if the value is redacted (i.e., all asterisks)
                        if value and value == "*" * len(value):
                            # print(f"Skipping redacted datetime field: {field_name} in message {message_id}", flush=True)
                            continue

                        if value:
                            if len(value) == 8:
                                # Format: YYYYMMDD
                                formatted_date = datetime.strptime(value, "%Y%m%d").strftime("%Y-%m-%d")
                            elif len(value) == 12:
                                # Format: YYYYMMDDHHMM
                                formatted_date = datetime.strptime(value, "%Y%m%d%H%M").strftime("%Y-%m-%d %H:%M")
                            elif len(value) == 17:
                                # Format: YYYYMMDDHHMM-ZZZZ
                                formatted_date = datetime.strptime(value, "%Y%m%d%H%M%z").strftime("%Y-%m-%d %H:%M")
                            else:
                                formatted_date = value

                            field_subfields[f"{field_name}.1"] = formatted_date
                            field_details["Subfields"] = field_subfields

                    except (ValueError, StopIteration) as e:
                        print(f"Error parsing date/time for {field_description}: {field_subfields}", flush=True)
                        continue
    return messages


def adjust_datetime_str(datetime_str):
    if set(datetime_str) == {"*"}:
        return datetime_str  # Return as is if redacted

    try:
        if len(datetime_str) == 8:
            # Format: YYYYMMDD
            return datetime.strptime(datetime_str, "%Y%m%d").strftime("%Y-%m-%d")
        elif len(datetime_str) == 12:
            # Format: YYYYMMDDHHMM
            return datetime.strptime(datetime_str, "%Y%m%d%H%M").strftime("%Y-%m-%d %H:%M")
        elif len(datetime_str) == 17:
            # Format: YYYYMMDDHHMM-ZZZZ
            return datetime.strptime(datetime_str, "%Y%m%d%H%M%z").strftime("%Y-%m-%d %H:%M")
        else:
            return datetime_str  # Return as is if format is not recognized
    except ValueError as e:
        print(f"Error parsing date/time: {e}", flush=True)
        return datetime_str  # Return as is in case of error
    
