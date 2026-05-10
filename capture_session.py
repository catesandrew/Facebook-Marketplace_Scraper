#!/usr/bin/env python3
"""
Opens a browser to Facebook. You log in manually, solve any CAPTCHA,
then press Enter here to save the session for the scraper to reuse.
"""

import os
import sys
from playwright.sync_api import sync_playwright

email = sys.argv[1] if len(sys.argv) > 1 else os.getenv('FACEBOOK_EMAIL', 'plumhorse83@gmail.com')

script_dir = os.path.dirname(os.path.abspath(__file__))
storage_dir = os.path.join(script_dir, 'SESSIONS', 'StorageCookies')
os.makedirs(storage_dir, exist_ok=True)
storage_path = os.path.join(storage_dir, f'{email}.json')

print(f"Opening Facebook in a browser window...")
print(f"Log in manually, solve any CAPTCHA, then come back here and press Enter.")
print(f"Session will be saved to: {storage_path}")
print()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(locale="en-GB", color_scheme="dark")
    page = context.new_page()
    page.goto("https://www.facebook.com/marketplace/")

    input(">>> Press Enter after you've logged in and can see Marketplace... ")

    context.storage_state(path=storage_path)
    print(f"\nSession saved to {storage_path}")
    print("You can now close this window and use the scraper.")

    context.close()
    browser.close()
