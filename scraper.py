import os
import datetime
from playwright.sync_api import sync_playwright
from feedgen.feed import FeedGenerator

URL = "https://www.uwm.com/press-releases"
OUTPUT_FILE = "rss.xml"

def scrape_uwm():
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Navigate and wait for the grid items to appear
        print(f"Loading {URL}...")
        page.goto(URL, wait_until="networkidle")
        
        # Wait specifically for the MUI Grid items (adjusting for the 10 item requirement)
        # We target the 'a' tags that likely lead to the full articles
        page.wait_for_selector(".MuiGrid-item", timeout=10000)
        
        # Grab the items
        items = page.locator(".MuiGrid-item").all()
        print(f"Found {len(items)} potential items.")

        fg = FeedGenerator()
        fg.id(URL)
        fg.title('UWM Press Releases')
        fg.link(href=URL, rel='alternate')
        fg.description('Latest press releases from UWM')
        fg.language('en')

        count = 0
        for item in items:
            if count >= 10: break # Limit to top 10
            
            # Extract Title and Link
            # MUI usually nests the text inside Typography/h tags and the link in an <a>
            link_element = item.locator("a").first
            title_element = item.locator("h2, h3, h4, p").first
            
            if link_element.count() > 0:
                title = title_element.inner_text().strip() if title_element.count() > 0 else "No Title"
                href = link_element.get_attribute("href")
                
                # Filter out navigation/footer links that might share the class
                if not href or "press-release" not in href.lower():
                    continue

                full_url = f"https://www.uwm.com{href}" if href.startswith("/") else href
                
                fe = fg.add_entry()
                fe.id(full_url)
                fe.title(title)
                fe.link(href=full_url)
                fe.pubDate(datetime.datetime.now(datetime.timezone.utc))
                count += 1
                print(f"Added: {title}")

        fg.rss_file(OUTPUT_FILE)
        browser.close()

if __name__ == "__main__":
    scrape_uwm()
