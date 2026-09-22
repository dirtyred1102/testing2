# testing2
testing random 2

# Cruise price tracker

Tracks the price of one specific Royal Caribbean sailing over time:

- **Ship:** Liberty of the Seas
- **Itinerary:** 5-night Western Caribbean Cruise, roundtrip from Galveston, TX
- **Sail date:** Saturday, Feb 1 - Friday, Feb 6, 2027
- **Itinerary ID:** `LB05GAL-2956042566`

## How it works

`scripts/track_price.py` uses Playwright (headless Chromium) to open the
Royal Caribbean search results page for this itinerary, finds the date
button for the Feb 1-6, 2027 sailing, and reads the price shown on it. Each
run appends a row (timestamp, ship, itinerary, price) to `price_history.csv`.

A GitHub Actions workflow (`.github/workflows/track-cruise-price.yml`) runs
this script once a day and commits the updated CSV back to the repo. You can
also trigger it manually from the Actions tab ("Run workflow").

## Changing the tracked cruise

Edit the constants at the top of `scripts/track_price.py`:

- `SEARCH_URL` — the full royalcaribbean.com search URL for the itinerary
- `DATE_LABEL_PATTERNS` — regex(es) matching the date button's label
  (e.g. `Feb 1 - Feb 6`)
- `SHIP_NAME`, `CRUISE_NAME`, `ITINERARY_ID`, `NIGHTS`, `SAIL_START`, `SAIL_END`

## Known limitation

This was built and pushed from an environment whose network egress policy
blocks `royalcaribbean.com`, so the scraper's selectors could not be
verified against the live site before committing. **Run the workflow once
manually** (Actions tab -> "Track cruise price" -> "Run workflow") and check
that a row was appended to `price_history.csv` with a sane price. If it
fails, the workflow uploads a `debug-artifacts` zip (a screenshot and the
page HTML at the point of failure) to help fix the text patterns in
`find_price()`.

Royal Caribbean may also change their page markup or add bot-detection over
time, which would require updating the script.
