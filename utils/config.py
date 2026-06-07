from dotenv import load_dotenv
import os

load_dotenv()

POSTGRES_CONFIG = {
    "host": os.getenv("POSTGRES_HOST"),
    "port": os.getenv("POSTGRES_PORT"),
    "dbname": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
}

INFLUX_CONFIG = {
    "url": os.getenv("INFLUX_URL"),
    "token": os.getenv("INFLUX_TOKEN"),
    "org": os.getenv("INFLUX_ORG"),
    "bucket": os.getenv("INFLUX_BUCKET"),
}