import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
import datetime

URL = "https://www.uwm.com/press-releases"
OUTPUT_FILE = "rss.xml"

def scrape_uwm():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    response = requests.get(URL, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find the press release items
    # Note: .MuiGrid-root is common; we look for the specific containers within the main section
    articles = soup.select('.MuiGrid-root.MuiGrid-item')

    fg = FeedGenerator()
    fg.id(URL)
    fg.title('UWM Press Releases')
    fg.link(href=URL, rel='alternate')
    fg.description('Latest press releases from UWM')
    fg.language('en')

    for article in articles:
        # Looking for titles and links inside the grid item
        link_tag = article.find('a')
        title_tag = article.find(['h2', 'h3', 'h4', 'p']) # MUI often uses different tags for headings
        
        if link_tag and title_tag:
            title = title_tag.get_text(strip=True)
            link = "https://www.uwm.com" + link_tag['href'] if link_tag['href'].startswith('/') else link_tag['href']
            
            fe = fg.add_entry()
            fe.id(link)
            fe.title(title)
            fe.link(href=link)
            # UWM releases usually have a date, you can try to parse it here if needed
            fe.pubDate(datetime.datetime.now(datetime.timezone.utc))

    fg.rss_file(OUTPUT_FILE)

if __name__ == "__main__":
    scrape_uwm()
