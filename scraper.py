import datetime
from playwright.sync_api import sync_playwright
from feedgen.feed import FeedGenerator

URL = "https://finance.yahoo.com/quote/UWMC/press-releases/"
OUTPUT_FILE = "rss.xml"

def scrape_uwmc_stream():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        print(f"Navigating to {URL}...")
        page.goto(URL, wait_until="domcontentloaded")

        # Quick consent click if it exists
        try:
            page.click('button[name="agree"]', timeout=3000)
        except:
            pass

        # Wait for the list items you confirmed
        print("Waiting for story items...")
        page.wait_for_selector("li.story-item", timeout=15000)
        
        # Grab all the story items
        stories = page.locator("li.story-item").all()
        print(f"Found {len(stories)} stories.")

        fg = FeedGenerator()
        fg.id(URL)
        fg.title('UWMC Press Releases')
        fg.link(href=URL, rel='alternate')
        fg.description('Live UWMC News Stream')
        fg.language('en')

        count = 0
        for story in stories:
            if count >= 10: break
            
            # REVISION: Yahoo headlines are almost always in an <h3> or have a specific data-test attribute
            # We look for the first link inside an h3, or just the first link with substantial text
            headline_el = story.locator("h3 a, a").first
            
            if headline_el.count() > 0:
                title = headline_el.inner_text().strip()
                href = headline_el.get_attribute("href")
                
                # If the title is empty (common if it's just an image link), 
                # we look for any link inside this item that actually has text.
                if not title or len(title) < 5:
                    all_links = story.locator("a").all()
                    for link in all_links:
                        text = link.inner_text().strip()
                        if len(text) > 10:
                            title = text
                            href = link.get_attribute("href")
                            break

                if not title or not href or href.startswith("#"):
                    continue

                # Ensure valid URL
                full_url = href
                if href.startswith("/"):
                    full_url = f"https://finance.yahoo.com{href}"

                fe = fg.add_entry()
                fe.id(full_url)
                fe.title(title)
                fe.link(href=full_url)
                fe.pubDate(datetime.datetime.now(datetime.timezone.utc))
                
                print(f"✅ Added: {title[:60]}...")
                count += 1

        fg.rss_file(OUTPUT_FILE)
        print(f"Done! Generated {OUTPUT_FILE} with {count} items.")
        browser.close()

if __name__ == "__main__":
    scrape_uwmc_stream()
