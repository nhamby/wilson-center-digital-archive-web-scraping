"""
Wilson Center Digital Archive Web Scraper

This module contains the WilsonArchiveScraper class for scraping documents
from the Wilson Center Digital Archive using SeleniumBase to avoid bot detection.
It stores data in a SQLite database and supports resuming.
"""

import csv
import json
import sqlite3
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
        self.driver: Any = None
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database with required schema"""
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                document_url TEXT PRIMARY KEY,
                page_number INTEGER,
                page_position INTEGER,
                original_publication_date TEXT,
                title TEXT,
                credits TEXT,
                text_body TEXT,
                summary TEXT,
                authors TEXT,
                associated_places TEXT,
                subjects_discussed TEXT,
                associated_people_orgs TEXT,
                document_contributors TEXT,
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

        try:
            cursor.execute("ALTER TABLE documents ADD COLUMN page_number INTEGER")
            self.conn.commit()
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute(
                "ALTER TABLE documents ADD COLUMN document_contributors TEXT"
            )
            self.conn.commit()
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE documents ADD COLUMN page_position INTEGER")
            self.conn.commit()
        except sqlite3.OperationalError:
            pass

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_documents_page_number 
            ON documents(page_number)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_documents_page_position 
            ON documents(page_number, page_position)
        """
        )

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

    def get_document_links(self, page_number: int) -> List[str]:
        """Extract document links from a search results page"""
        url = self.SEARCH_URL.format(page_number)
        print(f"Accessing page {page_number}: {url}")

        self.driver.get(url)
        time.sleep(5)

        links = []
        try:
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
                print("No elements found with any selector. Checking page structure...")
                page_source = self.driver.page_source[:1000]
                print(f"Page source preview: {page_source}")

            for element in elements:
                href = element.get_attribute("href")

                if href and "/document/" in href:

                    if href.startswith("/"):
                        full_url = self.BASE_URL + href
                    else:
                        full_url = href

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
            h2_elements = self.driver.find_elements("css selector", "h2.title")
            for h2 in h2_elements:
                try:
                    if title.lower() in h2.text.lower():
                        next_elem = self.driver.execute_script(
                            "return arguments[0].nextElementSibling;", h2
                        )
                        if next_elem:
                            pills = self.driver.execute_script(
                                'return Array.from(arguments[0].querySelectorAll(".pill .name span"));',
                                next_elem,
                            )
                            if pills:
                                names = [
                                    p.text.strip() for p in pills if p.text.strip()
                                ]
                                return json.dumps(names) if names else None
                except:
                    continue

            blocks = self.driver.find_elements(
                "css selector", ".pill-block, .information-block"
            )
            for block in blocks:
                try:
                    title_els = block.find_elements(
                        "css selector", "h3.title, h4.title, h3.sub-title"
                    )
                    for title_el in title_els:
                        if title.lower() in title_el.text.lower():
                            pills = block.find_elements(
                                "css selector", ".pill .name span"
                            )
                            if not pills:
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
        time.sleep(3)

        metadata = {
            "document_url": document_url,
            "original_publication_date": self._get_text_safe(".date"),
            "title": self._get_text_safe("h1.title"),
            "credits": self._get_text_safe(".donated"),
            "text_body": self._get_text_safe(".tab-pane.active"),
            "summary": self._get_text_safe(".text-block"),
            "scraped_at": datetime.now().isoformat(),
        }

        metadata["authors"] = self._get_pill_list("Author")
        metadata["associated_places"] = self._get_pill_list("Associated Places")
        metadata["subjects_discussed"] = self._get_pill_list("Subjects Discussed")
        metadata["associated_people_orgs"] = self._get_pill_list("Associated People")
        metadata["document_contributors"] = self._get_pill_list("Document Contributor")

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
                document_url, page_number, page_position, original_publication_date, title, credits, text_body,
                summary, authors, associated_places, subjects_discussed,
                associated_people_orgs, document_contributors, source, original_upload_date,
                original_archive_title, language, rights, record_id,
                original_classification, donors, scraped_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                metadata["document_url"],
                metadata.get("page_number"),
                metadata.get("page_position"),
                metadata.get("original_publication_date"),
                metadata.get("title"),
                metadata.get("credits"),
                metadata.get("text_body"),
                metadata.get("summary"),
                metadata.get("authors"),
                metadata.get("associated_places"),
                metadata.get("subjects_discussed"),
                metadata.get("associated_people_orgs"),
                metadata.get("document_contributors"),
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
        page_start_time = time.time()

        print(f"\n{'='*60}")
        print(f"Processing page {page_number}")
        print(f"{'='*60}")

        if self.is_page_completed(page_number):
            print(f"Page {page_number} already completed, skipping...")
            return

        document_links = self.get_document_links(page_number)

        if not document_links:
            print(f"No documents found on page {page_number}")
            self.mark_page_completed(page_number)
            return

        for i, doc_url in enumerate(document_links, 1):
            try:
                print(f"\nDocument {i}/{len(document_links)}")
                metadata = self.scrape_document(doc_url)
                metadata["page_number"] = page_number
                metadata["page_position"] = i
                self.save_document(metadata)
                time.sleep(1)
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"Error scraping document {doc_url}: {e}")

        self.mark_page_completed(page_number)

        page_elapsed_time = time.time() - page_start_time
        minutes = int(page_elapsed_time // 60)
        seconds = int(page_elapsed_time % 60)
        print(f"Page {page_number} marked as completed ({minutes}m {seconds}s)")

    def scrape_range(self, start_page: int = 0, end_page: int = 1615):
        """Scrape a range of pages"""
        print(f"Starting scraper for pages {start_page} to {end_page}")

        self._init_driver()

        try:
            for page_num in range(start_page, end_page + 1):
                try:
                    self.scrape_page(page_num)
                except KeyboardInterrupt:
                    raise
                except Exception as e:
                    print(f"Error processing page {page_num}: {e}")
        except KeyboardInterrupt:
            self.get_stats()
        finally:
            self._close_driver()

    def export_to_csv(self, output_file: str = "wilson_archive.csv"):
        """Export all documents from database to CSV ordered by page number and position"""
        print(f"\nExporting data to {output_file}")

        assert self.conn is not None
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM documents ORDER BY page_number ASC, page_position ASC, document_url ASC"
        )
        rows = cursor.fetchall()

        if not rows:
            print("No documents found in database")
            return

        columns = [description[0] for description in cursor.description]

        page_number_idx = (
            columns.index("page_number") if "page_number" in columns else None
        )

        if page_number_idx is not None:
            insert_idx = page_number_idx + 1
            columns.insert(insert_idx, "page_number_one_indexed")
        else:
            columns.insert(1, "page_number_one_indexed")

        with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(columns)

            for row in rows:
                row_list = list(row)
                page_num = (
                    row_list[page_number_idx] if page_number_idx is not None else None
                )

                if page_number_idx is not None:
                    insert_idx = page_number_idx + 1
                    row_list.insert(
                        insert_idx, page_num + 1 if page_num is not None else None
                    )
                else:
                    row_list.insert(1, None)

                writer.writerow(row_list)

        print(f"Exported {len(rows)} documents to {output_file}\n")

    def get_stats(self):
        """Print database statistics"""
        assert self.conn is not None
        cursor = self.conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM documents")
        doc_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM completed_pages")
        page_count = cursor.fetchone()[0]

        print(f"\n\nDatabase Statistics:")
        print(f"    Documents scraped: {doc_count}")
        print(f"    Pages completed: {page_count}\n")

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
