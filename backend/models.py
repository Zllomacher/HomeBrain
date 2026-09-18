from datetime import datetime, timezone
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, nullable=False)
    display_name: str = Field(default="")
    password_hash: str = Field(nullable=False)
    role: str = Field(default="user") # "admin" or "user"
    created_at: datetime = Field(default_factory=utc_now)

    emails: List["UserEmail"] = Relationship(back_populates="user")
    documents: List["Document"] = Relationship(back_populates="user")

class UserEmail(SQLModel, table=True):
    __tablename__ = "user_emails"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", nullable=False)
    label: str = Field(default="Hlavní e-mail") # e.g. "Služební", "Soukromý"
    email_address: str = Field(nullable=False)
    is_default: bool = Field(default=False)

    user: Optional[User] = Relationship(back_populates="emails")

class Category(SQLModel, table=True):
    __tablename__ = "categories"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="users.id", nullable=True) # None = global shared
    name: str = Field(nullable=False) # e.g. "Paragon", "Lékařská zpráva", "Smlouva"
    icon: str = Field(default="receipt") # "receipt", "heart-pulse", "file-text", "car", "folder"
    default_email: Optional[str] = Field(default=None, nullable=True)
    subject_template: str = Field(default="{category} - {date}")
    target_folder_name: str = Field(default="Dokumenty")
    sort_order: int = Field(default=0)

class Document(SQLModel, table=True):
    __tablename__ = "documents"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", nullable=False)
    category_id: Optional[int] = Field(default=None, foreign_key="categories.id", nullable=True)
    category_name: str = Field(default="Ostatní")
    
    original_filename: str = Field(default="")
    saved_filename: str = Field(default="")
    file_path: str = Field(nullable=False)
    file_size: int = Field(default=0)
    content_type: str = Field(default="image/jpeg")

    note: Optional[str] = Field(default=None, nullable=True)
    sent_to_email: Optional[str] = Field(default=None, nullable=True)
    email_subject: Optional[str] = Field(default=None, nullable=True)
    email_status: str = Field(default="none") # "sent", "mock_sent", "failed", "none"

    status: str = Field(default="pending") # "pending", "saved_to_pc", "archived"
    created_at: datetime = Field(default_factory=utc_now)

    user: Optional[User] = Relationship(back_populates="documents")
