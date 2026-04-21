# backend/org_services/crawler.py
# Synchronous crawler using requests + BeautifulSoup

import hashlib
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

import requests
from bs4 import BeautifulSoup
from sqlmodel import Session, select

from database import get_session
from models.crawl_config import CrawlConfig
from org_services.helper_client import HelperClient

logger = logging.getLogger(__name__)

# Global crawl state (set by run_crawl)
_crawl_running = False
_crawl_stop_requested = False
_crawl_progress = {}


def _compute_hash(title: str, content: str) -> str:
    return hashlib.md5(f"{title}|{content}".encode()).hexdigest()


def _fetch(url: str, timeout: float = 15.0) -> Optional[str]:
    """Fetch URL, return HTML text or None on failure."""
    try:
        r = requests.get(url, headers={
            "User-Agent": "Mozilla/5.0 (compatible; BIPTInfoOrganizer/1.0)"
        }, timeout=timeout)
        r.raise_for_status()
        return r.text
    except Exception as e:
        logger.warning(f"Failed to fetch {url}: {e}")
        return None


def _parse_article_links(html: str, article_selector: str, link_prefix: str) -> list[str]:
    """Extract article links from list page HTML."""
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for a in soup.select(article_selector):
        href = a.get("href", "")
        if not href:
            continue
        if link_prefix and not href.startswith(link_prefix) and not href.startswith("http"):
            href = link_prefix.rstrip("/") + "/" + href.lstrip("/")
        if href.startswith("http"):
            links.append(href)
        else:
            links.append(href)
    return links


def _extract_content(html: str, selector: str) -> tuple[str, str]:
    """Extract title and content from article page."""
    soup = BeautifulSoup(html, "html.parser")

    title = ""
    # Try <title> first, then h1, then the selected element's text
    title_el = soup.find("title")
    if title_el:
        title = title_el.get_text(strip=True)
    h1 = soup.find("h1")
    if h1:
        title = h1.get_text(strip=True) or title

    # Extract main content
    content_parts = []
    if selector and selector != "body":
        elements = soup.select(selector)
    else:
        elements = [soup.body] if soup.body else [soup]

    for el in elements:
        text = el.get_text(separator="\n", strip=True)
        if text:
            content_parts.append(text)

    content = "\n\n".join(content_parts)
    # Truncate very long content to avoid huge documents
    if len(content) > 50000:
        content = content[:50000] + "\n\n[内容已截断]"
    return title, content


