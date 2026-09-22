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

Royal Caribbean's bot detection blocks traffic from cloud/datacenter IP
ranges (confirmed: GitHub Actions' runners consistently got served a static
"royalcaribbean.com is on vacation" fallback page instead of the real site).
Because of this, **the GitHub Actions workflow does not work** — this script
needs to run from a normal residential internet connection instead, e.g. a
scheduled task on your own computer. See "Running locally on Windows" below.

Royal Caribbean may also change their page markup over time, which would
require updating the text patterns in `find_price()`.

## Running locally on Windows

1. Install Python from [python.org/downloads](https://www.python.org/downloads/).
   During install, check the box that says **"Add python.exe to PATH"**.
2. Download this repository: on the GitHub page, click the green **Code**
   button -> **Download ZIP**, then extract it somewhere like
   `C:\Users\<you>\cruise-tracker`.
3. Open Command Prompt (Start menu -> type `cmd`), then navigate into the
   folder, e.g.:
   ```
   cd C:\Users\<you>\cruise-tracker
   ```
4. Install dependencies (one-time setup):
   ```
   pip install -r requirements.txt
   playwright install chromium
   ```
5. Test it manually:
   ```
   python scripts\track_price.py
   ```
   Check that `price_history.csv` now has a new row with a real dollar price.
6. To automate it daily, use **Task Scheduler**:
   - Open Task Scheduler (Start menu -> type "Task Scheduler").
   - Click **Create Basic Task** (right panel).
   - Name it "Cruise price tracker", click Next.
   - Trigger: choose **Daily**, pick a time, click Next.
   - Action: choose **Start a program**, click Next.
   - Program/script: browse to `run_tracker.bat` inside the extracted folder.
   - Finish. Your computer needs to be on (or wake from sleep) at that time
     for it to run.
