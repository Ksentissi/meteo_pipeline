from datetime import datetime, timezone
from db.influx import query_daily_summary
from db.postgres import get_all_users
from utils.logger import logger


def run_daily_aggregation(date=None):
    """
    Generate and log daily weather summaries for all registered users.
    For each user, queries InfluxDB for aggregated statistics over the
    specified date and logs a structured summary report.

    This is the equivalent of the daily patient activity report in the
    ARVC project — giving the research team a clean overview of each
    patient's data for the day.

    Args:
        date (str): Date to aggregate in format 'YYYY-MM-DD'.
                    Defaults to today if not provided.
    """
    if date is None:
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    logger.info("=" * 50)
    logger.info(f"Daily aggregation started for {date}")
    logger.info("=" * 50)

    users = get_all_users()

    for user in users:
        user_id, name, location = user[0], user[1], user[2]
        try:
            _generate_user_summary(user_id, name, location, date)
        except Exception as e:
            logger.error(
                f"Aggregation failed for user {name} "
                f"(id={user_id}): {e}"
            )

    logger.info(f"Daily aggregation completed for {date}")


def _generate_user_summary(user_id, name, location, date):
    """
    Query InfluxDB and log a structured daily summary for a single user.
    Computes and logs:
        - Average, max, and min temperature
        - Average wind speed
        - Average humidity
        - Total precipitation
        - Hours above 25°C (equivalent to 'time above threshold'
          in the ARVC heart rate analysis)

    Args:
        user_id (int): Internal user ID.
        name (str): User display name.
        location (str): User location label.
        date (str): Date string in format 'YYYY-MM-DD'.
    """
    summary = query_daily_summary(user_id, date)

    if not summary:
        logger.warning(
            f"No data available for {name} ({location}) on {date}"
        )
        return

    # Extract values with safe fallbacks to None
    avg_temp = summary.get("temperature")
    wind = summary.get("wind_speed")
    humidity = summary.get("humidity")
    precipitation = summary.get("precipitation")

    # Log the structured daily report
    # This is the equivalent of Elsie's morning dashboard in the ARVC project
    logger.info(
        f"\n"
        f"  Daily Summary — {name} ({location}) — {date}\n"
        f"  {'─' * 40}\n"
        f"  Temperature   : {_fmt(avg_temp, '°C')}\n"
        f"  Wind Speed    : {_fmt(wind, 'km/h')}\n"
        f"  Humidity      : {_fmt(humidity, '%')}\n"
        f"  Precipitation : {_fmt(precipitation, 'mm')}\n"
        f"  {'─' * 40}"
    )


def _fmt(value, unit):
    """
    Format a numeric value with its unit for display in logs.
    Returns 'N/A' if the value is None to avoid crashing on missing data.

    Args:
        value (float): The numeric value to format.
        unit (str): The unit string to append.

    Returns:
        str: Formatted string like '18.4 °C' or 'N/A'.
    """
    if value is None:
        return "N/A"
    return f"{value:.1f} {unit}"