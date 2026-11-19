"""Funcionalidades 2, 3 e 4: abertura, classificação/priorização com IA e
atribuição de chamados a técnicos."""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..ai.classifier import classifier
from ..database import get_db
from ..models import Comment, KBArticle, Ticket, User
from ..schemas import (ClassificationOut, ClassifyIn, CommentIn, CommentOut, KBSuggestion, SelfResolveIn,
                       TicketCreate, TicketDetail, TicketOut, TicketUpdate)
from ..security import get_current_user, is_staff
from ..services import add_event, pick_technician, sla_info, suggest_articles

router = APIRouter(prefix="/api", tags=["Chamados"])


def to_out(ticket: Ticket, schema=TicketOut, **extra):
    out = schema.model_validate(ticket, from_attributes=True)
    out.sla_due_at, out.sla_breached = sla_info(ticket)
    for k, v in extra.items():
        setattr(out, k, v)
    return out


def get_ticket_for(db: Session, ticket_id: int, user: User) -> Ticket:
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(404, "Chamado não encontrado")
    if not is_staff(user) and ticket.requester_id != user.id:
        raise HTTPException(403, "Você só pode ver os próprios chamados")
    return ticket


# ---------- IA: pré-visualização enquanto o usuário digita ----------

@router.post("/ai/classify", response_model=ClassificationOut, tags=["IA"])
def classify_preview(data: ClassifyIn, _: User = Depends(get_current_user)):
    if len((data.title + data.description).strip()) < 5:
        raise HTTPException(422, "Texto insuficiente para classificar")
    c = classifier.classify(data.title, data.description)
    return ClassificationOut(
        category=c.category, category_confidence=c.category_confidence, category_scores=c.category_scores,
        priority=c.priority, priority_confidence=c.priority_confidence, priority_rule=c.priority_rule,
        needs_triage=c.needs_triage, model_version=c.model_version,
    )


@router.get("/ai/suggestions", response_model=List[KBSuggestion], tags=["IA"])
def suggestions_preview(q: str = Query(min_length=3), db: Session = Depends(get_db),
                        _: User = Depends(get_current_user)):
    category = classifier.classify(q, "").category if classifier.ready else None
    # Não contabiliza: a pré-visualização é chamada várias vezes enquanto o usuário digita.
    return suggest_articles(db, q, category=category)


# ---------- Chamados ----------

