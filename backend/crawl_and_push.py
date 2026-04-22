"""Quick crawl script: fetch cafeteria menus + school notices, push to bipthelper."""

import hashlib
import time
import uuid
import sys
import os

import httpx
import requests
from bs4 import BeautifulSoup

BIPTHELPER_URL = os.environ.get("BIPTHELPER_URL", "http://localhost:8000")
ORGANIZER_KEY = os.environ.get("ORGANIZER_API_KEY", "a0e1a1ad56456186e97d1fe1bd10b649")

BASE_URL = "https://info.bipt.edu.cn"
ARTICLE_SELECTOR = ".sub_right li a"
CONTENT_SELECTOR = ".subArticleCon"

configs = [
    {
        "name": "教工食堂菜谱",
        "list_url": f"{BASE_URL}/fwxx/fwshfw/index.htm",
        "link_prefix": f"{BASE_URL}/fwxx/fwshfw/",
        "parent_category": "服务信息",
        "sub_category": "生活服务",
        "category": "教工食堂",
    },
    {
        "name": "学校通知公告",
        "list_url": f"{BASE_URL}/xxxx/xxtzgg/index.htm",
        "link_prefix": f"{BASE_URL}/xxxx/xxtzgg/",
        "parent_category": "学校信息",
        "sub_category": "通知公告",
        "category": "通知公告",
    },
]


def fetch(url: str) -> bytes | None:
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}, timeout=15)
        r.raise_for_status()
        return r.content
    except Exception as e:
        print(f"  [ERR] fetch {url}: {e}")
        return None


def resolve_url(href: str, link_prefix: str) -> str:
    from urllib.parse import urljoin
    if href.startswith("http"):
        return href
    if href.startswith("/"):
        return BASE_URL + href
    # Use urljoin to properly handle ../ relative paths
    return urljoin(link_prefix, href)


def parse_links(html: bytes, link_prefix: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser", from_encoding="utf-8")
    links = []
    for a in soup.select(ARTICLE_SELECTOR):
        href = a.get("href", "")
        if not href or href.startswith("javascript"):
            continue
        url = resolve_url(href, link_prefix)
        links.append(url)
    return list(dict.fromkeys(links))  # dedupe


def extract_content(html: bytes) -> tuple[str, str]:
    from urllib.parse import urljoin
    import PyPDF2
    import tempfile
    import os

    soup = BeautifulSoup(html, "html.parser", from_encoding="utf-8")
    title = ""
    h1 = soup.find("h1")
    if h1:
        title = h1.get_text(strip=True)
    if not title:
        t = soup.find("title")
        if t:
            title = t.get_text(strip=True)

    content_parts = []
    for el in soup.select(CONTENT_SELECTOR):
        text = el.get_text(separator="\n", strip=True)
        if text:
            content_parts.append(text)
    content = "\n\n".join(content_parts) if content_parts else ""

    # If no text content, check for embedded PDF
    if not content:
        iframe = soup.find("iframe")
        if iframe and iframe.get("data-src"):
            pdf_rel = iframe["data-src"]
            # Need a base_url from caller — we'll handle this below
            return title, f"__PDF__{pdf_rel}"

    return title, content


def fetch_pdf_text(page_url: str, pdf_rel_path: str) -> str:
    """Download PDF and extract text content."""
    from urllib.parse import urljoin
    import tempfile, os
    import PyPDF2 as _PyPDF2
    pdf_url = urljoin(page_url, pdf_rel_path)
    try:
        r = requests.get(pdf_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
        r.raise_for_status()
        tmp = os.path.join(tempfile.gettempdir(), "bipt_crawl.pdf")
        with open(tmp, "wb") as f:
            f.write(r.content)
        reader = _PyPDF2.PdfReader(tmp)
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text.strip())
        return "\n\n".join(pages)
    except Exception as e:
        print(f"  [ERR] PDF extract {pdf_url}: {e}")
        return ""


def push_document(client: httpx.Client, doc: dict):
    resp = client.post(f"{BIPTHELPER_URL}/api/documents", json=doc)
    resp.raise_for_status()
    return resp.json()


def main():
    pushed = 0
    errors = 0

    with httpx.Client(timeout=30, headers={"X-Organizer-Key": ORGANIZER_KEY}) as client:
        for cfg in configs:
            print(f"\n=== {cfg['name']} ===")
            print(f"Fetching list: {cfg['list_url']}")
            list_html = fetch(cfg["list_url"])
            if not list_html:
                print("  Failed to fetch list page!")
                errors += 1
                continue

            article_links = parse_links(list_html, cfg["link_prefix"])
            print(f"  Found {len(article_links)} articles")

            for i, url in enumerate(article_links):
                print(f"  [{i+1}/{len(article_links)}] {url}")
                article_html = fetch(url)
                if not article_html:
                    errors += 1
                    continue

                title, content = extract_content(article_html)
                # Handle PDF-embedded pages
                if content.startswith("__PDF__"):
                    pdf_rel = content[7:]
                    content = fetch_pdf_text(url, pdf_rel)
                if not title and not content:
                    print(f"    No content extracted")
                    errors += 1
                    continue

                doc = {
                    "id": str(uuid.uuid4()),
                    "title": title,
                    "url": url,
                    "content": content[:50000],
                    "category": cfg["category"],
                    "parent_category": cfg["parent_category"],
                    "sub_category": cfg["sub_category"],
                    "ai_status": "pending",
                }

                try:
                    result = push_document(client, doc)
                    print(f"    OK: {result.get('message', '')} - {title[:40]}")
                    pushed += 1
                except Exception as e:
                    print(f"    PUSH FAILED: {e}")
                    errors += 1

                time.sleep(0.5)

    print(f"\n=== Done: pushed={pushed}, errors={errors} ===")


if __name__ == "__main__":
    main()
