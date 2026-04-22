# backend/main.py
import sys
import os

# organizer backend FIRST — all organizer's own modules (database, routers, services)
_backend_dir = os.path.normpath(os.path.dirname(os.path.abspath(__file__))).replace("\\", "/")
if _backend_dir not in [p.replace("\\", "/") for p in sys.path]:
    sys.path.insert(0, _backend_dir)

# bipthelper backend APPENDED — only for explicit bipthelper model imports in routes
_bp = os.path.normpath("E:/code/bipthelper/backend").replace("\\", "/")
if _bp not in [p.replace("\\", "/") for p in sys.path]:
    sys.path.append(_bp)

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from database import get_session, create_db_and_tables

# Local routers
from routers.auth import router as auth_router
from routers.crawl_admin import router as crawl_admin_router
from routers.organizer_docs import router as organizer_docs_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(title="BIPTInfoOrganizer", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(crawl_admin_router, prefix="/api/admin", tags=["crawl"])
app.include_router(organizer_docs_router, prefix="/api", tags=["documents"])


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "organizer"}


# Serve frontend SPA
_frontend_dir = os.path.join(_backend_dir, "assets", "frontend")
if os.path.isdir(_frontend_dir):
    app.mount("/assets", StaticFiles(directory=os.path.join(_frontend_dir, "assets")), name="frontend-assets")

    @app.get("/{path:path}")
    async def serve_spa(path: str):
        """Catch-all: serve frontend SPA, fall back to index.html for client-side routing."""
        file_path = os.path.join(_frontend_dir, path)
        if path and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(_frontend_dir, "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
