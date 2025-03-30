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
            "MRN": message["PID"]["fields"].get("PID-18", {}).get("Subfields", {}).get("PID-18.1", None),
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

def update_summary(id, message):
    
    summary = {
        "MCID": id,
        "MRN": message["PID"]["fields"].get("PID-18", {}).get("Subfields", {}).get("PID-18.1", None),
        "PLN": message["PID"]["fields"].get("PID-5", {}).get("Subfields", {}).get("PID-5.1", None),
        "MSG_TYPE": message["MSH"]["fields"].get("MSH-9", {}).get("Subfields", {}).get("MSH-9.1", None),
        "MSG_DATETIME": message["MSH"]["fields"].get("MSH-7", {}).get("Subfields", {}).get("MSH-7.1", None),
    }
    summary['MSG_DATETIME'] = adjust_datetime_str(summary['MSG_DATETIME']) if summary['MSG_DATETIME'] else None

    message['summary'] = summary
    return message


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
    

def get_deidentified_person(message):
    # from app.src.deidentify import deidentify
    from deidentify import deidentify_person

    """
    Extract and deidentify relevant fields from the HL7 message.
    """
    # Extract relevant fields for deidentification
    first_name = message["PID"]["fields"].get("PID-5", {}).get("Subfields", {}).get("PID-5.2", None)
    last_name = message["PID"]["fields"].get("PID-5", {}).get("Subfields", {}).get("PID-5.1", None)
    dob = message["PID"]["fields"].get("PID-7", {}).get("Subfields", {}).get("PID-7.1", None)
    mrn = message["PID"]["fields"].get("PID-18", {}).get("Subfields", {}).get("PID-18.1", None)

    # Deidentify the data
    unique_first_name, unique_last_name, new_dob, age, mrn = deidentify_person(first_name, last_name, dob, mrn)

    return {
        "unique_first_name": unique_first_name,
        "unique_last_name": unique_last_name,
        "new_dob": new_dob,
        "age": age,
        "mrn": mrn
    }

def get_deidentified_address(message):
    from app.src.deidentify import deidentify
    # from deidentify import deidentify_address

    """
    Extract and deidentify relevant fields from the HL7 message.
    """
    # Extract relevant fields for deidentification
    street = message["PID"]["fields"].get("PID-11", {}).get("Subfields", {}).get("PID-11.1", None)
    city = message["PID"]["fields"].get("PID-11", {}).get("Subfields", {}).get("PID-11.3", None)
    state = message["PID"]["fields"].get("PID-11", {}).get("Subfields", {}).get("PID-11.4", None)
    zip_code = message["PID"]["fields"].get("PID-11", {}).get("Subfields", {}).get("PID-11.5", None)
    mrn = message["PID"]["fields"].get("PID-18", {}).get("Subfields", {}).get("PID-18.1", None)

    # Deidentify the data
    unique_street, unique_city, unique_state, unique_zip_code = deidentify_address(street, city, state, zip_code, mrn)

    return {
        "unique_street": unique_street,
        "unique_city": unique_city,
        "unique_state": unique_state,
        "unique_zip_code": unique_zip_code
    }

def replace_deidentified_fields(message):
    # Deidentify person-related fields
    person_deid = get_deidentified_person(message)
    # Update the patient's name and date of birth fields in the PID segment
    if "PID" in message and "fields" in message["PID"]:
        if "PID-5" in message["PID"]["fields"]:
            subfields = message["PID"]["fields"]["PID-5"].get("Subfields", {})
            # Replace first and last names with deidentified values
            subfields["PID-5.1"] = person_deid["unique_last_name"]
            subfields["PID-5.2"] = person_deid["unique_first_name"]
            message["PID"]["fields"]["PID-5"]["Subfields"] = subfields

        if "PID-7" in message["PID"]["fields"]:
            subfields = message["PID"]["fields"]["PID-7"].get("Subfields", {})
            # Replace the date of birth with the deidentified date
            subfields["PID-7.1"] = person_deid["new_dob"]
            message["PID"]["fields"]["PID-7"]["Subfields"] = subfields

    # Deidentify address-related fields
    address_deid = get_deidentified_address(message)
    if "PID" in message and "fields" in message["PID"]:
        if "PID-11" in message["PID"]["fields"]:
            subfields = message["PID"]["fields"]["PID-11"].get("Subfields", {})
            subfields["PID-11.1"] = address_deid["unique_street"]
            subfields["PID-11.3"] = address_deid["unique_city"]
            subfields["PID-11.4"] = address_deid["unique_state"]
            subfields["PID-11.5"] = address_deid["unique_zip_code"]
            message["PID"]["fields"]["PID-11"]["Subfields"] = subfields

    # Optionally, update the summary with deidentified age if needed
    if "summary" in message:
        message["summary"]["age"] = person_deid["age"]

    return message
