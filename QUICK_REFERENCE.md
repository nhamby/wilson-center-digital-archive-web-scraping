# Quick Reference Guide

## Command Cheat Sheet

### Basic Commands

```bash
# Full scrape (all 1616 pages)
python scraper.py

# Scrape specific page range
python scraper.py --start-page 0 --end-page 10

# Resume from specific page
python scraper.py --start-page 500

# Export to CSV
python scraper.py --export

# Check statistics
python scraper.py --stats

# Use custom database
python scraper.py --db my_archive.db

# Help
python scraper.py --help
```

## Common Workflows

### First Time Setup
```bash
pip install -r requirements.txt
python scraper.py --start-page 0 --end-page 5  # Test run
python scraper.py --stats                       # Check results
python scraper.py --export                       # Export test data
```

### Full Production Scrape
```bash
python scraper.py                                # Start scraping
# Wait (may take 4-8 hours)
python scraper.py --stats                       # Verify completion
python scraper.py --export                       # Export all data
```

### Interrupted Scrape Recovery
```bash
python scraper.py --stats                       # Check what's done
python scraper.py                                # Resume from where it left off
```

## File Structure

```
wilson-center-digital-archive-web-scraping/
├── scraper.py              # Main scraper script
├── requirements.txt        # Python dependencies
├── README.md              # Full documentation
├── SETUP.md               # Installation guide
├── example_usage.py       # Code examples
├── wilson_archive.db      # SQLite database (created after first run)
└── wilson_archive.csv     # CSV export (created with --export)
```

## Database Schema Quick Reference

### documents table
| Column | Type | Description |
|--------|------|-------------|
| document_url | TEXT (PK) | Full URL to document |
| title | TEXT | Document title |
| authors | TEXT (JSON) | List of authors |
| summary | TEXT | Document summary |
| text_body | TEXT | Full text content |
| ... | ... | (14 more fields) |

### completed_pages table
| Column | Type | Description |
|--------|------|-------------|
| page_number | INTEGER (PK) | Page number |
| completed_at | TEXT | Completion timestamp |

## Metadata Fields

The scraper extracts **18 metadata fields** from each document:
1. Document URL (unique identifier)
2. Original Publication Date
3. Title
4. Credits
5. Text Body
6. Summary
7. Authors (multiple)
8. Associated Places (multiple)
9. Subjects Discussed (multiple)
10. Associated People & Organizations (multiple)
11. Source
12. Original Upload Date
13. Original Archive Title
14. Language
15. Rights
16. Record ID
17. Original Classification
18. Donors (multiple)

Fields marked as (multiple) are stored as JSON arrays.

## Estimated Metrics

- **Total Pages**: 1616 (pages 0-1615)
- **Documents per Page**: ~10 (except last page)
- **Total Documents**: ~16,160
- **Estimated Runtime**: 4-8 hours for full scrape
- **Database Size**: ~500MB-1GB when complete
- **Network Usage**: ~100-200MB download

## Python API Usage

```python
from scraper import WilsonArchiveScraper

# Create scraper instance
scraper = WilsonArchiveScraper(db_path="my_archive.db")

# Scrape pages
scraper.scrape_range(start_page=0, end_page=10)

# Check if page is completed
if scraper.is_page_completed(5):
    print("Page 5 is done")

# Get statistics
scraper.get_stats()

# Export to CSV
scraper.export_to_csv("my_export.csv")

# Close connection
scraper.close()
```

## Troubleshooting Quick Fixes

| Problem | Solution |
|---------|----------|
| Module not found | `pip install -r requirements.txt` |
| Chrome driver error | `pip install --upgrade seleniumbase` |
| Database locked | Close other programs accessing the .db file |
| Network timeout | Check internet connection, try again |
| Permission denied | Run from directory with write permissions |
| No documents found | Website may be down, try later |

## URLs and Patterns

- **Search pages**: `https://digitalarchive.wilsoncenter.org/search?page={0-1615}`
- **Document pages**: `https://digitalarchive.wilsoncenter.org/document/{slug}`
- **Base URL**: `https://digitalarchive.wilsoncenter.org`

## Key Features

✓ Bot detection avoidance (SeleniumBase UC mode)  
✓ Automatic resume after interruption  
✓ Progress tracking per page  
✓ CSV export functionality  
✓ Comprehensive metadata extraction  
✓ Error handling and recovery  
✓ Polite scraping with delays  
✓ SQLite database storage  

## Tips

- Start with a small range to test (e.g., pages 0-5)
- Run scraper overnight for full scrape
- Back up the .db file periodically
- Use `--stats` frequently to monitor progress
- Export to CSV when scraping is complete
- The scraper can be safely interrupted with Ctrl+C
