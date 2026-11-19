from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .config import CATEGORIES, PRIORITIES, ROLES, STATUSES


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------- Usuários / autenticação ----------

class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=160)
    password: str = Field(min_length=6, max_length=128)
    department: Optional[str] = Field(default=None, max_length=80)

    @field_validator("email")
    @classmethod
    def email_format(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("E-mail inválido")
        return v


class LoginIn(BaseModel):
    email: str
    password: str


class UserOut(ORM):
    id: int
    name: str
    email: str
    role: str
    specialty: Optional[str] = None
    department: Optional[str] = None
    active: bool


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class UserUpdate(BaseModel):
    role: Optional[str] = None
    specialty: Optional[str] = None
    active: Optional[bool] = None

    @field_validator("role")
    @classmethod
    def valid_role(cls, v):
        if v is not None and v not in ROLES:
            raise ValueError(f"Perfil deve ser um de {ROLES}")
        return v

    @field_validator("specialty")
    @classmethod
    def valid_specialty(cls, v):
        if v not in (None, "") and v not in CATEGORIES:
            raise ValueError(f"Especialidade deve ser uma de {CATEGORIES}")
        return v or None


class UserBrief(ORM):
    id: int
    name: str


# ---------- IA ----------

class ClassifyIn(BaseModel):
    title: str = ""
    description: str = ""


class ClassificationOut(BaseModel):
    category: str
    category_confidence: float
    category_scores: dict
    priority: str
    priority_confidence: float
    priority_rule: Optional[str] = None
    needs_triage: bool
    model_version: str


class KBSuggestion(BaseModel):
    id: int
    title: str
    category: Optional[str]
    solution: str
    score: float


# ---------- Chamados ----------

class TicketCreate(BaseModel):
    title: str = Field(min_length=5, max_length=200)
    description: str = Field(min_length=10, max_length=5000)


class SelfResolveIn(BaseModel):
    """Usuário resolveu sozinho usando um artigo sugerido, sem abrir chamado."""
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=5000)
    kb_article_id: int


class TicketUpdate(BaseModel):
    status: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    assignee_id: Optional[int] = None
    resolution: Optional[str] = Field(default=None, max_length=5000)
    kb_article_used_id: Optional[int] = None

    @field_validator("status")
    @classmethod
    def valid_status(cls, v):
        if v is not None and v not in STATUSES:
            raise ValueError(f"Status deve ser um de {STATUSES}")
        return v

    @field_validator("category")
    @classmethod
    def valid_category(cls, v):
        if v is not None and v not in CATEGORIES:
            raise ValueError(f"Categoria deve ser uma de {CATEGORIES}")
        return v

    @field_validator("priority")
    @classmethod
    def valid_priority(cls, v):
        if v is not None and v not in PRIORITIES:
            raise ValueError(f"Prioridade deve ser uma de {PRIORITIES}")
        return v


class CommentIn(BaseModel):
    body: str = Field(min_length=1, max_length=5000)


class CommentOut(ORM):
    id: int
    body: str
    is_system: bool
    created_at: datetime
    author: UserBrief


class TicketOut(ORM):
    id: int
    title: str
    description: str
    status: str
    category: Optional[str]
    priority: Optional[str]
    ai_category: Optional[str]
    ai_category_confidence: Optional[float]
    ai_priority: Optional[str]
    ai_priority_confidence: Optional[float]
    ai_model_version: Optional[str]
    priority_rule: Optional[str]
    classification_reviewed: bool
    requester: UserBrief
    assignee: Optional[UserBrief]
    resolution: Optional[str]
    kb_article_used_id: Optional[int]
    self_resolved: bool
    created_at: datetime
    assigned_at: Optional[datetime]
    resolved_at: Optional[datetime]
    updated_at: datetime
    sla_due_at: Optional[datetime] = None
    sla_breached: bool = False


class TicketDetail(TicketOut):
    comments: List[CommentOut] = []
    suggestions: List[KBSuggestion] = []


# ---------- Base de conhecimento ----------

class KBIn(BaseModel):
    title: str = Field(min_length=5, max_length=200)
    problem: str = Field(min_length=10)
    solution: str = Field(min_length=10)
    category: Optional[str] = None
    source_ticket_id: Optional[int] = None

    @field_validator("category")
    @classmethod
    def valid_category(cls, v):
        if v not in (None, "") and v not in CATEGORIES:
            raise ValueError(f"Categoria deve ser uma de {CATEGORIES}")
        return v or None


class KBOut(ORM):
    id: int
    title: str
    problem: str
    solution: str
    category: Optional[str]
    source_ticket_id: Optional[int]
    times_suggested: int
    times_helpful: int
    created_at: datetime
    updated_at: datetime
    author: Optional[UserBrief]


class ModelVersionOut(ORM):
    version: str
    trained_at: datetime
    samples: int
    samples_from_tickets: int
    category_accuracy: float
    priority_accuracy: float
    active: bool
