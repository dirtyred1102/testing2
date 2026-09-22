# testing2
testing random 2

# Cruise price tracker

Tracks the price of one specific Royal Caribbean sailing over time, and can
send a push notification to your phone when the price drops.

- **Ship:** Liberty of the Seas
- **Itinerary:** 5-night Western Caribbean Cruise, roundtrip from Galveston, TX
- **Sail date:** Saturday, Feb 1 - Friday, Feb 6, 2027
- **Itinerary ID:** `LB05GAL-2956042566`

## How it works

`scripts/track_price.py` uses Playwright to open a real (visible, non-headless)
Edge or Chrome browser, navigate to the Royal Caribbean search page for this
itinerary, and read the price shown on the Feb 1-6, 2027 date button. Each run
appends a row (timestamp, ship, itinerary, price) to `price_history.csv`, and
if the price dropped since the last run, sends a phone notification.

Royal Caribbean's bot detection blocks/serves fake pages to traffic from
cloud datacenter IPs (confirmed on GitHub Actions) and to headless/bundled
Chromium sessions, even from a normal residential IP. This only works
reliably from a real computer on a home internet connection, using a real
installed browser - see "Running locally on Windows" below.

## Changing the tracked cruise

Edit the constants at the top of `scripts/track_price.py`:

- `SEARCH_URL` — the full royalcaribbean.com search URL for the itinerary
- `DATE_LABEL_PATTERNS` — regex(es) matching the date button's label
  (e.g. `Feb 1 - Feb 6`)
- `SHIP_NAME`, `CRUISE_NAME`, `ITINERARY_ID`, `NIGHTS`, `SAIL_START`, `SAIL_END`

Royal Caribbean may also change their page markup over time, which would
require updating `find_price()`.

## Running locally on Windows

1. Install Python 3.12 from
   [python.org/downloads/release/python-3120](https://www.python.org/downloads/release/python-3120/)
   (newer Python versions don't yet have prebuilt installers for one of
   Playwright's dependencies on Windows). Check **"Add python.exe to PATH"**
   during install.
2. Download this repository: click the green **Code** button on the GitHub
   page -> **Download ZIP**, then extract it somewhere permanent, e.g.
   `C:\Users\<you>\CruiseTracker` (not a Downloads folder you might clean out).
3. Open Command Prompt (Start menu -> type `cmd`), then navigate into the
   folder:
   ```
   cd C:\Users\<you>\CruiseTracker
   ```
4. Install dependencies (one-time setup):
   ```
   py -3.12 -m pip install -r requirements.txt
   py -3.12 -m playwright install chromium
   ```
5. Test it manually:
   ```
   py -3.12 scripts\track_price.py
   ```
   A browser window will briefly open. Check that `price_history.csv` now has
   a new row with a real dollar price.
6. To automate it daily, use **Task Scheduler**:
   - Open Task Scheduler (Start menu -> type "Task Scheduler").
   - Click **Create Basic Task** (right panel).
   - Name it "Cruise price tracker", click Next.
   - Trigger: choose **Daily**, pick a time, click Next.
   - Action: choose **Start a program**, click Next.
   - Program/script: browse to `run_tracker.bat` inside the extracted folder.
   - Finish. Your computer needs to be on (or wake from sleep) at that time
     for it to run.

## Phone notifications on price drops

Uses [ntfy.sh](https://ntfy.sh), a free push-notification service that needs
no account or signup.

1. Install the **ntfy** app on your phone (search "ntfy" on the App Store or
   Google Play).
2. Open the app, tap **+** (subscribe to topic), and enter a topic name only
   you would know — e.g. `brady-cruise-price-8271`. Anyone who knows this
   exact name can see your notifications, so don't use something guessable.
3. Open `scripts/track_price.py` and set:
   ```python
   NTFY_TOPIC = "brady-cruise-price-8271"  # use your own topic name
   ```
4. Save the file and run it once (`py -3.12 scripts\track_price.py`) to
   confirm it still works. You'll only get a notification when the price on
   a run is lower than the price recorded on the previous run — so it won't
   notify every day, only on an actual drop. If the script itself breaks
   (e.g. Royal Caribbean changes their page), it also sends a notification
   saying so.
