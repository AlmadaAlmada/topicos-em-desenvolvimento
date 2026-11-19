"""Gestão do ciclo de vida do modelo de IA (sustentação)."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from ..ai.classifier import classifier
from ..database import get_db
from ..models import ModelVersion, Ticket, User
from ..schemas import ModelVersionOut
from ..security import require_roles

router = APIRouter(prefix="/api/ai", tags=["IA"])

# Exige um mínimo de novos rótulos para valer a pena retreinar.
MIN_NEW_SAMPLES = 1


def reviewed_samples(db: Session):
    rows = db.execute(
        select(Ticket).where(Ticket.classification_reviewed.is_(True), Ticket.self_resolved.is_(False),
                             Ticket.category.is_not(None), Ticket.priority.is_not(None))
    ).scalars().all()
    return [(t.title, t.description, t.category, t.priority) for t in rows]


def train_and_register(db: Session) -> ModelVersion:
    report = classifier.train(extra=reviewed_samples(db))
    db.execute(update(ModelVersion).values(active=False))
    mv = ModelVersion(version=report.version, samples=report.samples,
                      samples_from_tickets=report.samples_from_tickets,
                      category_accuracy=round(report.category_accuracy, 4),
                      priority_accuracy=round(report.priority_accuracy, 4), active=True)
    db.add(mv)
    db.commit()
    return mv


@router.get("/models", response_model=List[ModelVersionOut])
def list_models(db: Session = Depends(get_db), _: User = Depends(require_roles("tecnico", "admin"))):
    return db.execute(select(ModelVersion).order_by(ModelVersion.trained_at.desc())).scalars().all()


@router.post("/retrain", response_model=ModelVersionOut)
def retrain(db: Session = Depends(get_db), _: User = Depends(require_roles("admin"))):
    return train_and_register(db)


@router.post("/models/{version}/activate", response_model=ModelVersionOut)
def activate(version: str, db: Session = Depends(get_db), _: User = Depends(require_roles("admin"))):
    """Rollback: reativa uma versão anterior do modelo."""
    mv = db.execute(select(ModelVersion).where(ModelVersion.version == version)).scalar_one_or_none()
    if mv is None or not classifier.load(version):
        raise HTTPException(404, "Versão não encontrada")
    db.execute(update(ModelVersion).values(active=False))
    mv.active = True
    db.commit()
    return mv
