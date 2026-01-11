import json, re, sys
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

FSA_NEWS_URL = "https://www.fsa.go.jp/news/index.html"

def to_reiwa_parts(yyyy_mm_dd: str):
    y, m, d = map(int, yyyy_mm_dd.split("-"))
    reiwa_year = y - 2018
    return reiwa_year, m, d

def fetch(date_ymd: str):
    ry, m, d = to_reiwa_parts(date_ymd)

    # 전각/반각 섞여도 잡히게 숫자만 뽑아서 매칭
    # 예: 令和８年１月９日 / 令和8年1月9日 / 공백 포함 다 OK
    date_pat = re.compile(rf"令和\s*{ry}\s*年\s*{m}\s*月\s*{d}\s*日")

    r = requests.get(FSA_NEWS_URL, headers={"User-Agent":"Mozilla/5.0"}, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # 1) 날짜 문자열이 포함된 'li'를 찾는다 (트리 구조 대응)
    date_li = None
    for li in soup.find_all("li"):
        text = li.get_text(" ", strip=True)
        # 전각 숫자 대비: 숫자만 비교하는 fallback
        # (정규식이 전각 숫자를 완벽히 커버 못할 때 대비)
        if date_pat.search(text):
            date_li = li
            break

    # fallback: 숫자만 추출해서 비교
    if not date_li:
        target_nums = f"{ry}{m}{d}"
        for li in soup.find_all("li"):
            text = li.get_text(" ", strip=True)
            if "令和" in text:
                nums = "".join(re.findall(r"\d+", text))
                if nums == target_nums:
                    date_li = li
                    break

    items = []
    if not date_li:
        return {"date": date_ymd, "items": items}

    # 2) 날짜 li 이후에 나오는 링크들을 "다음 날짜 li" 전까지 수집
    cur = date_li
    while True:
        cur = cur.find_next_sibling()
        if cur is None:
            break

        # 다음 날짜 블록이 나오면 중단
        cur_text = cur.get_text(" ", strip=True)
        if "令和" in cur_text and ("年" in cur_text and "月" in cur_text and "日" in cur_text):
            # 다음 날짜로 보이면 stop
            # (이게 너무 민감하면 나중에 더 정교화 가능)
            break

        for a in cur.find_all("a", href=True):
            title = a.get_text(" ", strip=True)
            url = urljoin(FSA_NEWS_URL, a["href"])
            # 중복 제거
            if title and url and all(x["url"] != url for x in items):
                items.append({"title_ja": title, "title_ko": "", "url": url})

    return {"date": date_ymd, "items": items}

if __name__ == "__main__":
    date_ymd = sys.argv[1]
    print(json.dumps(fetch(date_ymd), ensure_ascii=False, indent=2))
