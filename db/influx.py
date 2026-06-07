from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from utils.config import INFLUX_CONFIG
from utils.logger import logger


def get_client():
    """
    Initialize and return an InfluxDB client instance.
    Uses credentials loaded from environment variables via INFLUX_CONFIG.
    """
    return InfluxDBClient(
        url=INFLUX_CONFIG["url"],
        token=INFLUX_CONFIG["token"],
        org=INFLUX_CONFIG["org"]
    )


def write_weather_records(records):
    """
    Write a list of weather measurements to InfluxDB.
    Each record is written as a data point with the following fields:
        - temperature (°C)
        - wind_speed (km/h)
        - humidity (%)
        - precipitation (mm)

    Args:
        records (list): List of dicts, each containing a timestamp and
                        weather measurements for a specific user.

    Only commits after all records are written successfully.
    Raises an exception if the write fails, allowing the orchestrator
    to skip the sync_state update and retry on the next run.
    """
    client = get_client()
    write_api = client.write_api(write_options=SYNCHRONOUS)

    points = []
    for record in records:
        # Build a data point for each measurement
        # Tags are indexed metadata (user, location)
        # Fields are the actual measured values
        point = (
            Point("weather_measurement")
            .tag("user_id", str(record["user_id"]))
            .tag("location", record["location"])
            .field("temperature", record["temperature"])
            .field("wind_speed", record["wind_speed"])
            .field("humidity", record["humidity"])
            .field("precipitation", record["precipitation"])
            .time(record["timestamp"], write_precision="s")
        )
        points.append(point)

    write_api.write(
        bucket=INFLUX_CONFIG["bucket"],
        org=INFLUX_CONFIG["org"],
        record=points
    )

    client.close()
    logger.info(f"Written {len(points)} records to InfluxDB")


def query_daily_summary(user_id, date):
    """
    Query InfluxDB for aggregated weather statistics for a given user and date.
    Returns a dict containing:
        - avg_temperature, max_temperature, min_temperature
        - avg_wind_speed
        - avg_humidity
        - total_precipitation

    Args:
        user_id (int): The internal user ID to query for.
        date (str): The date to query in format 'YYYY-MM-DD'.
    """
    client = get_client()
    query_api = client.query_api()

    # Flux query language is used to query InfluxDB
    # We filter by bucket, time range, measurement, and user tag
    query = f'''
    from(bucket: "{INFLUX_CONFIG["bucket"]}")
        |> range(start: {date}T00:00:00Z, stop: {date}T23:59:59Z)
        |> filter(fn: (r) => r._measurement == "weather_measurement")
        |> filter(fn: (r) => r.user_id == "{user_id}")
        |> mean()
    '''

    tables = query_api.query(query, org=INFLUX_CONFIG["org"])
    client.close()

    summary = {}
    for table in tables:
        for record in table.records:
            summary[record.get_field()] = record.get_value()

    return summary