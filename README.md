# Wilson Center Digital Archive Web Scraper

A Python web scraper for the [Wilson Center Digital Archive](https://digitalarchive.wilsoncenter.org) that extracts document metadata and full text content. Uses SeleniumBase with undetected-chromedriver mode to avoid bot detection.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the scrape
python main.py

# Check results
python main.py --stats

# Export database to CSV
python main.py --export
```

## Features

- **Bot Detection Avoidance**: Uses SeleniumBase UC mode to bypass anti-scraping measures
- **Complete Metadata Extraction**: Captures 18+ fields including title, authors, places, subjects, full text, and more
- **Resume Capability**: Automatically skips completed pages; safe to interrupt with Ctrl+C
- **SQLite Database**: Local storage with proper schema and JSON arrays for multi-value fields
- **CSV Export**: One-command export for analysis in Excel, Python, R, etc.
- **Progress Tracking**: Real-time feedback and statistics

## Table of Contents

- [Installation](#installation)
- [Basic Usage](#basic-usage)
- [Command Reference](#command-reference)
- [Project Structure](#project-structure)
- [Database Schema](#database-schema)
- [Metadata Fields](#metadata-fields)
- [Architecture](#architecture)
- [Programmatic Usage](#programmatic-usage)

## Installation

### Prerequisites

- Python 3.7 or higher
- Internet connection
- ~1GB free disk space (for full database)

### Setup

```bash
# Clone the repository
git clone https://github.com/nhamby/wilson-center-digital-archive-web-scraping.git
cd wilson-center-digital-archive-web-scraping

# (Optional) Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
python main.py --help
```

## Basic Usage

### Run the Scraper

```bash
# Scrape all pages (1615 pages, 16,153 documents, takes 4-8 hours)
python main.py

# Scrape specific page range
python main.py --start-page 0 --end-page 10

# Resume from specific page
python main.py --start-page 500
```

The scraper will:

- Create `wilson_archive.db` if it doesn't exist already
- Extract metadata from each document
- Track completed pages for resume capability
- Handle Ctrl+C gracefully (progress is saved)

### Export Data

```bash
# Export to CSV (creates wilson_archive.csv)
python main.py --export

# Export with custom filename
python main.py --export --db custom.db
```

### Check Progress

```bash
# Show statistics
python main.py --stats

# Output example:
# Database Statistics:
#   Documents scraped: 1250
#   Pages completed: 125
```

## Command Reference

| Command | Description |
|---------|-------------|
| `python main.py` | Start/resume scraping all pages |
| `python main.py --start-page N` | Start from page N |
| `python main.py --end-page N` | End at page N |
| `python main.py --start-page N --end-page M` | Scrape pages N through M |
| `python main.py --export` | Export database to CSV |
| `python main.py --stats` | Show scraping statistics |
| `python main.py --db PATH` | Use custom database file |
| `python main.py --help` | Show all options |

## Project Structure

```file tree
wilson-center-digital-archive-web-scraping/
├── main.py              # CLI entry point
├── scraper.py           # Core WilsonArchiveScraper class
├── requirements.txt     # Python dependencies
├── wilson_archive.db    # SQLite database (auto-created)
└── wilson_archive.csv   # CSV export (created with --export)
```

### File Purposes

- **`main.py`**: Command-line interface with argument parsing
- **`scraper.py`**: Reusable scraper class with all business logic

## Database Schema

### `documents` Table

Stores all scraped document metadata. **Primary key**: `document_url`

| Column | Type | Description |
|--------|------|-------------|
| `document_url` | TEXT | Unique document URL (primary key) |
| `page_number` | INTEGER | Search page where found |
| `page_number_one_indexed` | INTEGER | Search page where found |
| `page_position` | INTEGER | Document position on search page |
| `original_publication_date` | TEXT | Document's original date |
| `title` | TEXT | Document title |
| `credits` | TEXT | Credits/attribution |
| `text_body` | TEXT | Full document text content |
| `summary` | TEXT | Document summary |
| `authors` | TEXT | JSON array of authors |
| `associated_places` | TEXT | JSON array of geographic locations |
| `subjects_discussed` | TEXT | JSON array of topics |
| `associated_people_orgs` | TEXT | JSON array of people/organizations |
| `document_contributors` | TEXT | JSON array of document contributors |
| `source` | TEXT | Document source |
| `original_upload_date` | TEXT | Upload date to archive |
| `original_archive_title` | TEXT | Original archive name |
| `language` | TEXT | JSON array of languages |
| `rights` | TEXT | Rights information |
| `record_id` | TEXT | Unique record identifier |
| `original_classification` | TEXT | Classification level |
| `donors` | TEXT | JSON array of donors |
| `scraped_at` | TEXT | Timestamp when scraped |

**Note**: Fields marked as JSON arrays are stored as JSON-encoded strings (e.g., `["English", "German"]`).

### `completed_pages` Table

Tracks scraping progress. **Primary key**: `page_number`

| Column | Type | Description |
|--------|------|-------------|
| `page_number` | INTEGER | Page number (0-1615) |
| `completed_at` | TEXT | ISO timestamp when completed |

## Metadata Fields

The scraper extracts **18 metadata fields** from each document:

**Core Fields:**

- Document URL (unique identifier)
- Title
- Original Publication Date
- Credits
- Text Body (full content)
- Summary

**Categorization (Multi-value):**

- Authors
- Associated Places
- Document Contributors
- Subjects Discussed
- Associated People & Organizations
- Donors

**Archive Information:**

- Source
- Original Upload Date
- Original Archive Title
- Language
- Rights
- Record ID
- Original Classification

**Tracking:**

- Page Number (where document was found)
- Page Number One Indexed (where document was found)
- Page Position (where document was found)
- Scraped At (timestamp)

## Architecture

### Data Flow

```data flow
User → main.py (CLI) → scraper.py (WilsonArchiveScraper)
                              ↓
                        ┌─────┴─────┐
                        ↓           ↓
                  SeleniumBase   SQLite
                   (Web Scraping) (Storage)
                        ↓           ↓
                  Wilson Center   wilson_archive.db
                   Digital Archive
```

### How It Works

1. **Page Navigation**: Loops through search pages (0-1615)
   - URL pattern: `https://digitalarchive.wilsoncenter.org/search?page={N}`
   - Each page contains ~10 document links

2. **Link Extraction**: Finds document links on each search page
   - Selector: `td.document.contextual-region a`
   - Extracts URLs containing `/document/`

3. **Metadata Scraping**: For each document:
   - Opens document page with SeleniumBase
   - Extracts metadata using CSS selectors
   - Uses helper methods for complex structures:
     - `_get_text_safe()`: Single text values
     - `_get_information_block()`: Information blocks
     - `_get_pill_list()`: Multi-value pill lists
   - Stores as JSON arrays for multi-value fields

4. **Data Persistence**: Saves to SQLite database
   - `INSERT OR REPLACE` for idempotency
   - Marks page as completed after all documents saved

5. **Resume Support**: Checks `completed_pages` on startup
   - Automatically skips completed pages
   - Graceful Ctrl+C handling saves progress

### Key Design Features

- **Separation of Concerns**: CLI (`main.py`) separate from logic (`scraper.py`)
- **Bot Detection Avoidance**: SeleniumBase UC mode bypasses anti-scraping
- **Polite Scraping**: 1-3 second delays between requests
- **Error Handling**: Continues on individual document failures
- **Idempotent Operations**: Re-scraping same document updates existing record

## Programmatic Usage

Import and use the scraper in your own Python scripts:

```python
from scraper import WilsonArchiveScraper

# Initialize
scraper = WilsonArchiveScraper('my_database.db')

# Scrape pages
scraper.scrape_range(0, 10)

# Scrape single document
doc = scraper.scrape_document('https://digitalarchive.wilsoncenter.org/document/...')
print(f"Title: {doc['title']}")
print(f"Summary: {doc['summary']}")

# Check if page completed
if scraper.is_page_completed(5):
    print("Page 5 is done")

# Export data
scraper.export_to_csv('output.csv')

# Get statistics
scraper.get_stats()

# Clean up
scraper.close()
```

### Data Analysis Example

```python
import pandas as pd
import json

# Load exported CSV
df = pd.read_csv('wilson_archive.csv')

# Parse JSON fields
df['authors_list'] = df['authors'].apply(
    lambda x: json.loads(x) if pd.notna(x) else []
)

# Analyze
print(f"Total documents: {len(df)}")
print(f"Documents with authors: {df['authors'].notna().sum()}")
print(f"\nTop languages:")
print(df['language'].value_counts().head())
```

## Performance & Estimates

- **Total Pages**: 1,616 (pages 0-1615)
- **Documents per Page**: 10
- **Total Documents**: 16,153
- **Estimated Runtime**: 4-8 hours for full scrape
- **Database Size**: ~500MB-1GB when complete

## Tips & Best Practices

- Start with a test run (5-10 pages)
- Run overnight for full scrapes
- Back up database file periodically
- Use `--stats` to monitor progress
- Export to CSV when complete

## Ideas for the Future

- Add progress bar (tqdm)
- Implement logging module
- Add retry logic for failed documents
- Support for parallel scraping
- Docker containerization

## License

MIT License - See LICENSE file for details

## Acknowledgments

Data sourced from the [Wilson Center Digital Archive](https://digitalarchive.wilsoncenter.org). Please respect their Terms of Service and properly attribute data in any publications or analyses.
