#!/usr/bin/env python3
"""
Wilson Center Digital Archive Web Scraper

This script scrapes documents from the Wilson Center Digital Archive using SeleniumBase
to avoid bot detection. It stores data in a SQLite database and supports resuming.
"""

import argparse
import csv
import json
import sqlite3
import sys
import time
from datetime import datetime
from typing import List, Dict, Optional, Any

from seleniumbase import Driver


class WilsonArchiveScraper:
    """Scraper for Wilson Center Digital Archive"""

    BASE_URL = "https://digitalarchive.wilsoncenter.org"
    SEARCH_URL = f"{BASE_URL}/search?page={{}}"

    def __init__(self, db_path: str = "wilson_archive.db"):
        """Initialize the scraper with database connection"""
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self.driver: Any = None  # SeleniumBase Driver type
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database with required schema"""
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()

        # Create documents table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                document_url TEXT PRIMARY KEY,
                page_number INTEGER,
                original_publication_date TEXT,
                title TEXT,
                credits TEXT,
                text_body TEXT,
                summary TEXT,
                authors TEXT,
                associated_places TEXT,
                subjects_discussed TEXT,
                associated_people_orgs TEXT,
                source TEXT,
                original_upload_date TEXT,
                original_archive_title TEXT,
                language TEXT,
                rights TEXT,
                record_id TEXT,
                original_classification TEXT,
                donors TEXT,
                scraped_at TEXT
            )
        """
        )

        # Add page_number column if it doesn't exist (for existing databases)
        try:
            cursor.execute("ALTER TABLE documents ADD COLUMN page_number INTEGER")
            self.conn.commit()
        except sqlite3.OperationalError:
            # Column already exists
            pass

        # Create completed pages tracking table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS completed_pages (
                page_number INTEGER PRIMARY KEY,
                completed_at TEXT
            )
        """
        )

        self.conn.commit()

    def _init_driver(self):
        """Initialize SeleniumBase driver with settings to avoid bot detection"""
        if self.driver is None:
            # SeleniumBase Driver with UC mode (undetected-chromedriver)
            # uc=True uses undetected-chromedriver to bypass bot detection like triggerInterstitialChallenge()
            # headless=True runs without visible browser window
            self.driver = Driver(uc=True, headless=True)
            print("SeleniumBase driver initialized with undetected mode")

    def _close_driver(self):
        """Close the SeleniumBase driver"""
        if self.driver:
            self.driver.quit()
            self.driver = None

    def is_page_completed(self, page_number: int) -> bool:
        """Check if a page has already been scraped"""
        assert self.conn is not None
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT 1 FROM completed_pages WHERE page_number = ?", (page_number,)
        )
        return cursor.fetchone() is not None

    def mark_page_completed(self, page_number: int):
        """Mark a page as completed"""
        assert self.conn is not None
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO completed_pages (page_number, completed_at) VALUES (?, ?)",
            (page_number, datetime.now().isoformat()),
        )
        self.conn.commit()
        print(f"Page {page_number} marked as completed")

    def get_document_links(self, page_number: int) -> List[str]:
        """Extract document links from a search results page"""
        url = self.SEARCH_URL.format(page_number)
        print(f"Accessing page {page_number}: {url}")

        self.driver.get(url)
        time.sleep(5)  # Wait longer for page to load

        # Find all document links
        links = []
        try:
            # Try multiple selectors to find document links
            selectors = [
                "td.document.contextual-region a",
                "td.document a",
                ".views-row a[href*='/document/']",
                "a[href*='/document/']",
            ]

            for selector in selectors:
                try:
                    elements = self.driver.find_elements("css selector", selector)
                    if elements:
                        print(
                            f"Found {len(elements)} elements with selector: {selector}"
                        )
                        break
                except:
                    continue

            if not elements:
                # Debug: save page source to check what we got
                print("No elements found with any selector. Checking page structure...")
                page_source = self.driver.page_source[:1000]  # First 1000 chars
                print(f"Page source preview: {page_source}")

            for element in elements:
                href = element.get_attribute("href")
                if href and "/document/" in href:
                    # Handle relative URLs
                    if href.startswith("/"):
                        full_url = self.BASE_URL + href
                    else:
                        full_url = href

                    # Avoid duplicates
                    if full_url not in links:
                        links.append(full_url)

            print(f"Found {len(links)} document links on page {page_number}")
        except Exception as e:
            print(f"Error extracting links from page {page_number}: {e}")
            import traceback

            traceback.print_exc()

        return links

    def _get_text_safe(self, selector: str, multiple: bool = False) -> Optional[str]:
        """Safely extract text from element(s) by CSS selector"""
        try:
            if multiple:
                elements = self.driver.find_elements("css selector", selector)
                texts = [el.text.strip() for el in elements if el.text.strip()]
                return json.dumps(texts) if texts else None
            else:
                element = self.driver.find_element("css selector", selector)
                return element.text.strip() if element.text.strip() else None
        except:
            return None

    def _get_information_block(self, title: str) -> Optional[str]:
        """Extract text from information block by title"""
        try:
            # Find all information blocks
            blocks = self.driver.find_elements("css selector", ".information-block")
            for block in blocks:
                try:
                    subtitle = block.find_element("css selector", ".sub-title")
                    if subtitle and title.lower() in subtitle.text.lower():
                        # Try to get text from .text div
                        text_div = block.find_element("css selector", ".text")
                        return text_div.text.strip() if text_div.text.strip() else None
                except:
                    continue
            return None
        except:
            return None

    def _get_pill_list(self, title: str) -> Optional[str]:
        """Extract pill list items (authors, places, etc.) by section title"""
        try:
            # Find all pill blocks AND information blocks (some pills are in information blocks)
            blocks = self.driver.find_elements(
                "css selector", ".pill-block, .information-block"
            )
            for block in blocks:
                try:
                    # Look for the title (h3.title for pill-blocks, h3.sub-title for information-blocks)
                    title_els = block.find_elements(
                        "css selector", "h3.title, h4.title, h3.sub-title"
                    )
                    for title_el in title_els:
                        if title.lower() in title_el.text.lower():
                            # Found the right section, now get pill names
                            # Try nested span first (for places, people)
                            pills = block.find_elements(
                                "css selector", ".pill .name span"
                            )
                            if not pills:
                                # Fall back to direct .name (for subjects, language)
                                pills = block.find_elements(
                                    "css selector", ".pill .name"
                                )
                            if pills:
                                names = [
                                    p.text.strip() for p in pills if p.text.strip()
                                ]
                                return json.dumps(names) if names else None
                except:
                    continue
            return None
        except:
            return None

    def scrape_document(self, document_url: str) -> Dict:
        """Scrape metadata from a single document page"""
        print(f"Scraping document: {document_url}")

        self.driver.get(document_url)
        time.sleep(3)  # Wait for page to load

        # Extract all metadata fields
        metadata = {
            "document_url": document_url,
            "original_publication_date": self._get_text_safe(".date"),
            "title": self._get_text_safe("h1.title"),
            "credits": self._get_text_safe(".donated"),
            "text_body": self._get_text_safe(".tab-pane.active"),  # Full transcript
            "summary": self._get_text_safe(".text-block"),  # Summary text
            "scraped_at": datetime.now().isoformat(),
        }

        # Extract data using the new helper methods
        metadata["authors"] = self._get_pill_list("Author")
        metadata["associated_places"] = self._get_pill_list("Associated Places")
        metadata["subjects_discussed"] = self._get_pill_list("Subjects Discussed")
        metadata["associated_people_orgs"] = self._get_pill_list("Associated People")

        # Extract information blocks
        metadata["source"] = self._get_information_block("Source")
        metadata["original_upload_date"] = self._get_information_block(
            "Original Uploaded Date"
        )
        metadata["original_archive_title"] = self._get_pill_list("Original Archive")
        metadata["language"] = self._get_pill_list("Language")
        metadata["rights"] = self._get_information_block("Rights")
        metadata["record_id"] = self._get_information_block("Record ID")
        metadata["original_classification"] = self._get_information_block(
            "Original Classification"
        )
        metadata["donors"] = self._get_pill_list("Donor")

        return metadata

    def save_document(self, metadata: Dict):
        """Save document metadata to database"""
        assert self.conn is not None
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO documents (
                document_url, page_number, original_publication_date, title, credits, text_body,
                summary, authors, associated_places, subjects_discussed,
                associated_people_orgs, source, original_upload_date,
                original_archive_title, language, rights, record_id,
                original_classification, donors, scraped_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                metadata["document_url"],
                metadata.get("page_number"),
                metadata.get("original_publication_date"),
                metadata.get("title"),
                metadata.get("credits"),
                metadata.get("text_body"),
                metadata.get("summary"),
                metadata.get("authors"),
                metadata.get("associated_places"),
                metadata.get("subjects_discussed"),
                metadata.get("associated_people_orgs"),
                metadata.get("source"),
                metadata.get("original_upload_date"),
                metadata.get("original_archive_title"),
                metadata.get("language"),
                metadata.get("rights"),
                metadata.get("record_id"),
                metadata.get("original_classification"),
                metadata.get("donors"),
                metadata["scraped_at"],
            ),
        )
        self.conn.commit()
        print(f"Saved document: {metadata.get('title', 'Unknown')}")

    def scrape_page(self, page_number: int):
        """Scrape all documents from a single search results page"""
        print(f"\n{'='*60}")
        print(f"Processing page {page_number}")
        print(f"{'='*60}")

        # Check if page already completed
        if self.is_page_completed(page_number):
            print(f"Page {page_number} already completed, skipping...")
            return

        # Get document links from the page
        document_links = self.get_document_links(page_number)

        if not document_links:
            print(f"No documents found on page {page_number}")
            # Still mark as completed to avoid retrying empty pages
            self.mark_page_completed(page_number)
            return

        # Scrape each document
        for i, doc_url in enumerate(document_links, 1):
            try:
                print(f"\nDocument {i}/{len(document_links)}")
                metadata = self.scrape_document(doc_url)
                metadata["page_number"] = page_number  # Add page number to metadata
                self.save_document(metadata)
                time.sleep(1)  # Be polite to the server
            except KeyboardInterrupt:
                # Re-raise KeyboardInterrupt to stop gracefully
                raise
            except Exception as e:
                print(f"Error scraping document {doc_url}: {e}")
                # Continue with next document

        # Mark page as completed
        self.mark_page_completed(page_number)

    def scrape_range(self, start_page: int = 0, end_page: int = 1615):
        """Scrape a range of pages"""
        print(f"Starting scraper for pages {start_page} to {end_page}")
        print("Press Ctrl+C to stop gracefully...\n")

        self._init_driver()

        try:
            for page_num in range(start_page, end_page + 1):
                try:
                    self.scrape_page(page_num)
                except KeyboardInterrupt:
                    print("\n\n" + "=" * 60)
                    print("Received interrupt signal (Ctrl+C)")
                    print("Stopping gracefully and saving progress...")
                    print("=" * 60)
                    raise  # Re-raise to be caught by outer try-except
                except Exception as e:
                    print(f"Error processing page {page_num}: {e}")
                    # Continue with next page
        except KeyboardInterrupt:
            print("Cleanup in progress...")
            self.get_stats()
            print("\nScraping stopped by user. Progress has been saved.")
        finally:
            self._close_driver()

        print("\nScraping completed!")

    def export_to_csv(self, output_file: str = "wilson_archive.csv"):
        """Export all documents from database to CSV"""
        print(f"Exporting data to {output_file}...")

        assert self.conn is not None
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM documents ORDER BY document_url")
        rows = cursor.fetchall()

        if not rows:
            print("No documents found in database")
            return

        # Get column names
        columns = [description[0] for description in cursor.description]

        # Find the index of page_number column
        page_number_idx = (
            columns.index("page_number") if "page_number" in columns else None
        )

        # Add page indexed columns after page_number
        if page_number_idx is not None:
            insert_idx = page_number_idx + 1
            columns.insert(insert_idx, "page_zero_indexed")
            columns.insert(insert_idx + 1, "page_one_indexed")
        else:
            # If page_number doesn't exist, add at the beginning after document_url
            columns.insert(1, "page_zero_indexed")
            columns.insert(2, "page_one_indexed")

        with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(columns)

            # Write rows with additional page index columns
            for row in rows:
                row_list = list(row)
                page_num = (
                    row_list[page_number_idx] if page_number_idx is not None else None
                )

                if page_number_idx is not None:
                    insert_idx = page_number_idx + 1
                    # Insert page_zero_indexed (same as page_number)
                    row_list.insert(insert_idx, page_num)
                    # Insert page_one_indexed (page_number + 1)
                    row_list.insert(
                        insert_idx + 1, page_num + 1 if page_num is not None else None
                    )
                else:
                    # If no page_number column, insert None values
                    row_list.insert(1, None)
                    row_list.insert(2, None)

                writer.writerow(row_list)

        print(f"Exported {len(rows)} documents to {output_file}")

    def get_stats(self):
        """Print database statistics"""
        assert self.conn is not None
        cursor = self.conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM documents")
        doc_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM completed_pages")
        page_count = cursor.fetchone()[0]

        print(f"\nDatabase Statistics:")
        print(f"  Documents scraped: {doc_count}")
        print(f"  Pages completed: {page_count}")

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


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
