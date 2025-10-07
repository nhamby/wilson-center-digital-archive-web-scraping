#!/usr/bin/env python3
"""
Main entry point for Wilson Center Digital Archive Web Scraper

This script provides the command-line interface for running the scraper.
"""

import argparse
import sys

from scraper import WilsonArchiveScraper


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Wilson Center Digital Archive Web Scraper"
    )
    parser.add_argument(
        "--start-page", type=int, default=0, help="Starting page number (default: 0)"
    )
    parser.add_argument(
        "--end-page", type=int, default=1615, help="Ending page number (default: 1615)"
    )
    parser.add_argument(
        "--export", action="store_true", help="Export database to CSV and exit"
    )
    parser.add_argument(
        "--db",
        type=str,
        default="wilson_archive.db",
        help="Database file path (default: wilson_archive.db)",
    )
    parser.add_argument(
        "--stats", action="store_true", help="Show database statistics and exit"
    )

    args = parser.parse_args()

    scraper = WilsonArchiveScraper(db_path=args.db)

    try:
        if args.stats:
            scraper.get_stats()
        elif args.export:
            scraper.export_to_csv()
        else:
            scraper.scrape_range(args.start_page, args.end_page)
            scraper.get_stats()
    except KeyboardInterrupt:
        print("\n\nExiting...")
        sys.exit(0)
    finally:
        scraper.close()


if __name__ == "__main__":
    main()
