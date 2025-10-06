# Wilson Center Digital Archive Web Scraper

A web scraper for the Wilson Center Digital Archive using SeleniumBase to avoid bot detection.

## Features

- Scrapes search results from pages 0-1615
- Extracts document links and detailed metadata
- Stores data in SQLite database
- Tracks progress to support resuming after interruption
- Exports data to CSV format

## Installation

1. Install Python 3.7 or higher
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Run the scraper

```bash
python scraper.py
```

The scraper will:
- Create a database file `wilson_archive.db` if it doesn't exist
- Start from page 0 (or resume from where it left off)
- Scrape each page and extract document metadata
- Mark pages as complete in the database

### Export to CSV

```bash
python scraper.py --export
```

This will create a `wilson_archive.csv` file with all scraped documents.

### Resume from specific page

```bash
python scraper.py --start-page 100
```

### Scrape specific page range

```bash
python scraper.py --start-page 100 --end-page 200
```

## Database Schema

### documents table
Stores all document metadata:
- document_url (PRIMARY KEY)
- original_publication_date
- title
- credits
- text_body
- summary
- authors (JSON array)
- associated_places (JSON array)
- subjects_discussed (JSON array)
- associated_people_orgs (JSON array)
- source
- original_upload_date
- original_archive_title
- language
- rights
- record_id
- original_classification
- donors (JSON array)
- scraped_at (timestamp)

### completed_pages table
Tracks which pages have been fully scraped:
- page_number (PRIMARY KEY)
- completed_at (timestamp)

## License

MIT License - See LICENSE file for details
