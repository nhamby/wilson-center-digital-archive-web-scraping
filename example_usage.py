#!/usr/bin/env python3
"""
Example usage of the Wilson Archive Scraper

This script demonstrates various usage patterns for the scraper.
"""

from scraper import WilsonArchiveScraper

def example_basic_usage():
    """Example: Basic usage - scrape a small range"""
    print("Example 1: Basic scraping of pages 0-2")
    print("-" * 60)
    
    scraper = WilsonArchiveScraper(db_path="example.db")
    try:
        scraper.scrape_range(start_page=0, end_page=2)
        scraper.get_stats()
    finally:
        scraper.close()
    
    print("\n")

def example_check_status():
    """Example: Check what has been scraped"""
    print("Example 2: Checking scraping status")
    print("-" * 60)
    
    scraper = WilsonArchiveScraper(db_path="example.db")
    try:
        scraper.get_stats()
        
        # Check specific pages
        for page_num in range(0, 5):
            is_done = scraper.is_page_completed(page_num)
            status = "✓ Completed" if is_done else "✗ Not completed"
            print(f"  Page {page_num}: {status}")
    finally:
        scraper.close()
    
    print("\n")

def example_export_data():
    """Example: Export data to CSV"""
    print("Example 3: Exporting data to CSV")
    print("-" * 60)
    
    scraper = WilsonArchiveScraper(db_path="example.db")
    try:
        scraper.export_to_csv(output_file="example_export.csv")
    finally:
        scraper.close()
    
    print("\n")

def example_resume_scraping():
    """Example: Resume scraping (skips completed pages)"""
    print("Example 4: Resume scraping")
    print("-" * 60)
    print("If you run this again, it will skip already completed pages")
    
    scraper = WilsonArchiveScraper(db_path="example.db")
    try:
        # This will skip pages 0-2 if they were already completed
        scraper.scrape_range(start_page=0, end_page=5)
        scraper.get_stats()
    finally:
        scraper.close()
    
    print("\n")

def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("Wilson Archive Scraper - Usage Examples")
    print("="*60 + "\n")
    
    print("NOTE: These examples require network access to run.")
    print("The actual scraping will work when the script can reach")
    print("https://digitalarchive.wilsoncenter.org\n")
    
    # Uncomment to run examples:
    # example_basic_usage()
    # example_check_status()
    # example_export_data()
    # example_resume_scraping()
    
    print("Examples are commented out. Uncomment in the code to run them.")

if __name__ == "__main__":
    main()
