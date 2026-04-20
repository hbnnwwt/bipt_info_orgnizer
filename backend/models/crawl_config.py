from sqlmodel import SQLModel, Field
from typing import Optional
import uuid

class CrawlConfig(SQLModel, table=True):
    __tablename__ = "crawl_configs"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str
    url: str
    category: Optional[str] = None
    parent_category: Optional[str] = None
    sub_category: Optional[str] = None
    selector: str = "body"
    is_list_page: bool = True
    article_selector: str = "a"
    link_prefix: Optional[str] = None
    pagination_selector: str = ""
    pagination_max: int = 0
    enabled: bool = True
    last_hash: Optional[str] = None
    last_crawl: Optional[str] = None
    initialized: bool = False
    auto_interval_hours: int = 0