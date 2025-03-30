import hashlib
import datetime
from app.src.constants import FIRST_NAMES, LAST_NAMES, STREET_PREFIXES, STREET_SUFFIXES, CITIES
# from constants import FIRST_NAMES, LAST_NAMES, STREET_PREFIXES, STREET_SUFFIXES, CITIES

def consistent_bday(dob, identifier):
    """
    Create a pseudo-random but consistent birthday based on the hashed identifier.
    """

    if dob is None:
        return None, None

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
        age = 0
        new_dob = datetime.datetime.today().strftime("%Y-%m-%d")  # Set to today if future date
    elif age > 89:
        age = '90+'  # Cap age for privacy

    return new_dob, age


def deidentify_person(first_name, last_name, dob, mrn):
    # Create a unique identifier based on first name, last name, dob, and mrn
    identifier = f"{first_name}{last_name}{dob}{mrn}"
    
    # Hash the identifier for consistent indexing
    sha256_hash = hashlib.sha256(identifier.encode()).hexdigest()
    
    # Use the hash to select consistent indices for first and last names
    first_name_index = int(sha256_hash[:8], 16) % len(FIRST_NAMES)
    last_name_index = int(sha256_hash[8:14], 16) % len(LAST_NAMES)
    mrn = int(sha256_hash[14:16], 16) % 1000000  # Assuming MRN is a 6-digit number

    
    # Retrieve the unique first and last name
    unique_first_name = FIRST_NAMES[first_name_index]
    unique_last_name = LAST_NAMES[last_name_index]

    
    # Generate a consistent random birthday based on the identifier
    new_dob, age = consistent_bday(dob, identifier)

    return unique_first_name, unique_last_name.lower(), new_dob, age, mrn


def consistent_address(street, city, state, zip_code, identifier):
    """
    De-identify the street, city, and zip code while keeping the state intact. 
    The de-identified values will be consistent based on the hashed identifier.
    """
    # Hash the identifier to get a deterministic "random" value
    hash_value = hashlib.sha256(identifier.encode()).hexdigest()
    
    # Use parts of the hash to create pseudo-random but consistent address components
    street_index = int(hash_value[:2], 16) % 1000  # Street number (0-999)
    street_prefix_index = int(hash_value[2:4], 16) % len(STREET_PREFIXES)  # Prefix from predefined list
    street_suffix_index = int(hash_value[4:6], 16) % len(STREET_SUFFIXES)  # Suffix from predefined list
    city_index = int(hash_value[6:10], 16) % len(CITIES)  # City from predefined list
    zip_index = int(hash_value[10:14], 16) % 90000 + 10000  # Zip code between 10000 and 99999


    # Generate the new street and city names
    new_street_suffix = STREET_SUFFIXES[street_suffix_index]
    new_street_prefix = STREET_PREFIXES[street_prefix_index]
    new_city = CITIES[city_index]



    # Form the de-identified address
    new_street = f"{street_index} {new_street_prefix} {new_street_suffix}"
    new_zip_code = str(zip_index)  # Ensuring it's a string
    
    return new_street, new_city, state, new_zip_code


def deidentify_address(street, city, state, zip_code, mrn):
    """
    De-identify the address based on personal information while keeping the state unchanged.
    """
    # Create a unique identifier based on first name, last name, dob, mrn, and the original address
    identifier = f"{mrn}"
    
    # De-identify the street, city, and zip code (keep state intact)
    new_street, new_city, new_state, new_zip_code = consistent_address(street, city, state, zip_code, identifier)
    
    return new_street, new_city, new_state, new_zip_code
