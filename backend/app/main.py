"""HelpDesk Inteligente - API.

Execução:  uvicorn app.main:app --reload
Documentação interativa: http://localhost:8000/docs
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from .ai.classifier import classifier
from .config import CATEGORIES, CORS_ORIGINS, PRIORITIES, ROLES, STATUSES
from .database import Base, SessionLocal, engine
from .models import ModelVersion
from .routers import ai_admin, auth, dashboard, kb, tickets
from .seed import seed


def startup() -> None:
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        active = db.execute(select(ModelVersion).where(ModelVersion.active.is_(True))).scalar_one_or_none()
        if active is None or not classifier.load(active.version):
            # Primeiro uso (ou arquivo do modelo ausente): treina com a semente.
            ai_admin.train_and_register(db)
        seed(db, with_history=os.getenv("HELPDESK_SEED_HISTORY", "1") == "1")


@asynccontextmanager
async def lifespan(_: FastAPI):
    startup()
    yield


app = FastAPI(
    title="HelpDesk Inteligente",
    description="Gestão de chamados de suporte com apoio de IA (classificação e sugestão de soluções).",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

for r in (auth.router, tickets.router, kb.router, dashboard.router, ai_admin.router):
    app.include_router(r)


@app.get("/api/meta", tags=["Sistema"])
def meta():
    return {"categories": CATEGORIES, "priorities": PRIORITIES, "statuses": STATUSES, "roles": ROLES,
            "model_version": classifier.version}


@app.get("/api/health", tags=["Sistema"])
def health():
    return {"status": "ok", "model_loaded": classifier.ready}
