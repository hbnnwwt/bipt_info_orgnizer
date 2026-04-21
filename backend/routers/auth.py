# backend/routers/auth.py
# Auth: delegates to bipthelper API for user data (avoids sys.path conflicts)

import httpx
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse

from org_config import get_settings

router = APIRouter()


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    """Login via bipthelper - returns JWT token"""
    settings = get_settings()
    try:
        async with httpx.AsyncClient(base_url=settings.BIPTHELPER_URL, timeout=10.0) as client:
            response = await client.post(
                "/api/auth/login",
                data={
                    "username": form_data.username,
                    "password": form_data.password,
                },
            )
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="bipthelper service unavailable")

    if response.status_code == 401:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    if response.status_code == 403:
        raise HTTPException(status_code=403, detail="User account is inactive")
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Login failed")

    data = response.json()
    token = data["token"]
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    user = data["user"]

    response = JSONResponse({
        "user": {"id": user["id"], "username": user["username"], "role": user["role"]},
        "token": token,
        "points": data.get("points"),
        "last_checkin_date": data.get("last_checkin_date"),
        "checked_in_today": data.get("last_checkin_date") == today,
    })
    response.set_cookie(key="access_token", value=token, httponly=True, max_age=7*24*60*60, samesite="lax")
    return response


@router.get("/me")
async def get_me(authorization: str = Header(None)):
    """From Authorization: Bearer <token> get current user via bipthelper"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")

    settings = get_settings()
    token = authorization.replace("Bearer ", "")
    try:
        async with httpx.AsyncClient(base_url=settings.BIPTHELPER_URL, timeout=10.0) as client:
            response = await client.get(
                "/api/auth/me",
                headers={"Authorization": f"Bearer {token}"},
            )
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="bipthelper service unavailable")

    if response.status_code == 401:
        raise HTTPException(status_code=401, detail="Invalid token")
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to get user")

    return response.json()


@router.post("/logout")
def logout():
    response = JSONResponse({"message": "ok"})
    response.delete_cookie("access_token")
    return response


async def _get_user_from_token(token: str):
    """Call bipthelper /api/auth/me and return user dict or raise HTTPException"""
    settings = get_settings()
    try:
        async with httpx.AsyncClient(base_url=settings.BIPTHELPER_URL, timeout=10.0) as client:
            response = await client.get(
                "/api/auth/me",
                headers={"Authorization": f"Bearer {token}"},
            )
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="bipthelper service unavailable")

    if response.status_code == 401:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to verify user")

    return response.json()


async def get_current_admin(authorization: str = Header(None)):
    """Admin permission check - calls bipthelper to verify role"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = authorization.replace("Bearer ", "")
    user = await _get_user_from_token(token)

    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
