from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session, select

from backend.auth import create_access_token, get_current_user, require_admin
from backend.database import get_session, hash_password, verify_password
from backend.models import User, UserEmail

router = APIRouter(prefix="/api/auth", tags=["Autentizace"])

class LoginRequest(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    display_name: str
    role: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class CreateUserRequest(BaseModel):
    username: str
    password: str
    display_name: str
    role: str = "user"
    initial_email: Optional[str] = None

class UpdateProfileRequest(BaseModel):
    display_name: Optional[str] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = None

@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == data.username.strip().lower())).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nesprávné uživatelské jméno nebo heslo."
        )

    token = create_access_token({"sub": user.username})
    return LoginResponse(
        access_token=token,
        user=UserResponse(
            id=user.id,
            username=user.username,
            display_name=user.display_name or user.username,
            role=user.role
        )
    )

@router.post("/register", response_model=LoginResponse)
def register(data: CreateUserRequest, session: Session = Depends(get_session)):
    clean_username = data.username.strip().lower()
    if len(clean_username) < 2:
        raise HTTPException(status_code=400, detail="Uživatelské jméno musí mít alespoň 2 znaky.")
    if len(data.password) < 3:
        raise HTTPException(status_code=400, detail="Heslo/PIN musí mít alespoň 3 znaky.")

    existing = session.exec(select(User).where(User.username == clean_username)).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Uživatel se jménem '{clean_username}' již existuje.")

    # První registrovaný uživatel v systému se stává automaticky administrátorem
    has_any_user = session.exec(select(User)).first() is not None
    user_role = "admin" if not has_any_user else (data.role or "user")

    new_user = User(
        username=clean_username,
        display_name=data.display_name.strip() or clean_username,
        password_hash=hash_password(data.password),
        role=user_role
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    if data.initial_email:
        email = UserEmail(
            user_id=new_user.id,
            label="Hlavní e-mail",
            email_address=data.initial_email.strip(),
            is_default=True
        )
        session.add(email)
        session.commit()

    token = create_access_token({"sub": new_user.username})
    return LoginResponse(
        access_token=token,
        user=UserResponse(
            id=new_user.id,
            username=new_user.username,
            display_name=new_user.display_name,
            role=new_user.role
        )
    )

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        display_name=current_user.display_name or current_user.username,
        role=current_user.role
    )

@router.put("/profile", response_model=UserResponse)
def update_profile(
    data: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    user = session.get(User, current_user.id)
    if not user:
        raise HTTPException(status_code=404, detail="Uživatel nenalezen.")

    if data.display_name:
        user.display_name = data.display_name.strip()

    if data.new_password:
        if not data.current_password:
            raise HTTPException(status_code=400, detail="Pro změnu hesla musíte zadat současné heslo.")
        if not verify_password(data.current_password, user.password_hash):
            raise HTTPException(status_code=400, detail="Současné heslo je nesprávné.")
        if len(data.new_password) < 3:
            raise HTTPException(status_code=400, detail="Nové heslo musí mít alespoň 3 znaky.")
        user.password_hash = hash_password(data.new_password)

    session.add(user)
    session.commit()
    session.refresh(user)

    return UserResponse(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        role=user.role
    )

@router.get("/users", response_model=List[UserResponse])
def list_users(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    users = session.exec(select(User).order_by(User.id)).all()
    return [
        UserResponse(
            id=u.id,
            username=u.username,
            display_name=u.display_name or u.username,
            role=u.role
        )
        for u in users
    ]

@router.post("/users", response_model=UserResponse)
def create_user(
    data: CreateUserRequest,
    session: Session = Depends(get_session),
    admin: User = Depends(require_admin)
):
    clean_username = data.username.strip().lower()
    existing = session.exec(select(User).where(User.username == clean_username)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Uživatel se jménem '{clean_username}' již existuje."
        )

    new_user = User(
        username=clean_username,
        display_name=data.display_name.strip() or clean_username,
        password_hash=hash_password(data.password),
        role=data.role
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    if data.initial_email:
        email = UserEmail(
            user_id=new_user.id,
            label="Hlavní e-mail",
            email_address=data.initial_email.strip(),
            is_default=True
        )
        session.add(email)
        session.commit()

    return UserResponse(
        id=new_user.id,
        username=new_user.username,
        display_name=new_user.display_name,
        role=new_user.role
    )

@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    session: Session = Depends(get_session),
    admin: User = Depends(require_admin)
):
    if admin.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nemůžete smazat svůj vlastní administrátorský účet."
        )
    target_user = session.get(User, user_id)
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Uživatel nenalezen.")

    session.delete(target_user)
    session.commit()
    return {"message": f"Uživatel {target_user.username} byl úspěšně odstraněn."}
