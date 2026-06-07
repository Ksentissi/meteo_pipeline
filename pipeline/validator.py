from utils.logger import logger


# Physically plausible bounds for each weather measurement
VALIDATION_RULES = {
    "temperature": (-50, 60),      # °C — covers all Earth surface conditions
    "wind_speed": (0, 400),        # km/h — above 400 is beyond any recorded value
    "humidity": (0, 100),          # % — strict physical bounds
    "precipitation": (0, 500),     # mm/h — above 500 is beyond any recorded value
}


def validate_records(records):
    """
    Validate a list of weather records before writing to InfluxDB.
    Rejects any record containing out-of-bounds or missing values.
    Logs every rejected record with the reason for rejection.

    Args:
        records (list): List of weather measurement dicts as returned
                        by fetch_weather().

    Returns:
        list: A filtered list containing only valid records.
              Never returns None — returns an empty list if all records
              are invalid.
    """
    valid_records = []
    rejected_count = 0

    for record in records:
        if not _is_valid(record):
            rejected_count += 1
            continue
        valid_records.append(record)

    if rejected_count > 0:
        logger.warning(
            f"Validation: {rejected_count} records rejected out of "
            f"{len(records)} for user {records[0]['user_id']}"
        )

    logger.info(
        f"Validation passed: {len(valid_records)}/{len(records)} records valid"
    )
    return valid_records


def _is_valid(record):
    """
    Check a single weather record against all validation rules.
    Returns False and logs the reason if any field fails validation.

    Args:
        record (dict): A single weather measurement dict.

    Returns:
        bool: True if all fields are within expected bounds, False otherwise.
    """
    for field, (min_val, max_val) in VALIDATION_RULES.items():
        value = record.get(field)

        # Reject records with missing fields
        if value is None:
            logger.warning(
                f"Rejected record at {record['timestamp']} for user "
                f"{record['user_id']}: missing field '{field}'"
            )
            return False

        # Reject records with out-of-bounds values
        if not (min_val <= value <= max_val):
            logger.warning(
                f"Rejected record at {record['timestamp']} for user "
                f"{record['user_id']}: {field}={value} out of bounds "
                f"[{min_val}, {max_val}]"
            )
            return False

    return True