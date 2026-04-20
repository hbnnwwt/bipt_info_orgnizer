import os
from sqlmodel import SQLModel, create_engine

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "organizer.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)

def create_db_and_tables():
    from models.crawl_config import CrawlConfig
    from models.audit_log import AuditLog
    SQLModel.metadata.create_all(engine)

def get_session():
    from sqlmodel import Session
    with Session(engine) as session:
        yield session