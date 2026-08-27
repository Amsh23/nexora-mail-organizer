import argparse
import logging

from sync_service import run_sync


def configure_logging():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")


def main(dry_run=False):
    configure_logging()
    print("\n======================================")
    print("       NEXORA MAIL ORGANIZER")
    print("======================================")
    run_sync(dry_run=dry_run)
    print("\nFinished.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without saving anything")
    args = parser.parse_args()
    main(dry_run=args.dry_run)
