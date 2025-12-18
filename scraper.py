import datetime
from playwright.sync_api import sync_playwright
from feedgen.feed import FeedGenerator

# Configuration
TARGET_URL = "https://finance.yahoo.com/quote/UWMC/press-releases/"
OUTPUT_FILE = "rss.xml"

def scrape_uwmc_stream():
    with sync_playwright() as p:
        # Launch browser in headless mode
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        print(f"Navigating to {TARGET_URL}...")
        # Use domcontentloaded for speed and reliability on heavy sites
        page.goto(TARGET_URL, wait_until="domcontentloaded")

        # Bypass potential Yahoo cookie consent overlay
        try:
            page.click('button[name="agree"]', timeout=5000)
            print("Handled cookie consent.")
        except:
            pass

        # Wait for the stream container you identified
        print("Waiting for story items to load...")
        try:
            page.wait_for_selector("li.story-item", timeout=15000)
        except Exception:
            print("Timeout waiting for story items. The page layout might have shifted.")
            browser.close()
            return

        # Select all story items (this excludes 'ad-item' elements automatically)
        stories = page.locator("li.story-item").all()
        print(f"Found {len(stories)} stories.")

        # Initialize Feed Generator
        fg = FeedGenerator()
        fg.id(TARGET_URL)
        fg.title('UWMC Press Releases (Yahoo Finance)')
        fg.link(href=TARGET_URL, rel='alternate')
        fg.description(f'Latest UWMC news items updated on {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}')
        fg.language('en')

        # To keep the newest stories at the top of the RSS feed:
        # 1. Reverse the list so we process the oldest visible stories first.
        # 2. Use order='prepend' so each new story is pushed to the top of the XML.
        count = 0
        for story in reversed(stories):
            if count >= 20: break # Grab up to 20 stories
            
            # Target the headline link (usually inside an h3 or a main link class)
            headline_el = story.locator("h3 a, a.subtle-link, a.link").first
            
            # Fallback if the first link is an image or empty
            if headline_el.count() == 0 or len(headline_el.inner_text().strip()) < 5:
                # Scan all links in the item for one with significant text
                all_links = story.locator("a").all()
                for link in all_links:
                    if len(link.inner_text().strip()) > 10:
                        headline_el = link
                        break

            if headline_el.count() > 0:
                title = headline_el.inner_text().strip()
                href = headline_el.get_attribute("href")
                
                if not title or not href or href.startswith("#"):
                    continue

                # Clean up the URL
                full_url = href
                if href.startswith("/"):
                    full_url = f"https://finance.yahoo.com{href}"

                # Add to feed (prepending puts the most recent at the top)
                fe = fg.add_entry(order='prepend')
                fe.id(full_url)
                fe.title(title)
                fe.link(href=full_url)
                # Since precise timestamps aren't in the markup, we use the fetch time
                fe.pubDate(datetime.datetime.now(datetime.timezone.utc))
                
                count += 1
                print(f"Scraped ({count}): {title[:50]}...")

        # Save the file
        fg.rss_file(OUTPUT_FILE)
        print(f"Successfully generated {OUTPUT_FILE} with {count} items.")
        browser.close()

if __name__ == "__main__":
    scrape_uwmc_stream()
