import requests
from datetime import datetime, timezone
from utils.logger import logger


# Open-Meteo API base URL — no authentication required
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def fetch_weather(user):
    """
    Fetch hourly weather data from the Open-Meteo API for a given user.
    Retrieves temperature, wind speed, humidity, and precipitation
    for the last 24 hours based on the user's GPS coordinates.

    Args:
        user (tuple): A tuple of (id, name, location, latitude, longitude)
                      as returned by get_all_users().

    Returns:
        list: A list of dicts, each representing one hourly measurement:
              {
                  "user_id": int,
                  "location": str,
                  "timestamp": datetime,
                  "temperature": float,
                  "wind_speed": float,
                  "humidity": float,
                  "precipitation": float
              }

    Raises:
        requests.HTTPError: If the API call fails.
    """
    user_id, name, location, latitude, longitude = user

    # Request hourly data for the last 24 hours
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "temperature_2m,wind_speed_10m,relative_humidity_2m,precipitation",
        "past_days": 1,
        "forecast_days": 0,
        "timezone": "Europe/Zurich"
    }

    logger.info(f"Fetching weather data for {name} ({location}) "
                f"at lat={latitude}, lon={longitude}")

    response = requests.get(OPEN_METEO_URL, params=params)
    response.raise_for_status()
    data = response.json()

    records = []
    hourly = data["hourly"]
    timestamps = hourly["time"]
    temperatures = hourly["temperature_2m"]
    wind_speeds = hourly["wind_speed_10m"]
    humidities = hourly["relative_humidity_2m"]
    precipitations = hourly["precipitation"]

    for i, ts in enumerate(timestamps):
        # Parse the timestamp string into a timezone-aware datetime object
        timestamp = datetime.fromisoformat(ts).replace(tzinfo=timezone.utc)

        records.append({
            "user_id": user_id,
            "location": location,
            "timestamp": timestamp,
            "temperature": temperatures[i],
            "wind_speed": wind_speeds[i],
            "humidity": humidities[i],
            "precipitation": precipitations[i]
        })

    logger.info(f"Fetched {len(records)} records for {name}")
    return records