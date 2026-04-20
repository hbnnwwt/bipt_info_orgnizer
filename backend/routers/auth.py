# backend/routers/auth.py
# Self-contained auth: uses bipthelper's SQLite DB directly, no bipthelper services imported

import sys
import jwt
from datetime import datetime, timezone, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, Header
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from sqlmodel import Session, select

# Use bipthelper's database (same SQLite file)
sys.path.insert(0, "E:/code/bipthelper/backend")
from database import get_session
from config import get_settings

sys.path.insert(0, "E:/code/bipthelper/backend")
from models.user import User

router = APIRouter()

def verify_password(plain: str, hashed: str) -> bool:
    import hashlib
    if ":" in hashed:
        method, data = hashed.split(":", 1)
        if method == "sha256":
            return hashlib.sha256(plain.encode()).hexdigest() == data
    return False

def create_access_token(data: dict, expires_delta: timedelta = timedelta(days=7)):
    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


@router.post("/login")
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    """登录"""
    user = session.exec(select(User).where(User.username == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is inactive")

    token = create_access_token(data={"sub": user.username})
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    response = JSONResponse({
        "user": {"id": user.id, "username": user.username, "role": user.role},
        "token": token,
        "points": user.points,
        "last_checkin_date": user.last_checkin_date,
        "checked_in_today": user.last_checkin_date == today,
    })
    response.set_cookie(key="access_token", value=token, httponly=True, max_age=7*24*60*60, samesite="lax")
    return response


@router.get("/me")
def get_me(
    authorization: str = Header(None),
    session: Session = Depends(get_session),
):
    """从 Authorization: Bearer <token> 获取当前用户"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        settings = get_settings()
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username = payload.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = session.exec(select(User).where(User.username == username)).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return {"id": user.id, "username": user.username, "role": user.role, "points": user.points}


@router.post("/logout")
def logout():
    response = JSONResponse({"message": "ok"})
    response.delete_cookie("access_token")
    return response


def get_current_admin(
    authorization: str = Header(None),
    session: Session = Depends(get_session),
) -> User:
    """Admin 权限检查"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        settings = get_settings()
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username = payload.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = session.exec(select(User).where(User.username == username)).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user