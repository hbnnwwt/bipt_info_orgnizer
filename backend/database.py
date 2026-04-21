# backend/database.py
# Organizer's own SQLite (data/organizer.db).
# sys.path already configured by main.py: bipthelper at [0], organizer at [1].
# Models imported here resolve to organizer's local models (path[1]).

import os
from sqlmodel import create_engine, Session, SQLModel

DATA_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data"))
os.makedirs(DATA_DIR, exist_ok=True)

_engine = create_engine(
    f"sqlite:///{DATA_DIR}/organizer.db",
    echo=False,
    connect_args={"check_same_thread": False},
)


def create_db_and_tables():
    """Create tables in organizer's SQLite."""
    from models.crawl_config import CrawlConfig  # noqa: F401
    from models.audit_log import AuditLog  # noqa: F401
    SQLModel.metadata.create_all(_engine)
    print(f"Organizer tables at {DATA_DIR}/organizer.db")


def get_session():
    with Session(_engine) as session:
        yield session
