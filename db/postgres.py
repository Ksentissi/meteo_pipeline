import psycopg2
from utils.config import POSTGRES_CONFIG
from utils.logger import logger


def get_connection():
    """
    Establish and return a new connection to the PostgreSQL database.
    Uses credentials loaded from environment variables via POSTGRES_CONFIG.
    """
    return psycopg2.connect(**POSTGRES_CONFIG)


def get_last_fetched_at(user_id):
    """
    Retrieve the last successful fetch timestamp for a given user.
    Used at the start of each pipeline run to determine the fetch window
    and avoid duplicate ingestion.

    Returns the timestamp if found, None if no sync state exists yet.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT last_fetched_at FROM sync_state WHERE user_id = %s",
        (user_id,)
    )
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0] if result else None


def update_sync_state(user_id, last_fetched_at):
    """
    Update the sync_state table after a successful pipeline run.
    Records the latest fetch timestamp so the next run knows where to start.
    Must only be called after data has been successfully written to InfluxDB.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE sync_state 
        SET last_fetched_at = %s, updated_at = NOW()
        WHERE user_id = %s
        """,
        (last_fetched_at, user_id)
    )
    # Commit is required to persist the changes to the database
    conn.commit()
    cursor.close()
    conn.close()
    logger.info(f"sync_state updated for user {user_id}: {last_fetched_at}")


def get_all_users():
    """
    Fetch all registered users from the database.
    Returns a list of tuples: (id, name, location, latitude, longitude).
    Called by the orchestrator at startup to determine which users to process.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, location, latitude, longitude FROM users")
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return users