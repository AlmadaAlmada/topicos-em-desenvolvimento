"""Modelo de dados (ORM).

Separação deliberada entre o que a IA sugeriu (ai_*) e o valor final
adotado (category/priority). Isso permite auditar a IA, medir acurácia
em produção e retreinar o modelo apenas com rótulos confirmados por humanos.
"""
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utcnow() -> datetime:
    return datetime.utcnow()


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(256))
    role: Mapped[str] = mapped_column(String(20), default="solicitante")
    # Para técnicos: categoria em que é especialista (usada na atribuição).
    specialty: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="Aberto", index=True)

    # Valores finais (podem ser ajustados por técnicos).
    category: Mapped[Optional[str]] = mapped_column(String(40), nullable=True, index=True)
    priority: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)

    # Rastro da IA (nunca sobrescrito depois da criação).
    ai_category: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    ai_category_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ai_priority: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    ai_priority_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ai_model_version: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    priority_rule: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    # True quando um humano confirmou ou corrigiu a classificação.
    classification_reviewed: Mapped[bool] = mapped_column(Boolean, default=False)

    requester_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    assignee_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)

    resolution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    kb_article_used_id: Mapped[Optional[int]] = mapped_column(ForeignKey("kb_articles.id"), nullable=True)
    self_resolved: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    assigned_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    requester: Mapped[User] = relationship(foreign_keys=[requester_id])
    assignee: Mapped[Optional[User]] = relationship(foreign_keys=[assignee_id])
    comments: Mapped[List["Comment"]] = relationship(
        back_populates="ticket", cascade="all, delete-orphan", order_by="Comment.created_at"
    )


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    body: Mapped[str] = mapped_column(Text)
    # Eventos de sistema (mudança de status, atribuição) também ficam aqui.
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    ticket: Mapped[Ticket] = relationship(back_populates="comments")
    author: Mapped[User] = relationship()


class KBArticle(Base):
    __tablename__ = "kb_articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    problem: Mapped[str] = mapped_column(Text)
    solution: Mapped[str] = mapped_column(Text)
    category: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    author_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    source_ticket_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    times_suggested: Mapped[int] = mapped_column(Integer, default=0)
    times_helpful: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    author: Mapped[Optional[User]] = relationship()


class ModelVersion(Base):
    """Registro de cada treinamento do classificador (rastreabilidade)."""

    __tablename__ = "model_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    version: Mapped[str] = mapped_column(String(40), unique=True)
    trained_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    samples: Mapped[int] = mapped_column(Integer)
    samples_from_tickets: Mapped[int] = mapped_column(Integer, default=0)
    category_accuracy: Mapped[float] = mapped_column(Float)
    priority_accuracy: Mapped[float] = mapped_column(Float)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
