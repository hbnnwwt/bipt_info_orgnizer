import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))  # backend/ parent

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from pydantic import BaseModel
from sqlmodel import Session, select, func

from database import get_session
from services.helper_client import HelperClient

router = APIRouter()
_helper = None

def get_helper():
    global _helper
    if _helper is None:
        _helper = HelperClient()
    return _helper


class BulkDeleteRequest(BaseModel):
    ids: list[str]


@router.get("/documents/categories")
def get_categories():
    client = get_helper()
    resp = client.get_categories()
    return resp


@router.get("/documents")
def list_documents(
    page: int = 1,
    page_size: int = 20,
    category: Optional[str] = None,
    parent_category: Optional[str] = None,
    keyword: Optional[str] = None,
    ai_status: Optional[str] = None,
    sort: str = "updated_desc",
):
    client = get_helper()
    params = {"page": page, "page_size": page_size, "sort": sort}
    if category:
        params["category"] = category
    if parent_category:
        params["parent_category"] = parent_category
    if keyword:
        params["keyword"] = keyword
    if ai_status:
        params["ai_status"] = ai_status
    resp = client.get_documents(params)
    return resp


@router.delete("/documents/{doc_id}")
def delete_document(doc_id: str):
    client = get_helper()
    resp = client.delete_document(doc_id)
    return resp


@router.post("/documents/batch-delete")
def batch_delete_documents(req: BulkDeleteRequest = None):
    client = get_helper()
    deleted = 0
    for doc_id in (req.ids if req else []):
        try:
            client.delete_document(doc_id)
            deleted += 1
        except Exception:
            pass
    return {"deleted": deleted}


@router.put("/documents/{doc_id}/category")
def update_category(
    doc_id: str,
    category: str,
    current_admin=None,  # auth handled at proxy level
):
    client = get_helper()
    resp = client.update_document(doc_id, {"category": category})
    return resp


@router.post("/documents/{doc_id}/approve")
def approve_document(
    doc_id: str,
    categories: Optional[str] = None,
):
    client = get_helper()
    resp = client.approve_document(doc_id, categories)
    return resp


@router.get("/audit")
def list_audit_logs(
    page: int = 1,
    page_size: int = 50,
    action: Optional[str] = None,
    session: Session = Depends(get_session),
):
    from models.audit_log import AuditLog as AL
    count_query = select(func.count()).select_from(AL)
    if action:
        count_query = count_query.where(AL.action == action)
    total = session.exec(count_query).one()

    query = select(AL)
    if action:
        query = query.where(AL.action == action)
    query = query.order_by(AL.created_at.desc())
    logs = session.exec(query.offset((page - 1) * page_size).limit(page_size)).all()

    return {
        "logs": [
            {
                "id": log.id,
                "username": log.username,
                "action": log.action,
                "target": log.target or "",
                "detail": log.detail or "",
                "created_at": log.created_at,
            }
            for log in logs
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }