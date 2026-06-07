import argparse
from pipeline.orchestrator import run_pipeline
from pipeline.aggregator import run_daily_aggregation
from utils.logger import logger


def main():
    """
    Main entry point for the meteo pipeline.
    Supports two modes via command-line arguments:
        - pipeline : fetch and store weather data for all users
        - aggregate : generate daily summaries from stored data

    Usage:
        python run_pipeline.py --mode pipeline
        python run_pipeline.py --mode aggregate
        python run_pipeline.py --mode aggregate --date 2026-06-04
    """
    parser = argparse.ArgumentParser(
        description="Meteo Pipeline — fetch, store and summarize weather data"
    )
    parser.add_argument(
        "--mode",
        choices=["pipeline", "aggregate"],
        default="pipeline",
        help="pipeline: fetch and store data | aggregate: generate daily summary"
    )
    parser.add_argument(
        "--date",
        default=None,
        help="Date for aggregation in format YYYY-MM-DD (default: today)"
    )

    args = parser.parse_args()

    if args.mode == "pipeline":
        logger.info("Mode: pipeline — fetching and storing weather data")
        run_pipeline()

    elif args.mode == "aggregate":
        logger.info(f"Mode: aggregate — generating daily summary "
                    f"for {args.date or 'today'}")
        run_daily_aggregation(date=args.date)


if __name__ == "__main__":
    main()