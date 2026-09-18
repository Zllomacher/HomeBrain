import hashlib
import secrets
from sqlmodel import SQLModel, create_engine, Session, select
from backend.config import settings
from backend.models import User, UserEmail, Category

# SQLite engine with check_same_thread=False for FastAPI concurrency
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

def hash_password(password: str, salt: str = None) -> str:
    """Hash a password using PBKDF2 with a secure salt."""
    if not salt:
        salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations=100_000
    ).hex()
    return f"{salt}${hashed}"

def verify_password(plain_password: str, stored_hash: str) -> bool:
    """Verify password against stored salt$hash."""
    try:
        salt, expected_hash = stored_hash.split("$", 1)
        calculated = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations=100_000
        ).hex()
        return secrets.compare_digest(expected_hash, calculated)
    except Exception:
        return False

def init_db():
    """Create tables and seed initial default users & categories."""
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        # Check if users exist
        admin = session.exec(select(User).where(User.username == settings.DEFAULT_ADMIN_USERNAME)).first()
        if not admin:
            # Create default admin (e.g. Radek)
            admin = User(
                username=settings.DEFAULT_ADMIN_USERNAME,
                display_name=settings.DEFAULT_ADMIN_NAME,
                password_hash=hash_password(settings.DEFAULT_ADMIN_PASSWORD),
                role="admin"
            )
            session.add(admin)
            session.commit()
            session.refresh(admin)

            # Add default emails for admin
            session.add(UserEmail(
                user_id=admin.id,
                label="Služební e-mail",
                email_address="radek.prace@firma.cz",
                is_default=True
            ))
            session.add(UserEmail(
                user_id=admin.id,
                label="Soukromý e-mail",
                email_address="radek.soukromy@seznam.cz",
                is_default=False
            ))

        # Check if wife account exists
        wife = session.exec(select(User).where(User.username == settings.DEFAULT_WIFE_USERNAME)).first()
        if not wife:
            wife = User(
                username=settings.DEFAULT_WIFE_USERNAME,
                display_name=settings.DEFAULT_WIFE_NAME,
                password_hash=hash_password(settings.DEFAULT_WIFE_PASSWORD),
                role="user"
            )
            session.add(wife)
            session.commit()
            session.refresh(wife)

            # Add default email for wife
            session.add(UserEmail(
                user_id=wife.id,
                label="Osobní e-mail",
                email_address="monika@seznam.cz",
                is_default=True
            ))

        # Seed standard categories if none exist
        categories = session.exec(select(Category)).all()
        if not categories:
            default_categories = [
                Category(
                    name="Paragon",
                    icon="receipt",
                    subject_template="Paragon - {date} - {note}",
                    target_folder_name="Paragony",
                    sort_order=1
                ),
                Category(
                    name="Lékařská zpráva",
                    icon="heart-pulse",
                    subject_template="Lékařská zpráva - {date} - {note}",
                    target_folder_name="Lekarske_zpravy",
                    sort_order=2
                ),
                Category(
                    name="Smlouva",
                    icon="file-text",
                    subject_template="Smlouva - {date} - {note}",
                    target_folder_name="Smlouvy",
                    sort_order=3
                ),
                Category(
                    name="Auto & Parkování",
                    icon="car",
                    subject_template="Parkování - {date} - {note}",
                    target_folder_name="Auto_Parkovani",
                    sort_order=4
                ),
                Category(
                    name="Ostatní",
                    icon="folder",
                    subject_template="Dokument - {date} - {note}",
                    target_folder_name="Ostatni",
                    sort_order=5
                )
            ]
            session.add_all(default_categories)
            session.commit()

def get_session():
    with Session(engine) as session:
        yield session