def _crawl_single_config(
    config: CrawlConfig,
    helper: HelperClient,
    crawl_progress: dict,
    session: Session,
) -> dict:
    """Crawl one config, return stats dict."""
    stats = {
        "found": 0,
        "pushed": 0,
        "skipped": 0,
        "errors": 0,
    }
    config_id = config.id

    crawl_progress[config_id] = {
        "name": config.name,
        "status": "crawling",
        "found": 0,
        "pushed": 0,
        "errors": 0,
    }

    try:
        if config.is_list_page:
            # Crawl list page(s) first
            page_urls = [config.url]
            pagination_max = config.pagination_max or 0

            # Build pagination URLs if pagination selector exists
            if config.pagination_selector and pagination_max > 0:
                page_urls = _build_pagination_urls(config.url, pagination_max, config.pagination_selector, config.link_prefix)

            all_article_links = []
            for page_url in page_urls:
                if _crawl_stop_requested:
                    break
                html = _fetch(page_url)
                if not html:
                    stats["errors"] += 1
                    continue
                links = _parse_article_links(html, config.article_selector or "a", config.link_prefix or "")
                all_article_links.extend(links)
                stats["found"] += len(links)

            # Deduplicate
            all_article_links = list(dict.fromkeys(all_article_links))
            crawl_progress[config_id]["found"] = stats["found"]

            # Crawl each article
            for i, article_url in enumerate(all_article_links):
                if _crawl_stop_requested:
                    break
                crawl_progress[config_id]["current"] = i + 1
                crawl_progress[config_id]["total"] = len(all_article_links)

                article_html = _fetch(article_url)
                if not article_html:
                    stats["errors"] += 1
                    continue

                title, content = _extract_content(article_html, config.selector or "body")
                if not title and not content:
                    stats["errors"] += 1
                    continue

                doc_hash = _compute_hash(title, content)

                # Skip if same hash as last crawl (unless first time)
                if config.last_hash and config.last_hash == doc_hash:
                    stats["skipped"] += 1
                    continue

                # Push to bipthelper
                try:
                    helper.ingest_document({
                        "id": str(uuid.uuid4()),
                        "title": title,
                        "url": article_url,
                        "content": content,
                        "category": config.category or "",
                        "parent_category": config.parent_category or "",
                        "sub_category": config.sub_category or "",
                        "ai_status": "pending",
                    })
                    stats["pushed"] += 1
                except Exception as e:
                    logger.warning(f"Failed to push document {article_url}: {e}")
                    stats["errors"] += 1

                time.sleep(0.5)  # Be polite

        else:
            # Direct article page
            html = _fetch(config.url)
            if html:
                title, content = _extract_content(html, config.selector or "body")
                if title or content:
                    doc_hash = _compute_hash(title, content)
                    if not config.last_hash or config.last_hash != doc_hash:
                        try:
                            helper.ingest_document({
                                "id": str(uuid.uuid4()),
                                "title": title,
                                "url": config.url,
                                "content": content,
                                "category": config.category or "",
                                "parent_category": config.parent_category or "",
                                "sub_category": config.sub_category or "",
                                "ai_status": "pending",
                            })
                            stats["pushed"] += 1
                        except Exception as e:
                            logger.warning(f"Failed to push document: {e}")
                            stats["errors"] += 1
                    else:
                        stats["skipped"] += 1
                else:
                    stats["errors"] += 1
            else:
                stats["errors"] += 1

    except Exception as e:
        logger.error(f"Error crawling config {config_id}: {e}")
        stats["errors"] += 1

    # Update config last_crawl and hash
    config.last_crawl = datetime.now(timezone.utc).isoformat()
    config.last_hash = _compute_hash(str(stats["pushed"]), str(stats.get("found", 0)))
    config.initialized = True
    session.add(config)
    session.commit()

    crawl_progress[config_id] = {
        "name": config.name,
        "status": "done",
        "found": stats["found"],
        "pushed": stats["pushed"],
        "skipped": stats["skipped"],
        "errors": stats["errors"],
    }
    return stats


def _build_pagination_urls(base_url: str, max_pages: int, pagination_selector: str, link_prefix: str) -> list[str]:
    """Build list of pagination page URLs by following next-page links."""
    urls = [base_url]
    html = _fetch(base_url)
    if not html:
        return urls

    for _ in range(max_pages - 1):
        if _crawl_stop_requested:
            break
        soup = BeautifulSoup(html, "html.parser")
        next_link = soup.select_one(pagination_selector)
        if not next_link:
            break
        href = next_link.get("href", "")
        if not href:
            break
        if href.startswith("http"):
            next_url = href
        elif href.startswith("/"):
            from urllib.parse import urlparse
            parsed = urlparse(base_url)
            next_url = f"{parsed.scheme}://{parsed.netloc}{href}"
        else:
            next_url = base_url.rstrip("/") + "/" + href.lstrip("/")
        urls.append(next_url)
        html = _fetch(next_url)
        if not html:
            break
    return urls


def run_crawl(config_ids: Optional[str] = None):
    """Main crawl entry point — runs in background thread."""
    global _crawl_running, _crawl_stop_requested, _crawl_progress

    _crawl_running = True
    _crawl_stop_requested = False
    _crawl_progress = {}

    helper = HelperClient()

    try:
        with Session(_get_engine()) as session:
            query = select(CrawlConfig).where(CrawlConfig.enabled == True)
            if config_ids:
                id_list = [cid.strip() for cid in config_ids.split(",") if cid.strip()]
                query = query.where(CrawlConfig.id.in_(id_list))

            configs = session.exec(query).all()

            total_stats = {"found": 0, "pushed": 0, "skipped": 0, "errors": 0}
            for config in configs:
                if _crawl_stop_requested:
                    break
                stats = _crawl_single_config(config, helper, _crawl_progress, session)
                for k in total_stats:
                    total_stats[k] += stats[k]

            _crawl_progress["_total"] = total_stats
            _crawl_progress["_done"] = True

    finally:
        _crawl_running = False


def _get_engine():
    """Import here to avoid circular imports and use correct sys.path."""
    from database import _engine
    return _engine


def stop_crawl():
    global _crawl_stop_requested
    _crawl_stop_requested = True


def get_crawl_progress():
    return _crawl_progress


def is_crawl_running():
    return _crawl_running
