import datetime
from playwright.sync_api import sync_playwright
from feedgen.feed import FeedGenerator

URL = "https://finance.yahoo.com/quote/UWMC/press-releases/"
OUTPUT_FILE = "rss.xml"

def scrape_uwmc_stream():
    with sync_playwright() as p:
        # Use a real User-Agent to prevent immediate blocking
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        print(f"Navigating to {URL}...")
        page.goto(URL, wait_until="networkidle")

        # 1. Handle Cookie Consent (if it appears)
        try:
            # Look for "Accept all" or "Agree" buttons
            page.click('button[name="agree"]', timeout=5000)
            print("Accepted cookie consent.")
        except:
            pass

        # 2. Wait for the stream list to load
        page.wait_for_selector("ul.stream-items", timeout=15000)
        
        # 3. Target stream items that are stories (skipping ads)
        # We look for li.stream-item that ALSO have the story-item class
        items = page.locator("li.stream-item.story-item").all()
        print(f"Found {len(items)} story items.")

        fg = FeedGenerator()
        fg.id(URL)
        fg.title('UWMC Press Releases (Yahoo Stream)')
        fg.link(href=URL, rel='alternate')
        fg.description('Live RSS feed of UWMC news items from the Yahoo Finance stream.')
        fg.language('en')

        count = 0
        for item in items:
            if count >= 10: break
            
            # Extract link and title from the first <a> tag
            link_el = item.locator("a").first
            if link_el.count() > 0:
                title = link_el.inner_text().strip()
                href = link_el.get_attribute("href")
                
                if not href or href.startswith("#"): continue
                full_url = f"https://finance.yahoo.com{href}" if href.startswith("/") else href

                fe = fg.add_entry()
                fe.id(full_url)
                fe.title(title)
                fe.link(href=full_url)
                fe.pubDate(datetime.datetime.now(datetime.timezone.utc))
                
                print(f"Scraped: {title[:50]}...")
                count += 1

        fg.rss_file(OUTPUT_FILE)
        print(f"Done! Saved {count} items to {OUTPUT_FILE}.")
        browser.close()

if __name__ == "__main__":
    scrape_uwmc_stream()
