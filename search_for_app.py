#!/usr/bin/env python3
"""
Wrapper script for the Facebook Marketplace scraper.
Called by the car-search app via child_process.
Accepts search params as CLI args and outputs JSON to stdout.
"""

import sys
import time
import json
import os
import argparse
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()


def abort_requests(route, request):
    if request.resource_type == "image" or any(ext in request.url.lower() for ext in [".png", ".jpg", ".jpeg"]):
        route.abort()
        return
    if request.resource_type == "media" or any(ext in request.url.lower() for ext in [".mp4", ".webm", ".avi"]):
        route.abort()
        return
    route.continue_()


def scrape(args):
    email = args.email or os.getenv('FACEBOOK_EMAIL')
    password = args.password or os.getenv('FACEBOOK_PASSWORD')

    if not email or not password:
        print(json.dumps({"error": "FACEBOOK_EMAIL and FACEBOOK_PASSWORD required"}))
        sys.exit(1)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    storage_dir = os.path.join(script_dir, 'SESSIONS', 'StorageCookies')
    os.makedirs(storage_dir, exist_ok=True)
    storage = os.path.join(storage_dir, f'{email}.json')

    # Parse makes_models JSON if provided
    makes_models = []
    if args.makes_models:
        try:
            makes_models = json.loads(args.makes_models)
        except json.JSONDecodeError:
            makes_models = [args.makes_models]

    # Build location from zip (FB uses city names, fall back to zip)
    location = args.location or args.zip or 'losangeles'

    all_vehicles = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)

        if os.path.isfile(storage):
            context = browser.new_context(storage_state=storage, locale="en-GB", color_scheme='dark')
        else:
            context = browser.new_context(locale="en-GB", color_scheme='dark')

        page = context.new_page()
        page.route("**/*", abort_requests)

        # Login if no session
        base_url = 'https://web.facebook.com/marketplace/'
        page.goto(base_url)
        page.wait_for_timeout(5000)

        if not os.path.isfile(storage):
            try:
                page.get_by_role("textbox", name="Email address or phone number").click()
                page.keyboard.type(email)
                page.wait_for_timeout(2000)
                # Find password field
                pwd_fields = page.locator('input[type="password"]')
                if pwd_fields.count() > 0:
                    pwd_fields.first.click()
                else:
                    page.locator("input[id='«r15»']").click()
                page.keyboard.type(password)
                page.wait_for_timeout(1000)
                page.get_by_role("button", name="Log in to Facebook").click()
                page.wait_for_timeout(5000)
                page.context.storage_state(path=storage)
            except Exception as e:
                print(json.dumps({"error": f"Login failed: {str(e)}"}), file=sys.stderr)

        # Search for each make/model combo
        search_queries = makes_models if makes_models else [f"{args.make or 'Toyota'} {args.model or 'Tacoma'}"]
        radius = args.radius or 80  # miles

        for query in search_queries:
            url = (
                f"{base_url}{location}/search?"
                f"minPrice={args.price_min or 1000}"
                f"&maxPrice={args.price_max or 15000}"
                f"&daysSinceListed={args.days_listed or 14}"
                f"&maxMileage={args.mileage_max or 200000}"
                f"&minYear={args.year_min or 2005}"
                f"&maxYear={args.year_max or 2025}"
                f"&transmissionType=automatic"
                f"&topLevelVehicleType=truck%2Fsuv"
                f"&query={query}"
                f"&radius={radius}"
                f"&exact=true"
            )

            try:
                page.goto(url)
                page.wait_for_timeout(3000)

                scroll_count = args.scroll_count or 5
                seen_vehicles = set()
                unique_vehicles = []

                for i in range(scroll_count):
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                    try:
                        new_vehicles = page.evaluate("""() => {
                            const results = [];
                            // FB listing cards are links inside the main feed
                            const links = document.querySelectorAll('a[href*="/marketplace/item/"]');
                            const seen = new Set();
                            for (const link of links) {
                                const href = link.getAttribute('href');
                                if (seen.has(href)) continue;
                                seen.add(href);
                                // Walk up to find the card container and extract text
                                const card = link.closest('div[class]') || link;
                                const text = card.innerText || '';
                                const lines = text.split('\\n').map(l => l.trim()).filter(l => l.length > 0);

                                let price = null, title = null, location = null, mileage = null;
                                for (const line of lines) {
                                    // Price: "$X,XXX"
                                    if (/^\\$[\\d,]+$/.test(line) && !price) {
                                        price = line;
                                        continue;
                                    }
                                    // Title: "2015 Toyota tundra..." (starts with year)
                                    if (/^(19|20)\\d{2}\\s+/.test(line) && !title) {
                                        title = line;
                                        continue;
                                    }
                                    // Location: "City, ST" or "City, CA"
                                    if (/^[A-Z][a-z].*,\\s*[A-Z]{2}$/.test(line) && !location) {
                                        location = line;
                                        continue;
                                    }
                                    // Mileage: "131K miles" or "131,000 miles"
                                    if (/miles$/i.test(line) && !mileage) {
                                        mileage = line;
                                        continue;
                                    }
                                }
                                if (title || price) {
                                    // Parse title into year/make/model
                                    const parts = (title || '').split(/\\s+/);
                                    const year = parts[0] || '';
                                    const make = parts[1] || '';
                                    const model = parts.slice(2).join(' ') || '';
                                    // Parse mileage number
                                    let miles = '';
                                    if (mileage) {
                                        const m = mileage.match(/([\\d,.]+)\\s*K?/i);
                                        if (m) {
                                            let num = m[1].replace(',', '');
                                            if (mileage.includes('K')) num = String(Math.round(parseFloat(num) * 1000));
                                            miles = num;
                                        }
                                    }
                                    // Get image
                                    const img = link.querySelector('img');
                                    const image_url = img ? img.src : '';

                                    results.push({
                                        year, make, model, price: price || '',
                                        location: location || '', mileage: miles ? parseInt(miles) : '',
                                        image_url, listing_url: 'https://www.facebook.com' + href
                                    });
                                }
                            }
                            return results;
                        }""")
                        for vehicle in new_vehicles:
                            vehicle_id = vehicle.get('listing_url', '')
                            if vehicle_id and vehicle_id not in seen_vehicles:
                                seen_vehicles.add(vehicle_id)
                                unique_vehicles.append(vehicle)
                    except Exception as e:
                        print(f"Parse error on scroll {i}: {e}", file=sys.stderr)
                    page.wait_for_timeout(2000)

                all_vehicles.extend(unique_vehicles)
            except Exception as e:
                print(f"Error searching {query}: {e}", file=sys.stderr)

        context.close()
        browser.close()

    # Output JSON to stdout for the Node.js wrapper to parse
    print(json.dumps(all_vehicles))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='FB Marketplace vehicle scraper')
    parser.add_argument('--email', help='Facebook email')
    parser.add_argument('--password', help='Facebook password')
    parser.add_argument('--zip', default='92646')
    parser.add_argument('--location', default='losangeles', help='FB marketplace location slug')
    parser.add_argument('--price-min', type=int, default=1000)
    parser.add_argument('--price-max', type=int, default=15000)
    parser.add_argument('--mileage-max', type=int, default=200000)
    parser.add_argument('--year-min', type=int, default=2005)
    parser.add_argument('--year-max', type=int, default=2025)
    parser.add_argument('--days-listed', type=int, default=14)
    parser.add_argument('--makes-models', help='JSON array like \'["Toyota Tacoma","Toyota 4Runner"]\'')
    parser.add_argument('--make', default='Toyota')
    parser.add_argument('--model', default='Tacoma')
    parser.add_argument('--radius', type=int, default=80, help='Search radius in miles')
    parser.add_argument('--scroll-count', type=int, default=5)
    args = parser.parse_args()
    scrape(args)
