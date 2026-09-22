#!/usr/bin/env python3
"""Track the price of one specific Royal Caribbean sailing over time.

Cruise being tracked (see README.md for how to change it):
  Ship:       Liberty of the Seas
  Itinerary:  5-night Western Caribbean Cruise, roundtrip from Galveston, TX
  Sail date:  Saturday, Feb 1 - Friday, Feb 6, 2027
  Source URL: royalcaribbean.com cruise search, itinerary LB05GAL-2956042566

The page is a JS-rendered SPA, so this uses Playwright (headless Chromium)
rather than a plain HTTP request. It finds the date-selector button whose
label matches the target sail dates and pulls the "lowest price" dollar
amount shown on that button, then appends a row to price_history.csv.

Exits non-zero (and saves a debug screenshot + HTML dump) if the expected
elements can't be found, so a broken selector shows up as a failed CI run
instead of silently logging nothing.
"""

import csv
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

# --- Configuration for the tracked sailing -----------------------------

SEARCH_URL = (
    "https://www.royalcaribbean.com/cruises"
    "?search=departurePort:GAL|startDate:2027-02-01~2027-02-28"
    "&itineraryPanel=LB05GAL-2956042566"
    "&country=USA&hp_search_widget=home"
)

ITINERARY_ID = "LB05GAL-2956042566"
SHIP_NAME = "Liberty of the Seas"
CRUISE_NAME = "Western Caribbean Cruise"
NIGHTS = 5
SAIL_START = "2027-02-01"
SAIL_END = "2027-02-06"

# Regexes used to find the right date button among the "Available dates" list.
# Royal Caribbean renders labels like "Feb 1 - Feb 6" (may use a hyphen or
# an en dash). Adjust here if the sail date changes.
DATE_LABEL_PATTERNS = [
    re.compile(r"Feb\s*1\s*[-–]\s*Feb\s*6", re.IGNORECASE),
]

PRICE_PATTERN = re.compile(r"\$\s?[\d,]+")

OUTPUT_CSV = Path(__file__).resolve().parent.parent / "price_history.csv"
DEBUG_DIR = Path(__file__).resolve().parent.parent / "debug"

CSV_HEADER = [
    "timestamp_utc",
    "ship",
    "cruise_name",
    "itinerary_id",
    "nights",
    "sail_start",
    "sail_end",
    "price_usd",
]


def find_price(page) -> int:
    """Return the lowest price (as an int, USD) for the target sail date button."""

    # Wait for the itinerary flyout panel to render.
    page.wait_for_selector(f"text={CRUISE_NAME}", timeout=45000)

    # The date-selector buttons live under an "Available dates" section.
    # Search the whole panel's text nodes for a container that has both the
    # target date label and a dollar amount, walking up from the date label
    # until a $-containing ancestor is found.
    result = page.evaluate(
        """
        (labelPatterns) => {
            const patterns = labelPatterns.map(p => new RegExp(p, 'i'));
            const priceRe = /\\$\\s?[\\d,]+/;

            const all = Array.from(document.querySelectorAll('body *'));
            for (const el of all) {
                const ownText = el.textContent || '';
                if (!patterns.some(p => p.test(ownText))) continue;

                // Walk up looking for the smallest ancestor that also has a price.
                let node = el;
                for (let i = 0; i < 6 && node; i++) {
                    const text = node.textContent || '';
                    const m = text.match(priceRe);
                    if (m) {
                        return { text, price: m[0] };
                    }
                    node = node.parentElement;
                }
            }
            return null;
        }
        """,
        [p.pattern for p in DATE_LABEL_PATTERNS],
    )

    if not result:
        raise RuntimeError(
            "Could not find a date button matching the target sail dates with a price nearby."
        )

    match = PRICE_PATTERN.search(result["price"])
    if not match:
        raise RuntimeError(f"Found a candidate element but no price in it: {result!r}")

    price_str = match.group(0).replace("$", "").replace(",", "").strip()
    return int(price_str)


def save_debug_artifacts(page) -> None:
    DEBUG_DIR.mkdir(exist_ok=True)
    try:
        page.screenshot(path=str(DEBUG_DIR / "failure.png"), full_page=True)
    except Exception:
        pass
    try:
        (DEBUG_DIR / "failure.html").write_text(page.content(), encoding="utf-8")
    except Exception:
        pass


def append_row(price: int) -> None:
    is_new = not OUTPUT_CSV.exists()
    with OUTPUT_CSV.open("a", newline="") as f:
        writer = csv.writer(f)
        if is_new:
            writer.writerow(CSV_HEADER)
        writer.writerow(
            [
                datetime.now(timezone.utc).isoformat(timespec="seconds"),
                SHIP_NAME,
                CRUISE_NAME,
                ITINERARY_ID,
                NIGHTS,
                SAIL_START,
                SAIL_END,
                price,
            ]
        )


def launch_browser(p):
    """Prefer the machine's real installed Edge/Chrome over Playwright's bundled
    Chromium, and run visibly (not headless). Royal Caribbean's bot detection
    fingerprints headless/bundled-Chromium sessions and serves a fake "site
    down" page to them even from a normal residential IP."""

    launch_args = ["--disable-blink-features=AutomationControlled", "--start-maximized"]
    for channel in ("msedge", "chrome"):
        try:
            return p.chromium.launch(channel=channel, headless=False, args=launch_args)
        except Exception:
            continue
    return p.chromium.launch(headless=False, args=launch_args)


def main() -> int:
    with sync_playwright() as p:
        browser = launch_browser(p)
        context = browser.new_context(
            viewport=None,
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0"
            ),
        )
        context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
        )
        page = context.new_page()
        try:
            # "networkidle" is unreliable on a real browser: background chatter
            # (telemetry, extensions, etc.) can mean the network never truly
            # goes quiet. Wait only for the initial HTML instead, then let
            # find_price() wait for the actual content to render.
            page.goto(SEARCH_URL, wait_until="domcontentloaded", timeout=45000)
            price = find_price(page)
        except Exception as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            save_debug_artifacts(page)
            browser.close()
            return 1

        browser.close()

    append_row(price)
    print(f"Recorded price ${price} for {SHIP_NAME} sailing {SAIL_START} -> {SAIL_END}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
