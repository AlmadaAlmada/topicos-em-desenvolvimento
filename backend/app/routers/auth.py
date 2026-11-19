"""Funcionalidade 1: cadastro e autenticação de usuários (sem IA)."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import LoginIn, RegisterIn, TokenOut, UserOut, UserUpdate
from ..security import create_token, get_current_user, hash_password, require_roles, verify_password

router = APIRouter(prefix="/api", tags=["Usuários e autenticação"])


@router.post("/auth/register", response_model=TokenOut, status_code=201)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    if db.execute(select(User).where(User.email == data.email)).scalar_one_or_none():
        raise HTTPException(status.HTTP_409_CONFLICT, "E-mail já cadastrado")
    # Todo autocadastro entra como solicitante; só admin promove perfis.
    user = User(name=data.name.strip(), email=data.email, password_hash=hash_password(data.password),
                department=data.department, role="solicitante")
    db.add(user)
    db.commit()
    return TokenOut(access_token=create_token(user), user=UserOut.model_validate(user))


@router.post("/auth/login", response_model=TokenOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.email == data.email.strip().lower())).scalar_one_or_none()
    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "E-mail ou senha inválidos")
    if not user.active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Usuário desativado")
    return TokenOut(access_token=create_token(user), user=UserOut.model_validate(user))


@router.get("/auth/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.get("/users", response_model=List[UserOut])
def list_users(role: Optional[str] = None, db: Session = Depends(get_db),
               _: User = Depends(require_roles("tecnico", "admin"))):
    query = select(User).order_by(User.name)
    if role:
        query = query.where(User.role == role)
    return db.execute(query).scalars().all()


@router.patch("/users/{user_id}", response_model=UserOut)
def update_user(user_id: int, data: UserUpdate, db: Session = Depends(get_db),
                admin: User = Depends(require_roles("admin"))):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(404, "Usuário não encontrado")
    if user.id == admin.id and (data.role not in (None, "admin") or data.active is False):
        raise HTTPException(400, "Você não pode remover o próprio acesso de administrador")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    db.commit()
    return user
