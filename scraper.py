import datetime
import time
from playwright.sync_api import sync_playwright
from feedgen.feed import FeedGenerator

URL = "https://finance.yahoo.com/quote/UWMC/press-releases/"
OUTPUT_FILE = "rss.xml"

def scrape_uwmc_stream():
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)
        # Using a standard desktop user agent to avoid bot detection
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        print(f"Navigating to {URL}...")
        try:
            # CHANGE: wait_until="domcontentloaded" is much faster/reliable than "networkidle"
            page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            print(f"Initial navigation timed out, but proceeding to check for content: {e}")

        # 1. Handle Cookie Consent (Crucial on Yahoo)
        # We try to click "Accept all" or "Agree" if it blocks the view
        try:
            consent_selectors = ['button[name="agree"]', 'button:has-text("Accept all")', '.accept-all']
            for selector in consent_selectors:
                if page.locator(selector).is_visible(timeout=3000):
                    page.click(selector)
                    print("Handled cookie consent.")
                    break
        except:
            pass

        # 2. Wait for the specific list items you identified
        print("Waiting for story items to appear...")
        try:
            # We wait for the first story-item to appear on the page
            page.wait_for_selector("li.story-item", timeout=20000)
        except Exception as e:
            print(f"Warning: Could not find story items. Stream might be empty or layout changed. {e}")
            browser.close()
            return

        # 3. Targeted extraction based on your markup
        # We specifically target li.story-item to automatically skip li.ad-item
        stories = page.locator("li.story-item").all()
        print(f"Found {len(stories)} stories.")

        fg = FeedGenerator()
        fg.id(URL)
        fg.title('UWMC Press Releases (Yahoo Stream)')
        fg.link(href=URL, rel='alternate')
        fg.description('Live RSS feed of UWMC news items.')
        fg.language('en')

        count = 0
        for story in stories:
            if count >= 15: break # Increased to 15 to ensure a full feed
            
            # Find the main link/headline inside the story item
            link_el = story.locator("a.subtle-link, a.link").first 
            # If the class varies, we can fall back to the first <a> with text
            if link_el.count() == 0:
                link_el = story.locator("a").first

            if link_el.count() > 0:
                title = link_el.inner_text().strip()
                href = link_el.get_attribute("href")
                
                if not title or not href or href.startswith("#"): continue
                
                full_url = f"https://finance.yahoo.com{href}" if href.startswith("/") else href

                fe = fg.add_entry()
                fe.id(full_url)
                fe.title(title)
                fe.link(href=full_url)
                # Note: Exact timestamps are hard to parse from '2 hours ago', 
                # so we use the current fetch time as the pubDate.
                fe.pubDate(datetime.datetime.now(datetime.timezone.utc))
                
                print(f"Scraped: {title[:60]}...")
                count += 1

        fg.rss_file(OUTPUT_FILE)
        print(f"Done! Saved {count} items to {OUTPUT_FILE}.")
        browser.close()

if __name__ == "__main__":
    scrape_uwmc_stream()
