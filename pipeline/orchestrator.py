from datetime import datetime, timezone
from tenacity import retry, stop_after_attempt, wait_exponential

from api.fetch import fetch_weather
from db.postgres import get_all_users, get_last_fetched_at, update_sync_state
from db.influx import write_weather_records
from pipeline.validator import validate_records
from utils.logger import logger


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8)
)
def _fetch_and_store(user):
    """
    Core pipeline logic for a single user:
        1. Fetch weather data from Open-Meteo API
        2. Filter records newer than last_fetched_at (anti-duplication)
        3. Validate records against physical bounds
        4. Write valid records to InfluxDB
        5. Update sync_state in PostgreSQL — only if write succeeded

    The @retry decorator automatically retries up to 3 times with
    exponential backoff (1s → 2s → 4s) if any step raises an exception.
    sync_state is only updated after a confirmed successful write to InfluxDB,
    guaranteeing crash-safe idempotency.

    Args:
        user (tuple): (id, name, location, latitude, longitude)
    """
    user_id, name, location, latitude, longitude = user

    # Step 1 — Fetch raw records from the API
    records = fetch_weather(user)

    # Step 2 — Filter out already-fetched records using sync_state
    # This is the incremental fetch mechanism — equivalent to the
    # transaction model in the Polar AccessLink API
    last_fetched_at = get_last_fetched_at(user_id)
    if last_fetched_at:
        # Make last_fetched_at timezone-aware for comparison
        if last_fetched_at.tzinfo is None:
            last_fetched_at = last_fetched_at.replace(tzinfo=timezone.utc)
        records = [
            r for r in records
            if r["timestamp"] > last_fetched_at
        ]
        logger.info(
            f"Incremental fetch: {len(records)} new records "
            f"after {last_fetched_at} for {name}"
        )

    if not records:
        logger.info(f"No new records to process for {name}")
        return

    # Step 3 — Validate records before writing to InfluxDB
    valid_records = validate_records(records)

    if not valid_records:
        logger.warning(f"No valid records to write for {name}")
        return

    # Step 4 — Write to InfluxDB
    # If this fails, an exception is raised and sync_state is NOT updated
    # The @retry decorator will attempt this up to 3 times
    write_weather_records(valid_records)

    # Step 5 — Only update sync_state after confirmed successful write
    # This guarantees that if the write fails, the next run will retry
    # the same records — zero data loss
    latest_timestamp = max(r["timestamp"] for r in valid_records)
    update_sync_state(user_id, latest_timestamp)

    logger.info(f"Pipeline completed successfully for {name}")


def run_pipeline():
    """
    Main pipeline entry point. Fetches and stores weather data
    for all registered users sequentially.
    Errors for one user are caught and logged without stopping
    the pipeline for other users.
    """
    logger.info("=" * 50)
    logger.info("Pipeline run started")
    logger.info("=" * 50)

    users = get_all_users()
    logger.info(f"Processing {len(users)} user(s)")

    success_count = 0
    error_count = 0

    for user in users:
        user_id, name = user[0], user[1]
        try:
            _fetch_and_store(user)
            success_count += 1
        except Exception as e:
            # Log the error but continue processing other users
            # In the real ARVC project this would be asyncio.gather()
            # with return_exceptions=True
            logger.error(
                f"Pipeline failed for user {name} (id={user_id}): {e}"
            )
            error_count += 1

    logger.info(
        f"Pipeline run completed — "
        f"{success_count} succeeded, {error_count} failed"
    )