@router.post("/tickets", response_model=TicketDetail, status_code=201)
def create_ticket(data: TicketCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    c = classifier.classify(data.title, data.description)
    ticket = Ticket(
        title=data.title.strip(), description=data.description.strip(), requester_id=user.id,
        ai_category=c.category, ai_category_confidence=c.category_confidence,
        ai_priority=c.ai_priority, ai_priority_confidence=c.priority_confidence,
        ai_model_version=c.model_version, priority_rule=c.priority_rule,
        priority=c.priority,
    )
    if c.needs_triage:
        # Confiança baixa: a IA não decide; um técnico faz a triagem manual.
        ticket.status = "Triagem"
    else:
        ticket.status = "Aberto"
        ticket.category = c.category
    db.add(ticket)
    db.flush()

    add_event(db, ticket, user, (
        f"IA ({c.model_version}) sugeriu categoria '{c.category}' ({c.category_confidence:.0%}) "
        f"e prioridade '{c.ai_priority}'."
        + (f" Prioridade elevada para '{c.priority}' pela regra: {c.priority_rule}." if c.priority_rule else "")
        + (" Confiança baixa: enviado para triagem humana." if c.needs_triage else "")
    ))
    if not c.needs_triage:
        tech = pick_technician(db, ticket.category)
        if tech:
            ticket.assignee_id = tech.id
            ticket.assigned_at = datetime.utcnow()
            add_event(db, ticket, user, f"Atribuído automaticamente a {tech.name} (especialidade + menor carga).")
    db.commit()
    db.refresh(ticket)
    sugg = suggest_articles(db, f"{ticket.title} {ticket.description}", category=c.category, count_as_suggested=True)
    return to_out(ticket, TicketDetail, comments=[CommentOut.model_validate(x) for x in ticket.comments],
                  suggestions=[KBSuggestion(**s) for s in sugg])


@router.post("/tickets/self-resolved", response_model=TicketOut, status_code=201)
def self_resolved(data: SelfResolveIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Registra que o usuário resolveu sozinho com um artigo sugerido.
    Gera indicador de 'chamados evitados' e reforça o artigo."""
    article = db.get(KBArticle, data.kb_article_id)
    if article is None:
        raise HTTPException(404, "Artigo não encontrado")
    article.times_helpful += 1
    now = datetime.utcnow()
    ticket = Ticket(title=data.title.strip() or article.title, description=data.description or "(resolvido via base de conhecimento)",
                    requester_id=user.id, status="Resolvido", category=article.category, priority="Baixa",
                    self_resolved=True, kb_article_used_id=article.id, resolved_at=now,
                    resolution=f"Resolvido pelo próprio usuário com o artigo #{article.id}: {article.title}")
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return to_out(ticket)


@router.get("/tickets", response_model=List[TicketOut])
def list_tickets(
    status: Optional[str] = None, category: Optional[str] = None, priority: Optional[str] = None,
    assigned_to_me: bool = False, q: Optional[str] = None, include_self_resolved: bool = False,
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    query = select(Ticket).order_by(Ticket.created_at.desc())
    if not is_staff(user):
        query = query.where(Ticket.requester_id == user.id)
    if not include_self_resolved:
        query = query.where(Ticket.self_resolved.is_(False))
    if status:
        query = query.where(Ticket.status == status)
    if category:
        query = query.where(Ticket.category == category)
    if priority:
        query = query.where(Ticket.priority == priority)
    if assigned_to_me:
        query = query.where(Ticket.assignee_id == user.id)
    if q:
        like = f"%{q}%"
        query = query.where(or_(Ticket.title.ilike(like), Ticket.description.ilike(like)))
    return [to_out(t) for t in db.execute(query.limit(500)).scalars().all()]


@router.get("/tickets/{ticket_id}", response_model=TicketDetail)
def get_ticket(ticket_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ticket = get_ticket_for(db, ticket_id, user)
    sugg = suggest_articles(db, f"{ticket.title} {ticket.description}", category=ticket.category or ticket.ai_category)
    return to_out(ticket, TicketDetail, comments=[CommentOut.model_validate(x) for x in ticket.comments],
                  suggestions=[KBSuggestion(**s) for s in sugg])


@router.patch("/tickets/{ticket_id}", response_model=TicketOut)
def update_ticket(ticket_id: int, data: TicketUpdate, db: Session = Depends(get_db),
                  user: User = Depends(get_current_user)):
    ticket = get_ticket_for(db, ticket_id, user)
    changes = data.model_dump(exclude_unset=True)

    if not is_staff(user):
        # Solicitante só pode confirmar o fechamento ou reabrir um chamado resolvido.
        if set(changes) - {"status"} or changes.get("status") not in ("Fechado", "Aberto"):
            raise HTTPException(403, "Solicitantes só podem fechar ou reabrir chamados resolvidos")
        if ticket.status != "Resolvido":
            raise HTTPException(400, "O chamado ainda não foi resolvido")
        if changes["status"] == "Aberto":
            ticket.resolved_at = None
        ticket.status = changes["status"]
        add_event(db, ticket, user, "Solicitante " + ("confirmou a solução." if ticket.status == "Fechado" else "reabriu o chamado."))
        db.commit()
        db.refresh(ticket)
        return to_out(ticket)

    # ----- técnico / admin -----
    if "category" in changes or "priority" in changes:
        new_cat = changes.get("category", ticket.category)
        new_prio = changes.get("priority", ticket.priority)
        if new_cat != ticket.category or new_prio != ticket.priority:
            add_event(db, ticket, user, f"Classificação ajustada: categoria '{ticket.category or '-'}' → '{new_cat}', "
                                        f"prioridade '{ticket.priority}' → '{new_prio}'.")
        else:
            add_event(db, ticket, user, "Classificação da IA confirmada pelo técnico.")
        ticket.category, ticket.priority = new_cat, new_prio
        # Rótulo confirmado por humano: entra no próximo retreino.
        ticket.classification_reviewed = ticket.category is not None and ticket.priority is not None
        if ticket.status == "Triagem" and ticket.category:
            ticket.status = "Aberto"

    if "assignee_id" in changes:
        tech = db.get(User, changes["assignee_id"]) if changes["assignee_id"] else None
        if changes["assignee_id"] and (tech is None or tech.role not in ("tecnico", "admin")):
            raise HTTPException(400, "Responsável deve ser um técnico")
        ticket.assignee_id = tech.id if tech else None
        ticket.assigned_at = datetime.utcnow() if tech else None
        add_event(db, ticket, user, f"Atribuído a {tech.name}." if tech else "Atribuição removida.")
        if tech and ticket.status == "Triagem" and ticket.category:
            ticket.status = "Aberto"

    if "resolution" in changes:
        ticket.resolution = changes["resolution"]
    if "kb_article_used_id" in changes:
        art = db.get(KBArticle, changes["kb_article_used_id"]) if changes["kb_article_used_id"] else None
        if art:
            art.times_helpful += 1
        ticket.kb_article_used_id = art.id if art else None

    if "status" in changes and changes["status"] != ticket.status:
        new = changes["status"]
        if new == "Resolvido" and not (ticket.resolution or "").strip():
            raise HTTPException(400, "Informe a solução aplicada antes de resolver o chamado")
        if new in ("Em atendimento", "Aberto") and ticket.status == "Triagem" and not ticket.category:
            raise HTTPException(400, "Defina a categoria antes de tirar o chamado da triagem")
        add_event(db, ticket, user, f"Status alterado: '{ticket.status}' → '{new}'.")
        ticket.status = new
        if new in ("Resolvido", "Fechado"):
            ticket.resolved_at = ticket.resolved_at or datetime.utcnow()
        else:
            ticket.resolved_at = None
        if new == "Em atendimento" and ticket.assignee_id is None:
            ticket.assignee_id, ticket.assigned_at = user.id, datetime.utcnow()

    db.commit()
    db.refresh(ticket)
    return to_out(ticket)


@router.post("/tickets/{ticket_id}/auto-assign", response_model=TicketOut)
def auto_assign(ticket_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not is_staff(user):
        raise HTTPException(403, "Apenas técnicos")
    ticket = get_ticket_for(db, ticket_id, user)
    tech = pick_technician(db, ticket.category)
    if tech is None:
        raise HTTPException(400, "Nenhum técnico ativo disponível")
    ticket.assignee_id, ticket.assigned_at = tech.id, datetime.utcnow()
    add_event(db, ticket, user, f"Atribuído automaticamente a {tech.name} (especialidade + menor carga).")
    db.commit()
    db.refresh(ticket)
    return to_out(ticket)


@router.post("/tickets/{ticket_id}/comments", response_model=CommentOut, status_code=201)
def add_comment(ticket_id: int, data: CommentIn, db: Session = Depends(get_db),
                user: User = Depends(get_current_user)):
    ticket = get_ticket_for(db, ticket_id, user)
    comment = Comment(ticket_id=ticket.id, author_id=user.id, body=data.body.strip())
    db.add(comment)
    if not is_staff(user) and ticket.status == "Aguardando usuário":
        ticket.status = "Em atendimento"
    db.commit()
    db.refresh(comment)
    return comment
