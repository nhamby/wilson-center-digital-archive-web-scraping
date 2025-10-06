# Wilson Center Digital Archive Web Scraper

A web scraper for the Wilson Center Digital Archive using SeleniumBase to avoid bot detection.

## Features

- **Bot Detection Avoidance**: Uses SeleniumBase with undetected-chromedriver mode to avoid triggering `triggerInterstitialChallenge()` functions
- **Page-by-Page Scraping**: Scrapes search results from pages 0-1615 (10 documents per page, except the last)
- **Complete Metadata Extraction**: Extracts 18 different metadata fields from each document
- **SQLite Database Storage**: All data stored in a local SQLite database with proper schema
- **Resume Capability**: Tracks completed pages to support resuming after interruption
- **CSV Export**: Export all scraped data to CSV format for analysis
- **Progress Tracking**: Shows real-time progress and statistics

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
- Automatically skip pages that have already been completed

### Export to CSV

```bash
python scraper.py --export
```

This will create a `wilson_archive.csv` file with all scraped documents.

### Check statistics

```bash
python scraper.py --stats
```

This will show how many documents and pages have been scraped.

### Resume from specific page

```bash
python scraper.py --start-page 100
```

This will start scraping from page 100 through page 1615.

### Scrape specific page range

```bash
python scraper.py --start-page 100 --end-page 200
```

This will only scrape pages 100-200.

### Use custom database file

```bash
python scraper.py --db custom_archive.db
```

This will use a custom database file instead of the default `wilson_archive.db`.

## Examples

### Full scrape from beginning

```bash
python scraper.py
```

### Resume interrupted scrape

If the scraper is interrupted, simply run it again. It will automatically skip completed pages:

```bash
python scraper.py
```

### Scrape a small test batch

```bash
python scraper.py --start-page 0 --end-page 5
```

### Export and analyze data

```bash
python scraper.py --export
# Now you can open wilson_archive.csv in Excel or other tools
```

## Metadata Fields Extracted

For each document, the scraper extracts the following fields:

| Field | Description | HTML Selector | Multiple Values |
|-------|-------------|---------------|-----------------|
| Document URL | Full URL to the document | Constructed from href | No |
| Original Publication Date | When document was originally published | `.date` | No |
| Title | Document title | `.title` | No |
| Credits | Credits information | `.donated` | No |
| Text Body | Full text content | `.Textbody` | No |
| Summary | Document summary | `.text-block` | No |
| Authors | Document authors | `div.field--name-field-authors .name` | Yes (JSON array) |
| Associated Places | Geographic locations | `div.field--name-field-places .name` | Yes (JSON array) |
| Subjects Discussed | Topics covered | `div.field--name-field-topics .name` | Yes (JSON array) |
| Associated People & Organizations | Related entities | `div.field--name-field-people-orgs .name` | Yes (JSON array) |
| Source | Document source | `div.field--name-field-source .text` | No |
| Original Upload Date | When uploaded to archive | `div.field--name-field-date-uploaded .text` | No |
| Original Archive Title | Original archive name | `div.field--name-field-original-archive .name` | No |
| Language | Document language | `div.field--name-field-language .name` | No |
| Rights | Rights information | `div.field--name-field-rights .text` | No |
| Record ID | Unique record identifier | `div.field--name-field-record-id .text` | No |
| Original Classification | Classification level | `div.field--name-field-original-classification .text` | No |
| Donors | Archive donors | `div.field--name-field-donors .name` | Yes (JSON array) |
| Scraped At | Timestamp of scraping | Generated | No |

## Database Schema

### documents table

Stores all document metadata with 19 columns (all fields listed above)

**Primary Key**: `document_url`

Fields with multiple values (authors, places, subjects, people/orgs, donors) are stored as JSON arrays.

### completed_pages table

Tracks which pages have been fully scraped:

- `page_number` (INTEGER, PRIMARY KEY) - Page number that was completed
- `completed_at` (TEXT) - ISO timestamp when page was completed

## How It Works

1. **Page Traversal**: The scraper loops through pages 0-1615 using the URL pattern `https://digitalarchive.wilsoncenter.org/search?page={N}`

2. **Link Extraction**: On each search results page, it finds all document links by looking for anchor tags containing `/document/` in the href attribute

3. **Metadata Scraping**: For each document link, it:
   - Navigates to the document page
   - Extracts all metadata fields using CSS selectors
   - Handles multiple values (like authors) by storing them as JSON arrays
   - Saves everything to the SQLite database

4. **Progress Tracking**: After successfully scraping all documents on a page, it marks that page as completed in the `completed_pages` table

5. **Resume Support**: When restarted, the scraper checks which pages are already completed and skips them

## Troubleshooting

### No documents found on a page

- The page might not have loaded completely. The scraper waits 5 seconds after loading each page.
- The CSS selectors might have changed. Check the website's HTML structure.
- The website might be blocking the scraper (though SeleniumBase with UC mode should prevent this).

### Network errors

- Ensure you have a stable internet connection
- Some networks may block the Wilson Center domain
- Check if a firewall or proxy is interfering

### Chrome/ChromeDriver issues

- SeleniumBase manages ChromeDriver automatically
- If you get driver errors, try: `pip install --upgrade seleniumbase`

### Database locked errors

- Make sure no other process is accessing the database file
- Close any SQLite browsers/viewers that might have the database open

## Implementation Notes

- **SeleniumBase with UC Mode**: Uses undetected-chromedriver mode to avoid bot detection mechanisms
- **Headless Mode**: Runs in headless mode by default for efficiency
- **Polite Scraping**: Includes 1-2 second delays between requests to be respectful to the server
- **Error Handling**: Continues scraping even if individual documents fail
- **Data Integrity**: Uses `INSERT OR REPLACE` to handle re-scraping of documents
- **JSON Storage**: Multi-value fields stored as JSON arrays for easy parsing

## License

MIT License - See LICENSE file for details
