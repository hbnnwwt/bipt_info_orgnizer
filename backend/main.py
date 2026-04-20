# backend/main.py
import sys
import os

# bipthelper backend FIRST so its models/services are found by default
_bp = os.path.normpath("E:/code/bipthelper/backend").replace("\\", "/")
if _bp not in [p.replace("\\", "/") for p in sys.path]:
    sys.path.insert(0, _bp)

# organizer backend SECOND so its local modules (services, database, routers) take precedence
_backend_dir = os.path.normpath(os.path.dirname(os.path.abspath(__file__))).replace("\\", "/")
if _backend_dir not in [p.replace("\\", "/") for p in sys.path]:
    sys.path.insert(1, _backend_dir)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# These import from bipthelper (User model, config, etc.)
from database import get_session, create_db_and_tables
from models.user import User

# Local routers — their local imports (services.helper_client, etc.) find organizer's local modules
from routers.auth import router as auth_router
from routers.crawl_admin import router as crawl_admin_router
from routers.organizer_docs import router as organizer_docs_router


app = FastAPI(title="BIPTInfoOrganizer")

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


if __name__ == "__main__":
    import uvicorn
    create_db_and_tables()
    uvicorn.run(app, host="0.0.0.0", port=8001)
