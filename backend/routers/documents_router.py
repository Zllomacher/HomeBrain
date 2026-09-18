import io
import os
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from sqlmodel import Session, select

from backend.auth import get_current_user
from backend.config import BASE_DIR, settings
from backend.database import get_session
from backend.mailer import format_subject, send_document_email
from backend.models import Category, Document, User

router = APIRouter(prefix="/api/documents", tags=["Dokumenty"])

UPLOAD_DIR = BASE_DIR / settings.STORAGE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

class DocumentResponse(BaseModel):
    id: int
    user_id: int
    user_name: str
    category_id: Optional[int]
    category_name: str
    original_filename: str
    file_size: int
    content_type: str
    note: Optional[str]
    sent_to_email: Optional[str]
    email_subject: Optional[str]
    email_status: str
    status: str
    created_at: datetime

class UpdateStatusRequest(BaseModel):
    status: str # "pending", "saved_to_pc", "archived"

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    category_id: Optional[int] = Form(None),
    target_email: str = Form(...),
    note: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    # Determine category and subject
    category_name = "Ostatní"
    subject_template = "{category} - {date} - {note}"
    target_folder = "Ostatni"

    if category_id:
        cat = session.get(Category, category_id)
        if cat:
            category_name = cat.name
            subject_template = cat.subject_template
            target_folder = cat.target_folder_name

    # Format email subject
    email_subject = format_subject(subject_template, category_name, note)

    # Save file safely
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_orig_name = Path(file.filename).name.replace(" ", "_") if file.filename else "photo.jpg"
    saved_filename = f"{timestamp}_{current_user.username}_{clean_orig_name}"
    save_path = UPLOAD_DIR / saved_filename

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size = save_path.stat().st_size
    content_type = file.content_type or "image/jpeg"

    # Send email
    email_status, email_message = await send_document_email(
        to_email=target_email.strip(),
        subject=email_subject,
        attachment_path=save_path,
        original_filename=clean_orig_name,
        sender_name=current_user.display_name or current_user.username,
        note=note
    )

    # Create document record in database
    doc = Document(
        user_id=current_user.id,
        category_id=category_id,
        category_name=category_name,
        original_filename=clean_orig_name,
        saved_filename=saved_filename,
        file_path=str(save_path),
        file_size=file_size,
        content_type=content_type,
        note=note.strip() if note else None,
        sent_to_email=target_email.strip(),
        email_subject=email_subject,
        email_status=email_status,
        status="pending"
    )
    session.add(doc)
    session.commit()
    session.refresh(doc)

    return DocumentResponse(
        id=doc.id,
        user_id=doc.user_id,
        user_name=current_user.display_name or current_user.username,
        category_id=doc.category_id,
        category_name=doc.category_name,
        original_filename=doc.original_filename,
        file_size=doc.file_size,
        content_type=doc.content_type,
        note=doc.note,
        sent_to_email=doc.sent_to_email,
        email_subject=doc.email_subject,
        email_status=doc.email_status,
        status=doc.status,
        created_at=doc.created_at
    )

@router.get("/inbox", response_model=List[DocumentResponse])
def get_inbox_documents(
    status_filter: Optional[str] = "pending",
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    query = select(Document)
    if status_filter and status_filter != "all":
        query = query.where(Document.status == status_filter)

    query = query.order_by(Document.created_at.desc())
    docs = session.exec(query).all()

    # Pre-fetch user map for fast display names
    users = session.exec(select(User)).all()
    user_map = {u.id: (u.display_name or u.username) for u in users}

    result = []
    for d in docs:
        result.append(DocumentResponse(
            id=d.id,
            user_id=d.user_id,
            user_name=user_map.get(d.user_id, "Neznámý"),
            category_id=d.category_id,
            category_name=d.category_name,
            original_filename=d.original_filename,
            file_size=d.file_size,
            content_type=d.content_type,
            note=d.note,
            sent_to_email=d.sent_to_email,
            email_subject=d.email_subject,
            email_status=d.email_status,
            status=d.status,
            created_at=d.created_at
        ))
    return result

@router.get("/{document_id}/file")
def get_document_file(
    document_id: int,
    download: bool = False,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    doc = session.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Dokument nebyl nalezen.")

    path = Path(doc.file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Soubor na disku neexistuje.")

    return FileResponse(
        path=path,
        media_type=doc.content_type,
        filename=doc.original_filename if download else None
    )

@router.put("/{document_id}/status")
def update_document_status(
    document_id: int,
    data: UpdateStatusRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    doc = session.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Dokument nebyl nalezen.")

    doc.status = data.status
    session.add(doc)
    session.commit()
    return {"message": "Stav byl úspěšně změněn.", "status": doc.status}

@router.get("/export-zip")
def export_documents_zip(
    status_filter: Optional[str] = "pending",
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    query = select(Document)
    if status_filter and status_filter != "all":
        query = query.where(Document.status == status_filter)
    docs = session.exec(query).all()

    if not docs:
        raise HTTPException(status_code=404, detail="Žádné dokumenty k exportu.")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for doc in docs:
            file_p = Path(doc.file_path)
            if file_p.exists():
                # Store inside category folder: e.g. "Paragony/2026-09-19_paragon.jpg"
                folder_clean = doc.category_name.replace(" ", "_")
                archive_name = f"{folder_clean}/{file_p.name}"
                zip_file.write(file_p, arcname=archive_name)

    zip_buffer.seek(0)
    filename = f"HomeBrain_export_{datetime.now().strftime('%Y%m%d_%H%M')}.zip"
    return StreamingResponse(
        zip_buffer,
        media_type="application/x-zip-compressed",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
