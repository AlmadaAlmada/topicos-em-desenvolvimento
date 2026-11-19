"""Funcionalidade 5: base de conhecimento com sugestão de soluções (IA na busca)."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import KBArticle, Ticket, User
from ..schemas import KBIn, KBOut
from ..security import get_current_user, require_roles

router = APIRouter(prefix="/api/kb", tags=["Base de conhecimento"])


@router.get("", response_model=List[KBOut])
def list_articles(q: Optional[str] = None, category: Optional[str] = None, db: Session = Depends(get_db),
                  _: User = Depends(get_current_user)):
    query = select(KBArticle).order_by(KBArticle.times_helpful.desc(), KBArticle.title)
    if category:
        query = query.where(KBArticle.category == category)
    if q:
        like = f"%{q}%"
        query = query.where(or_(KBArticle.title.ilike(like), KBArticle.problem.ilike(like),
                                KBArticle.solution.ilike(like)))
    return db.execute(query).scalars().all()


@router.get("/{article_id}", response_model=KBOut)
def get_article(article_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    art = db.get(KBArticle, article_id)
    if art is None:
        raise HTTPException(404, "Artigo não encontrado")
    return art


@router.post("", response_model=KBOut, status_code=201)
def create_article(data: KBIn, db: Session = Depends(get_db), user: User = Depends(require_roles("tecnico", "admin"))):
    if data.source_ticket_id and db.get(Ticket, data.source_ticket_id) is None:
        raise HTTPException(400, "Chamado de origem não existe")
    art = KBArticle(**data.model_dump(), author_id=user.id)
    db.add(art)
    db.commit()
    db.refresh(art)
    return art


@router.put("/{article_id}", response_model=KBOut)
def update_article(article_id: int, data: KBIn, db: Session = Depends(get_db),
                   _: User = Depends(require_roles("tecnico", "admin"))):
    art = db.get(KBArticle, article_id)
    if art is None:
        raise HTTPException(404, "Artigo não encontrado")
    for k, v in data.model_dump().items():
        setattr(art, k, v)
    db.commit()
    db.refresh(art)
    return art


@router.delete("/{article_id}", status_code=204)
def delete_article(article_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles("admin"))):
    art = db.get(KBArticle, article_id)
    if art is None:
        raise HTTPException(404, "Artigo não encontrado")
    for ticket in db.execute(select(Ticket).where(Ticket.kb_article_used_id == art.id)).scalars():
        ticket.kb_article_used_id = None
    db.delete(art)
    db.commit()


@router.post("/{article_id}/helpful", response_model=KBOut)
def mark_helpful(article_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    art = db.get(KBArticle, article_id)
    if art is None:
        raise HTTPException(404, "Artigo não encontrado")
    art.times_helpful += 1
    db.commit()
    db.refresh(art)
    return art
