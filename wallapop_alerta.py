import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import requests
import time

# Replace this with actual Telegram bot token and chat ID before running
TELEGRAM_TOKEN = "TELEGRAM_TOKEN"
TELEGRAM_CHAT_ID = "TELEGRAM_CHAT_ID"

KEYWORDS = "steam deck oled"
PRICE_MIN = 100
PRICE_MAX = 350

TIME = 5 # Time between searches in minutes

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
async def search_wallapop(page):
    url = (
        f"https://es.wallapop.com/search?"
        f"keywords={KEYWORDS.replace(' ', '%20')}"
        f"&priceMax={PRICE_MAX}"
        f"&order_by=newest"
    )

    print(url)

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
        products = await page.query_selector_all('a.item-card_ItemCard--vertical__FiFz6')
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

# Main loop that runs the search periodically
async def main_loop():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)  # Run in headless mode
        page = await browser.new_page()

        while True:
            try:
                print("\nStarting search cycle...")
                await search_wallapop(page)
                await asyncio.sleep(2)  # Short pause between searches
            except Exception as e:
                print(f"Error during search: {e}")

            print(f"\nWaiting {TIME} minutes before the next search...\n")
            await asyncio.sleep(TIME * 60)  # Wait 10 minutes before the next cycle

# Run the script
if __name__ == "__main__":
    asyncio.run(main_loop())
