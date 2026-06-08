# meteo_pipeline

A fully automated weather data ingestion and processing pipeline. Built ad Poc for the ARVC project.

This project mirrors the architecture of the real study pipeline — dual database (PostgreSQL + InfluxDB), incremental fetching, data validation, crash-safe sync state, logging, and scheduled execution — using the Open-Meteo API as a lightweight data source in place of the Polar AccessLink API.

---

## Architecture

```
Open-Meteo API
      ↓
api/fetch.py          — HTTP request, response parsing
      ↓
pipeline/validator.py — Data validation (bounds checking, null detection)
      ↓
db/influx.py          — Write time-series measurements to InfluxDB
      ↓
db/postgres.py        — Update sync_state (anti-duplication mechanism)
      ↓
pipeline/aggregator.py — Generate daily summaries
```

---

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.13+ |
| Metadata database | PostgreSQL 17 |
| Time-series database | InfluxDB 2 |
| Data source | Open-Meteo API (no auth required) |
| Retry logic | tenacity |
| Scheduling | cron |

---

## Project Structure

```
meteo_pipeline/
├── api/
│   └── fetch.py              # Open-Meteo API client
├── db/
│   ├── postgres.py           # PostgreSQL client (metadata, sync state)
│   └── influx.py             # InfluxDB client (time-series write/query)
├── pipeline/
│   ├── orchestrator.py       # Core pipeline logic per user
│   ├── validator.py          # Data validation layer
│   └── aggregator.py        # Daily summary generation
├── utils/
│   ├── config.py             # Environment variable loader
│   └── logger.py             # Logging configuration
├── logs/                     # Auto-generated log files
├── run_pipeline.py           # Entry point
├── .env                      # Credentials (not committed)
└── README.md
```

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-username/meteo_pipeline.git
cd meteo_pipeline
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file at the root of the project:

```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=meteo_pipeline
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

INFLUX_URL=http://localhost:8086
INFLUX_TOKEN=your_influxdb_token_here
INFLUX_ORG=meteo_org
INFLUX_BUCKET=meteo_data
```

### 4. Set up PostgreSQL

```bash
psql postgres
```

```sql
CREATE DATABASE meteo_pipeline;
\c meteo_pipeline

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    location VARCHAR(100) NOT NULL,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE sync_state (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    last_fetched_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO users (name, location, latitude, longitude)
VALUES ('Kamil', 'ETH Zurich HG', 47.3763, 8.5480);

INSERT INTO sync_state (user_id, last_fetched_at)
VALUES (1, NOW() - INTERVAL '1 day');
```

### 5. Set up InfluxDB

Start InfluxDB and navigate to `http://localhost:8086`. Complete the initial setup with:
- Organization: `meteo_org`
- Bucket: `meteo_data`

Copy the generated token into your `.env` file.

---

## Usage

### Run the ingestion pipeline

```bash
python run_pipeline.py --mode pipeline
```

### Generate a daily summary

```bash
# Today
python run_pipeline.py --mode aggregate

# Specific date
python run_pipeline.py --mode aggregate --date 2026-06-07
```

---

## Scheduling (cron)

To run the pipeline automatically every hour and generate a daily summary at 8am:

```bash
crontab -e
```

```
0 * * * *   /path/to/venv/bin/python /path/to/meteo_pipeline/run_pipeline.py --mode pipeline
0 8 * * *   /path/to/venv/bin/python /path/to/meteo_pipeline/run_pipeline.py --mode aggregate
```

---

## Key Design Decisions

**Why two databases?**
PostgreSQL handles structured metadata that rarely changes (user profiles, sync state). InfluxDB handles continuous timestamped measurements — it is purpose-built for time-range queries at scale, which would be slow in a relational database.

**Crash-safe sync state**
The `sync_state` table in PostgreSQL is only updated *after* a confirmed successful write to InfluxDB. If the pipeline crashes mid-run, the next execution will re-fetch and re-process the same records — guaranteeing zero data loss.

**Incremental fetching**
Each run reads `last_fetched_at` from PostgreSQL and only processes records newer than that timestamp. This is the equivalent of the transaction model in the Polar AccessLink API used in the real ARVC project.

**Retry with exponential backoff**
Every API call is wrapped with the `tenacity` library — 3 attempts with 1s → 2s → 4s wait. One transient failure never causes a full pipeline failure.

---

## Mapping to the ARVC Project

| This project | ARVC wearable pipeline |
|---|---|
| Open-Meteo API | Polar AccessLink API |
| 1 user | 25 ARVC patients |
| Temperature, wind, humidity | Heart rate, steps, exercise sessions |
| sync_state (timestamp-based) | Transaction model + sync_state |
| Sequential loop | asyncio.gather() for 25 patients |
| Local server | ETH Zurich server + systemd |

---

## Author

Kamil Sentissi
