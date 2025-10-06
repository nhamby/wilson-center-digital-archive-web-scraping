# Setup Guide

This guide will help you get started with the Wilson Center Digital Archive Web Scraper.

## Prerequisites

- Python 3.7 or higher
- Internet connection
- At least 1GB of free disk space (for the database)

## Installation Steps

### 1. Clone the repository

```bash
git clone https://github.com/nhamby/wilson-center-digital-archive-web-scraping.git
cd wilson-center-digital-archive-web-scraping
```

### 2. (Optional) Create a virtual environment

It's recommended to use a virtual environment to keep dependencies isolated:

```bash
# On Linux/Mac
python3 -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

This will install SeleniumBase, which includes:

- Selenium
- Undetected ChromeDriver
- Chrome browser management
- All necessary dependencies

### 4. Verify installation

```bash
python scraper.py --help
```

You should see the help message with available options.

## Quick Start

### Test with a small batch

Start by scraping just a few pages to make sure everything works:

```bash
python scraper.py --start-page 0 --end-page 5
```

This will:

1. Create a `wilson_archive.db` database file
2. Scrape pages 0-5 (approximately 60 documents)
3. Show progress as it runs
4. Display statistics when complete

### Check the results

```bash
# View statistics
python scraper.py --stats

# Export to CSV
python scraper.py --export
```

You can now open `wilson_archive.csv` in Excel, Google Sheets, or any spreadsheet application.

## Running the Full Scrape

To scrape all 1616 pages (approximately 16,160 documents):

```bash
python scraper.py
```

**Important Notes:**

- This will take several hours to complete (estimated 4-8 hours depending on connection speed)
- The database file will grow to approximately 500MB-1GB
- The scraper is designed to be stopped and resumed at any time
- Progress is saved after each page, so you can safely interrupt with Ctrl+C

### Resuming after interruption

If the scraper is interrupted for any reason, simply run it again:

```bash
python scraper.py
```

It will automatically skip pages that have already been completed.

## Advanced Usage

### Scrape a specific range

```bash
python scraper.py --start-page 100 --end-page 200
```

### Use a custom database file

```bash
python scraper.py --db my_archive.db
```

### Export from a specific database

```bash
python scraper.py --db my_archive.db --export
```

## Understanding the Output

### During scraping

```md
============================================================
Processing page 0
============================================================
Accessing page 0: https://digitalarchive.wilsoncenter.org/search?page=0
Found 10 document links on page 0

Document 1/10
Scraping document: https://digitalarchive.wilsoncenter.org/document/...
Saved document: [Document Title]

Document 2/10
...
```

### After completion

```md
Database Statistics:
  Documents scraped: 16160
  Pages completed: 1616
```

## Troubleshooting

### "No module named 'seleniumbase'"

Make sure you've installed the dependencies:

```bash
pip install -r requirements.txt
```

### "Permission denied" errors

Make sure you have write permissions in the current directory, or specify a database path where you have write access:

```bash
python scraper.py --db ~/Documents/wilson_archive.db
```

### Chrome/ChromeDriver issues

SeleniumBase manages ChromeDriver automatically. If you encounter issues:

1. Make sure you have Chrome browser installed
2. Update SeleniumBase: `pip install --upgrade seleniumbase`
3. Try running once with visible browser to see what's happening: edit `scraper.py` and change `headless=True` to `headless=False`

### Network timeouts

If you're experiencing frequent timeouts:

- Check your internet connection
- Try increasing the sleep delays in the code
- Make sure no firewall is blocking access

## Data Analysis

Once you've exported to CSV, you can:

- Open in Excel or Google Sheets for manual analysis
- Use pandas in Python for data analysis
- Import into a database for SQL queries
- Create visualizations with tools like Tableau

Example with pandas:

```python
import pandas as pd
import json

# Load the CSV
df = pd.read_csv('wilson_archive.csv')

# Parse JSON arrays
df['authors_list'] = df['authors'].apply(lambda x: json.loads(x) if pd.notna(x) else [])

# Analyze
print(f"Total documents: {len(df)}")
print(f"Documents with authors: {df['authors'].notna().sum()}")
print(f"\nMost common languages:")
print(df['language'].value_counts().head())
```

## Next Steps

After successful scraping:

1. Back up your database file (`wilson_archive.db`)
2. Export to CSV for analysis
3. Consider adding custom analysis scripts for your specific use case
4. Share your findings (respecting the rights and attribution in the documents)

## Support

For issues or questions:

- Check the main README.md for more details
- Open an issue on GitHub
- Review the code comments in scraper.py
