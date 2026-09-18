from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session, select, or_

from backend.auth import get_current_user
from backend.database import get_session
from backend.models import User, UserEmail, Category

router = APIRouter(prefix="/api/settings", tags=["Nastavení a Složky"])

# --- Models ---
class UserEmailCreate(BaseModel):
    label: str
    email_address: str
    is_default: bool = False

class UserEmailResponse(BaseModel):
    id: int
    user_id: int
    label: str
    email_address: str
    is_default: bool

class CategoryCreate(BaseModel):
    name: str
    icon: Optional[str] = "folder"
    default_email: Optional[str] = None
    subject_template: Optional[str] = "{category} - {date} - {note}"
    target_folder_name: Optional[str] = None

class CategoryResponse(BaseModel):
    id: int
    name: str
    icon: str
    default_email: Optional[str] = None
    subject_template: str
    target_folder_name: str
    sort_order: int

# --- Email Endpoints ---
@router.get("/emails", response_model=List[UserEmailResponse])
def get_user_emails(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    emails = session.exec(
        select(UserEmail)
        .where(UserEmail.user_id == current_user.id)
        .order_by(UserEmail.is_default.desc(), UserEmail.id.asc())
    ).all()
    return emails

@router.post("/emails", response_model=UserEmailResponse)
def add_user_email(
    data: UserEmailCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    # If set as default, reset other defaults
    if data.is_default:
        existing_defaults = session.exec(
            select(UserEmail).where(UserEmail.user_id == current_user.id, UserEmail.is_default == True)
        ).all()
        for e in existing_defaults:
            e.is_default = False
            session.add(e)

    new_email = UserEmail(
        user_id=current_user.id,
        label=data.label.strip(),
        email_address=data.email_address.strip(),
        is_default=data.is_default
    )
    session.add(new_email)
    session.commit()
    session.refresh(new_email)
    return new_email

@router.delete("/emails/{email_id}")
def delete_user_email(
    email_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    email = session.get(UserEmail, email_id)
    if not email or email.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="E-mail nenalezen.")
    session.delete(email)
    session.commit()
    return {"message": "E-mail byl smazán."}

# --- Category / Folder Endpoints ---
@router.get("/categories", response_model=List[CategoryResponse])
def get_categories(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    # Categories available to user: either user_id is None (shared) or matches current_user.id
    categories = session.exec(
        select(Category)
        .where(or_(Category.user_id == None, Category.user_id == current_user.id))
        .order_by(Category.sort_order.asc(), Category.id.asc())
    ).all()
    return categories

@router.post("/categories", response_model=CategoryResponse)
def create_category(
    data: CategoryCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    target_folder = data.target_folder_name or data.name.strip().replace(" ", "_")
    category = Category(
        user_id=current_user.id,
        name=data.name.strip(),
        icon=data.icon or "folder",
        default_email=data.default_email.strip() if data.default_email else None,
        subject_template=data.subject_template or "{category} - {date} - {note}",
        target_folder_name=target_folder,
        sort_order=10
    )
    session.add(category)
    session.commit()
    session.refresh(category)
    return category

@router.delete("/categories/{category_id}")
def delete_category(
    category_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    category = session.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Kategorie nenalezena.")
    if category.user_id is not None and category.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Nemáte oprávnění smazat tuto kategorii.")

    session.delete(category)
    session.commit()
    return {"message": "Kategorie byla smazána."}
