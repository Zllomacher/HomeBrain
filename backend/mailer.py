import json
import logging
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path
from typing import Optional, Tuple
import aiosmtplib

from backend.config import settings, BASE_DIR

logger = logging.getLogger("homebrain.mailer")

def format_subject(template: str, category_name: str, note: Optional[str] = None) -> str:
    today_str = datetime.now().strftime("%Y-%m-%d")
    note_str = (note or "").strip()
    
    subject = template.replace("{category}", category_name)
    subject = subject.replace("{date}", today_str)
    subject = subject.replace("{note}", note_str)
    
    # Clean up awkward formatting if note was empty (e.g. " - ")
    subject = subject.strip(" -:")
    if not subject:
        subject = f"{category_name} - {today_str}"
    return subject

async def send_document_email(
    to_email: str,
    subject: str,
    attachment_path: Path,
    original_filename: str,
    sender_name: str = "HomeBrain",
    note: Optional[str] = None
) -> Tuple[str, str]:
    """
    Sends an email with attachment.
    Returns (status, message), where status in ["sent", "mock_sent", "failed"].
    """
    if not to_email or "@" not in to_email:
        return "failed", "Neplatná cílová e-mailová adresa."

    # Check if real SMTP is enabled
    if not settings.SMTP_ENABLED or not settings.SMTP_HOST:
        # MOCK MODE: Save preview to storage/mail_previews
        preview_dir = BASE_DIR / settings.STORAGE_DIR / "mail_previews"
        preview_dir.mkdir(parents=True, exist_ok=True)

        preview_file = preview_dir / f"mail_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{attachment_path.stem}.json"
        preview_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "to": to_email,
            "subject": subject,
            "sender": sender_name,
            "note": note,
            "attachment": str(attachment_path),
            "original_filename": original_filename,
            "mode": "TEST_MOCK_MODE (SMTP vypnuto v .env)"
        }
        with open(preview_file, "w", encoding="utf-8") as f:
            json.dump(preview_data, f, ensure_ascii=False, indent=2)

        logger.info(f"[MOCK EMAIL] Odesláno do náhledu pro {to_email}: {subject}")
        return "mock_sent", f"E-mail uložen do testovacího náhledu (cílový e-mail: {to_email})."

    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = f"{sender_name} <{settings.SMTP_FROM}>"
        msg["To"] = to_email

        body = f"Ahoj,\n\nv příloze posílám vyfocený dokument: {subject}.\n"
        if note:
            body += f"\nPoznámka: {note}\n"
        body += f"\nOdesláno systémem HomeBrain dne {datetime.now().strftime('%d.%m.%Y v %H:%M')}.\n"

        msg.set_content(body)

        # Attach file
        with open(attachment_path, "rb") as f:
            file_data = f.read()

        # Guess mime type or default to octet-stream
        maintype = "image" if attachment_path.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"] else "application"
        subtype = attachment_path.suffix.lower().lstrip(".") or "octet-stream"
        if subtype == "jpg":
            subtype = "jpeg"

        msg.add_attachment(
            file_data,
            maintype=maintype,
            subtype=subtype,
            filename=original_filename or attachment_path.name
        )

        use_tls = settings.SMTP_PORT == 465
        start_tls = settings.SMTP_PORT == 587 or settings.SMTP_USE_TLS

        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER if settings.SMTP_USER else None,
            password=settings.SMTP_PASSWORD if settings.SMTP_PASSWORD else None,
            use_tls=use_tls,
            start_tls=start_tls if not use_tls else False
        )
        logger.info(f"E-mail úspěšně odeslán na {to_email} s předmětem: {subject}")
        return "sent", f"E-mail byl úspěšně odeslán na {to_email}."
    except Exception as e:
        logger.error(f"Chyba při odesílání e-mailu na {to_email}: {e}")
        return "failed", f"Chyba při odesílání e-mailu: {str(e)}"
