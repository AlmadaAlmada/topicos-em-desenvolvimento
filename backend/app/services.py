"""Regras de negócio convencionais (sem IA).

Atribuição de chamados e SLA são decisões que precisam ser previsíveis,
justas e auditáveis; um algoritmo determinístico simples resolve bem e
não requer dados históricos.
"""
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .ai.recommender import recommender
from .config import SLA_HOURS
from .models import Comment, KBArticle, Ticket, User

OPEN_STATUSES = ("Triagem", "Aberto", "Em atendimento", "Aguardando usuário")


def add_event(db: Session, ticket: Ticket, author: User, text: str) -> None:
    db.add(Comment(ticket_id=ticket.id, author_id=author.id, body=text, is_system=True))


def pick_technician(db: Session, category: Optional[str]) -> Optional[User]:
    """Atribuição automática por regra:
    1. Técnicos ativos com especialidade igual à categoria do chamado;
       se não houver, qualquer técnico ativo.
    2. Entre eles, o que tem MENOS chamados abertos (balanceamento de carga).
    3. Empate: o de menor id (determinístico).
    """
    open_count = (
        select(Ticket.assignee_id, func.count(Ticket.id).label("n"))
        .where(Ticket.status.in_(OPEN_STATUSES))
        .group_by(Ticket.assignee_id)
        .subquery()
    )
    base = (
        select(User, func.coalesce(open_count.c.n, 0).label("load"))
        .outerjoin(open_count, open_count.c.assignee_id == User.id)
        .where(User.role == "tecnico", User.active.is_(True))
        .order_by("load", User.id)
    )
    if category:
        row = db.execute(base.where(User.specialty == category)).first()
        if row:
            return row[0]
    row = db.execute(base).first()
    return row[0] if row else None


def sla_info(ticket: Ticket, now: Optional[datetime] = None) -> Tuple[Optional[datetime], bool]:
    if not ticket.priority:
        return None, False
    due = ticket.created_at + timedelta(hours=SLA_HOURS[ticket.priority])
    end = ticket.resolved_at or (now or datetime.utcnow())
    return due, end > due


def refresh_kb_index(db: Session) -> None:
    stamp = db.execute(select(func.count(KBArticle.id), func.max(KBArticle.updated_at))).one()
    if stamp == recommender._stamp:
        return
    articles = db.execute(select(KBArticle)).scalars().all()
    recommender.index(articles, tuple(stamp))


def suggest_articles(db: Session, text: str, category: Optional[str] = None, top_k: int = 3,
                     count_as_suggested: bool = False) -> List[dict]:
    refresh_kb_index(db)
    hits = recommender.search(text, top_k=top_k, category=category)
    out = []
    for article_id, score in hits:
        art = db.get(KBArticle, article_id)
        if art is None:
            continue
        if count_as_suggested:
            art.times_suggested += 1
        out.append({"id": art.id, "title": art.title, "category": art.category,
                    "solution": art.solution, "score": score})
    if count_as_suggested and out:
        db.commit()
    return out
