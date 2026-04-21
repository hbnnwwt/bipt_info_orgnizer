# backend/routers/crawl_admin.py
# Crawler config management + crawl status SSE

import asyncio
import json
import threading
import uuid
from datetime import datetime, timezone
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional
from sqlmodel import Session, select

from database import get_session
from models.crawl_config import CrawlConfig
from routers.auth import get_current_admin
from org_services.crawler import run_crawl, stop_crawl as stop_crawler, get_crawl_progress, is_crawl_running

router = APIRouter()


def _validate_selector(selector: str, field_name: str) -> bool:
    if not selector or not selector.strip():
        return True
    dangerous = ["<script", "javascript:", "onerror", "onclick", "onload", "onmouse", "onkey"]
    lower = selector.lower()
    for d in dangerous:
        if d in lower:
            raise HTTPException(status_code=400, detail=f"{field_name}: 选择器不能包含危险内容 '{d}'")
    return True


def _validate_url(url: str, field_name: str) -> bool:
    try:
        u = urlparse(url)
        if u.scheme not in ("http", "https", ""):
            raise HTTPException(status_code=400, detail=f"{field_name}: 仅支持 http/https URL")
        return True
    except Exception:
        raise HTTPException(status_code=400, detail=f"{field_name}: URL 格式无效")


def add_audit_log_local(user_id, username, action, target, detail, session):
    from models.audit_log import AuditLog
    log = AuditLog(
        id=str(uuid.uuid4()),
        user_id=user_id or "",
        username=username,
        action=action,
        target=target or "",
        detail=detail,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    session.add(log)
    session.commit()


# --- Crawl state managed by crawler.py ---
# crawl_running, crawl_stop_requested, crawl_progress live in org_services.crawler


@router.get("/configs")
def list_configs(
    current_admin=Depends(get_current_admin),
    session: Session = Depends(get_session),
):
    configs = session.exec(select(CrawlConfig)).all()
    return {
        "configs": [
            {
                "id": c.id,
                "name": c.name,
                "url": c.url,
                "selector": c.selector or "body",
                "category": c.category or "",
                "parent_category": c.parent_category or "",
                "sub_category": c.sub_category or "",
                "is_list_page": c.is_list_page,
                "article_selector": c.article_selector or "a",
                "link_prefix": c.link_prefix or "",
                "pagination_selector": c.pagination_selector or "",
                "pagination_max": c.pagination_max or 0,
                "enabled": c.enabled,
                "last_crawl": c.last_crawl or "",
                "initialized": c.initialized,
            }
            for c in configs
        ]
    }


@router.post("/configs")
def create_config(
    name: str,
    url: str,
    selector: str = "body",
    category: Optional[str] = None,
    is_list_page: bool = True,
    article_selector: str = "a",
    link_prefix: Optional[str] = None,
    pagination_selector: str = "",
    pagination_max: int = 0,
    parent_category: Optional[str] = None,
    sub_category: Optional[str] = None,
    auto_interval_hours: int = 0,
    current_admin=Depends(get_current_admin),
    session: Session = Depends(get_session),
):
    _validate_url(url, "列表页URL")
    _validate_selector(selector, "内容选择器")
    _validate_selector(article_selector, "文章链接选择器")
    if link_prefix:
        _validate_selector(link_prefix, "链接前缀")
    if pagination_selector:
        _validate_selector(pagination_selector, "分页选择器")

    config = CrawlConfig(
        id=str(uuid.uuid4()),
        name=name,
        url=url,
        selector=selector,
        category=category,
        parent_category=parent_category,
        sub_category=sub_category,
        is_list_page=is_list_page,
        article_selector=article_selector,
        link_prefix=link_prefix,
        pagination_selector=pagination_selector,
        pagination_max=pagination_max,
        auto_interval_hours=auto_interval_hours,
    )
    session.add(config)
    session.commit()
    add_audit_log_local(current_admin["id"], current_admin["username"], "add_config", config.id, f"添加配置: {config.name}", session)
    return {"id": config.id, "name": config.name, "url": config.url}


@router.put("/configs/{config_id}")
def update_config(
    config_id: str,
    name: Optional[str] = None,
    url: Optional[str] = None,
    selector: Optional[str] = None,
    category: Optional[str] = None,
    is_list_page: Optional[bool] = None,
    article_selector: Optional[str] = None,
    link_prefix: Optional[str] = None,
    pagination_selector: Optional[str] = None,
    pagination_max: Optional[int] = None,
    enabled: Optional[bool] = None,
    initialized: Optional[bool] = None,
    parent_category: Optional[str] = None,
    sub_category: Optional[str] = None,
    auto_interval_hours: Optional[int] = None,
    current_admin=Depends(get_current_admin),
    session: Session = Depends(get_session),
):
    config = session.get(CrawlConfig, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")

    if url is not None:
        _validate_url(url, "列表页URL")
    if selector is not None:
        _validate_selector(selector, "内容选择器")
    if article_selector is not None:
        _validate_selector(article_selector, "文章链接选择器")
    if link_prefix is not None:
        _validate_selector(link_prefix, "链接前缀")
    if pagination_selector is not None:
        _validate_selector(pagination_selector, "分页选择器")

    if name is not None:
        config.name = name
    if url is not None:
        config.url = url
    if selector is not None:
        config.selector = selector
    if category is not None:
        config.category = category
    if is_list_page is not None:
        config.is_list_page = is_list_page
    if article_selector is not None:
        config.article_selector = article_selector
    if link_prefix is not None:
        config.link_prefix = link_prefix
    if pagination_selector is not None:
        config.pagination_selector = pagination_selector
    if pagination_max is not None:
        config.pagination_max = pagination_max
    if enabled is not None:
        config.enabled = enabled
    if initialized is not None:
        config.initialized = initialized
    if parent_category is not None:
        config.parent_category = parent_category
    if sub_category is not None:
        config.sub_category = sub_category
    if auto_interval_hours is not None:
        config.auto_interval_hours = auto_interval_hours

    session.add(config)
    session.commit()
    return {"message": "Config updated"}


@router.delete("/configs/{config_id}")
def delete_config(
    config_id: str,
    current_admin=Depends(get_current_admin),
    session: Session = Depends(get_session),
):
    config = session.get(CrawlConfig, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    session.delete(config)
    session.commit()
    add_audit_log_local(current_admin["id"], current_admin["username"], "delete_config", config_id, f"删除配置: {config.name}", session)
    return {"message": "Config deleted"}


@router.get("/crawl/status")
def get_crawl_status():
    return {"running": is_crawl_running()}


@router.get("/crawl/progress")
async def get_crawl_progress():
    async def event_generator():
        while True:
            yield f"event: progress\ndata: {json.dumps(get_crawl_progress())}\n\n"
            await asyncio.sleep(2)
    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/crawl/start")
def start_crawl(
    config_ids: Optional[str] = None,
    current_admin=Depends(get_current_admin),
    session: Session = Depends(get_session),
):
    if is_crawl_running():
        raise HTTPException(status_code=400, detail="Crawl already running")
    add_audit_log_local(current_admin["id"], current_admin["username"], "trigger_crawl", None,
                        f"手动触发爬取 {'指定配置' if config_ids else '全部配置'}", session)
    threading.Thread(target=run_crawl, args=(config_ids,), daemon=True).start()
    return {"status": "started"}


@router.post("/crawl/stop")
def stop_crawl(
    current_admin=Depends(get_current_admin),
    session: Session = Depends(get_session),
):
    current_admin  # used
    stop_crawler()
    return {"message": "Stop requested"}
