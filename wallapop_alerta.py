import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import requests
import time
import json
import os

with open('data.json', 'r') as file:
    data = json.load(file)

# Replace this with actual Telegram bot token and chat ID before running
TELEGRAM_TOKEN = data["telegram_token"]
TELEGRAM_CHAT_ID = data["telegram_chat_id"]
# Here a user can add multiple products to search for
CONFIGURATIONS = data["configurations"]

TIME = data["time"]

LAST_SEEN = set()

# Function to send messages via Telegram


def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    params = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    requests.get(url, params=params)

# Function to search Wallapop using the defined keywords and price range


async def search_wallapop(config, page):
    KEYWORDS = config["keywords"]
    PRICE_MIN = config["min"]
    PRICE_MAX = config["max"]

    url = (
        f"https://es.wallapop.com/search?"
        f"keywords={KEYWORDS.replace(' ', '%20')}"
        f"&priceMax={PRICE_MAX}"
        f"&order_by=newest"
    )

    await page.goto(url)

    # Try to accept cookie banner if it appears
    try:
        accept_cookies_btn = await page.wait_for_selector('#onetrust-accept-btn-handler', timeout=5000)
        if accept_cookies_btn:
            await accept_cookies_btn.click()
            await asyncio.sleep(1)
    except PlaywrightTimeoutError:
        pass  # No cookie banner appeared

    # Scroll and wait for products to load
    max_scroll_time = 20
    scroll_interval = 1
    start_time = time.time()

    products = []
    while time.time() - start_time < max_scroll_time:
        products = await page.query_selector_all('a.item-card_ItemCard--vertical__CNrfk')
        if products:
            break
        await page.evaluate("window.scrollBy(0, window.innerHeight);")
        await asyncio.sleep(scroll_interval)

    if not products:
        print(f"[{KEYWORDS}] No products found.")
        return

    new_found = 0
    messages = []

    # Process each found product
    for prod in products:
        title_el = await prod.query_selector("h3")
        price_el = await prod.query_selector('strong[aria-label="Item price"]')
        link = await prod.get_attribute("href")

        if not title_el or not price_el or not link:
            continue

        title = await title_el.inner_text()
        price_text = await price_el.inner_text()
        price_num_str = ''.join(filter(str.isdigit, price_text))
        if not price_num_str:
            continue

        price_num = int(price_num_str)

        # Check if price is within range and if product is not already seen
        if PRICE_MIN <= price_num <= PRICE_MAX and link not in LAST_SEEN:
            LAST_SEEN.add(link)
            message = f"{title}\n{price_num} €\nhttps://es.wallapop.com{link}"
            messages.append(message)
            new_found += 1

    # If new products found, send a header and then the results
    if new_found > 0:
        header = f"...................\n\n📦 Results for: {KEYWORDS}\n\n..................."
        send_telegram_message(header)
        for message in messages:
            send_telegram_message(message)

    print(f"[{KEYWORDS}] {new_found} new products encountered.")

# Main loop that runs the search periodically


async def main_loop():
    async with async_playwright() as p:
        # Run in headless mode
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        while True:
            try:
                print("\nStarting search cycle...")
                for config in CONFIGURATIONS:
                    await search_wallapop(config, page)
                    await asyncio.sleep(2)  # Short pause between searches
            except Exception as e:
                print(f"Error during search: {e}")

            print(f"\nWaiting {TIME} minutes before the next search...\n")
            # Wait 10 minutes before the next cycle
            await asyncio.sleep(TIME * 60)

# Run the script
if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        print("\n Program manually detained with Ctrl + C.")
