import hashlib
import datetime
from constants import FIRST_NAMES, LAST_NAMES

def consistent_bday(dob, identifier):
    """
    Create a pseudo-random but consistent birthday based on the hashed identifier.
    """
    # Parse the year from the original dob
    year = datetime.datetime.strptime(dob, "%Y-%m-%d").year

    # Hash the identifier to get a deterministic "random" value
    hash_value = hashlib.sha256(identifier.encode()).hexdigest()
    
    # Use part of the hash to determine the month and day (within valid ranges)
    month = (int(hash_value[:2], 16) % 12) + 1  # Month between 1 and 12
    day = (int(hash_value[2:4], 16) % 28) + 1   # Day between 1 and 28 (safe for all months)

    new_dob = datetime.datetime(year, month, day).strftime("%Y-%m-%d")

    # Calculate age based on today's date
    today = datetime.datetime.today()
    dob_month = int(new_dob.split('-')[1])
    dob_day = int(new_dob.split('-')[2])
    dob_year = int(new_dob.split('-')[0])

    age = today.year - dob_year
    if today.month < dob_month or (today.month == dob_month and today.day < dob_day):
        age -= 1

    if age < 0:
        raise ValueError("Invalid date of birth: year cannot be in the future")
    elif age > 89:
        age = '90+'  # Cap age for privacy

    return new_dob, age


def deidentify(first_name, last_name, dob, mrn):
    # Create a unique identifier based on first name, last name, dob, and mrn
    identifier = f"{first_name}{last_name}{dob}{mrn}"
    
    # Hash the identifier for consistent indexing
    sha256_hash = hashlib.sha256(identifier.encode()).hexdigest()
    
    # Use the hash to select consistent indices for first and last names
    first_name_index = int(sha256_hash[:8], 16) % len(FIRST_NAMES)
    last_name_index = int(sha256_hash[8:16], 16) % len(LAST_NAMES)
    
    # Retrieve the unique first and last name
    unique_first_name = FIRST_NAMES[first_name_index]
    unique_last_name = LAST_NAMES[last_name_index]
    
    # Generate a consistent random birthday based on the identifier
    new_dob, age = consistent_bday(dob, identifier)

    return unique_first_name, unique_last_name.lower(), new_dob, age, mrn


# Example usage
# first_name, last_name, dob, age, mrn = deidentify("John", "Doe", "1990-01-01", "123456789")
