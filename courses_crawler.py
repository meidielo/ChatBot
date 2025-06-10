import requests
from bs4 import BeautifulSoup
import json
import time
from urllib.parse import urljoin

BASE_URL = "https://www.rmit.edu.au"
START_URL = "https://www.rmit.edu.au/study-with-us/levels-of-study/undergraduate-study/bachelor-degrees"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

visited = set()
courses_data = []


def clean_text(text):
    return ' '.join(text.strip().split())


def parse_course_plan(url):
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        course_entries = []
        rows = soup.select("table tr")
        for row in rows[1:]:  # skip header
            cols = row.find_all("td")
            if len(cols) >= 4:
                title = clean_text(cols[0].get_text())
                credit = clean_text(cols[1].get_text())
                code = clean_text(cols[2].get_text())
                campus = clean_text(cols[3].get_text())
                if code:
                    course_entries.append({
                        "course_code": code,
                        "title": title,
                        "credit_points": credit,
                        "campus": campus
                    })
        return course_entries

    except Exception as e:
        print(f"Failed to parse course plan at {url}: {e}")
        return []


def crawl_programs():
    try:
        res = requests.get(START_URL, headers=HEADERS)
        soup = BeautifulSoup(res.text, "html.parser")
        program_links = soup.select("a[href*='bachelor-degrees']")

        for link in program_links:
            title = clean_text(link.get_text())
            href = link.get("href")
            if not href:
                continue

            program_url = urljoin(BASE_URL, href)
            if program_url in visited or not program_url.startswith(BASE_URL):
                continue

            visited.add(program_url)
            print(f"Visiting plan page: {program_url}")

            # Visit the program page to find deep plan links
            try:
                sub_res = requests.get(program_url, headers=HEADERS, timeout=10)
                sub_soup = BeautifulSoup(sub_res.text, "html.parser")
                plan_links = sub_soup.select("a[href*='bp'][href*='auscy']")

                for plan_link in plan_links:
                    plan_url = urljoin(BASE_URL, plan_link.get("href"))
                    program_title = clean_text(sub_soup.select_one("h1").get_text() if sub_soup.select_one("h1") else title)
                    course_list = parse_course_plan(plan_url)
                    if course_list:
                        courses_data.append({
                            "program_title": program_title,
                            "url": program_url,
                            "course_details": course_list
                        })
            except Exception as e:
                print(f"Error processing {program_url}: {e}")

    except Exception as e:
        print(f"Initial crawl failed: {e}")


if __name__ == "__main__":
    crawl_programs()
    with open("rmit_bachelor_courses.json", "w", encoding="utf-8") as f:
        json.dump(courses_data, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(courses_data)} course entries to rmit_bachelor_courses.json")
