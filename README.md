# Facebook Marketplace Vehicle Scraper

** PLEASE USE A DISPOSABLE FACEBOOK ACCOUNT NOT YOUR MAIN ONE**

## Description
This script automates the process of scraping vehicle listings from Facebook Marketplace based on your specified criteria (make, model, price range, mileage, etc.). It uses Playwright for browser automation and BeautifulSoup for parsing the data.

## Prerequisites
- Python 3.x
- Playwright
- BeautifulSoup
- pandas
- python-dotenv

Install the required packages with:
```
pip install playwright beautifulsoup4 pandas python-dotenv
playwright install
```

## Important Setup
**You must create a `.env` file in the project root directory with your Facebook credentials:**

```
FACEBOOK_EMAIL=your_facebook_email@example.com
FACEBOOK_PASSWORD=your_facebook_password
```

Without this file containing your valid credentials, the script will not work!

## Usage
1. Set your search parameters in the script's SETTINGS section:
   - Location (e.g., 'nyc')
   - Price range
   - Vehicle specifications (make, model, year range, etc.)
   - scroll_count (how many times to scroll for more listings)

2. Run the script:
```
python scrape_marketplace.py
```

## Output
The script saves the scraped data in two formats:
- `DATA/vehicles.json` (JSON format)
- `DATA/vehicles.csv` (CSV format)

## Notes
- The script saves your login session to avoid repeated logins
- It runs in headed mode by default (you can see the browser)
- Be careful with your credentials - never commit the `.env` file to version control

## Disclaimer
Use this script responsibly and in compliance with Facebook's Terms of Service. The developers are not responsible for any misuse or consequences of using this script.