# data_crawler.py
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import sqlite3
import time
import json

BASE_URL = "https://www.rmit.edu.au/"

def init_db(db_path="rmit_data.db"):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pages (
            url TEXT PRIMARY KEY,
            content TEXT
        )
    """)
    conn.commit()
    return conn, cur

def crawl_page(url, cur, conn, visited, depth=0, max_depth=2):
    if url in visited or depth > max_depth:
        return
    visited.add(url)

    try:
        resp = requests.get(url, timeout=5)
        soup = BeautifulSoup(resp.text, "html.parser")
        text = soup.get_text(separator="\n").strip()

        # Save to SQLite (overwrite if exists)
        cur.execute("REPLACE INTO pages (url, content) VALUES (?, ?)", (url, text))
        conn.commit()
        print(f"[Depth {depth}] Crawled and stored: {url}")

        # Follow internal links
        for link in soup.find_all("a", href=True):
            next_url = urljoin(url, link["href"])
            parsed = urlparse(next_url)
            # Only stay on the rmit.edu.au domain
            if parsed.netloc.endswith("rmit.edu.au"):
                crawl_page(next_url, cur, conn, visited, depth + 1, max_depth)

        # Pause between requests to be polite
        time.sleep(1)

    except Exception as e:
        print(f"Failed to crawl {url}: {e}")

def scrape_disciplines():
    url = "https://www.rmit.edu.au/study-with-us"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    area_tags = soup.select("a.link-block__link, a[href*='/study-with-us/']")
    disciplines = {}

    for tag in area_tags:
        title = tag.get_text(strip=True)
        if title:
            simplified_keywords = title.lower().replace("&", "and").replace("/", " ").split()
            disciplines[title] = list(set(simplified_keywords))

    with open("discipline_keywords.json", "w", encoding="utf-8") as f:
        json.dump(disciplines, f, indent=2)
    print("✅ Scraped and saved discipline keywords.")

if __name__ == "__main__":
    conn, cur = init_db()
    visited_urls = set()
    crawl_page(BASE_URL, cur, conn, visited_urls, depth=0, max_depth=2)
    conn.close()
    print("Crawling complete. Data saved to rmit_data.db.")
    scrape_disciplines()