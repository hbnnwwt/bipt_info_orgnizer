from sqlmodel import SQLModel, Field

class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_logs"
    id: str = Field(primary_key=True)
    user_id: str = ""
    username: str
    action: str
    target: str = ""
    detail: str = ""
    created_at: str = ""