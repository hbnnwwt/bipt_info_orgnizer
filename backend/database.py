# backend/database.py
# Organizer's own database setup.
# For bipthelper models (User), routes import directly from bipthelper via sys.path.

import sys
import subprocess
import os
from pathlib import Path
from sqlmodel import create_engine, Session, SQLModel

# Add bipthelper backend so "from models.user import User" works in routes
_bp_backend = Path("E:/code/bipthelper/backend")
if str(_bp_backend) not in sys.path:
    sys.path.append(str(_bp_backend))

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

_engine = create_engine(
    f"sqlite:///{DATA_DIR / 'organizer.db'}",
    echo=False,
    connect_args={"check_same_thread": False},
)


def create_db_and_tables():
    """Create local tables and delegate bipthelper table creation to subprocess."""
    # Create local tables
    from models.crawl_config import CrawlConfig  # noqa: F401
    from models.audit_log import AuditLog  # noqa: F401
    SQLModel.metadata.create_all(_engine)
    print(f"Organizer local tables created at {DATA_DIR / 'organizer.db'}")

    # Also init bipthelper tables via subprocess
    result = subprocess.run(
        [sys.executable, "-c", """
import sys
sys.path.insert(0, 'E:/code/bipthelper/backend')
from database import create_db_and_tables, init_admin_user
create_db_and_tables()
init_admin_user()
print('Bipthelper tables initialized.')
"""],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"DB init warning: {result.stderr.strip()}")
    else:
        print(result.stdout.strip())


def get_session():
    with Session(_engine) as session:
        yield session
