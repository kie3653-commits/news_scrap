import json, re, sys
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

FSA_NEWS_URL = "https://www.fsa.go.jp/news/index.html"

def to_reiwa_date(yyyy_mm_dd: str) -> str:
    y, m, d = map(int, yyyy_mm_dd.split("-"))
    reiwa_year = y - 2018
    return f"令和{reiwa_year}年{int(m)}月{int(d)}日"

def fetch(date_ymd: str):
    date_ja = to_reiwa_date(date_ymd)
    r = requests.get(FSA_NEWS_URL, headers={"User-Agent":"Mozilla/5.0"}, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    target = None
    for li in soup.find_all("li"):
        txt = li.get_text(" ", strip=True)
        if date_ja in txt and li.find(["ul","ol"]):
            target = li
            break

    items = []
    if target:
        sub = target.find(["ul","ol"])
        for a in sub.find_all("a", href=True):
            title = a.get_text(" ", strip=True)
            url = urljoin(FSA_NEWS_URL, a["href"])
            items.append({"title_ja": title, "title_ko": "", "url": url})

    return {"date": date_ymd, "items": items}

if __name__ == "__main__":
    date_ymd = sys.argv[1]  # YYYY-MM-DD
    print(json.dumps(fetch(date_ymd), ensure_ascii=False, indent=2))
