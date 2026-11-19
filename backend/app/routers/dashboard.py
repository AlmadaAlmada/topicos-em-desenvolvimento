"""Funcionalidade 6: painel de indicadores (cálculo determinístico, sem IA).

Indicadores são agregações exatas sobre o banco: usar IA aqui só traria
imprecisão. Inclui também indicadores de QUALIDADE DA IA (acurácia em
produção), que alimentam a decisão de retreinar o modelo.
"""
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import AI_CONFIDENCE_THRESHOLD, CATEGORIES, PRIORITIES, STATUSES
from ..database import get_db
from ..models import KBArticle, Ticket, User
from ..security import require_roles
from ..services import OPEN_STATUSES, sla_info

router = APIRouter(prefix="/api/dashboard", tags=["Painel de indicadores"])


def _hours(a: Optional[datetime], b: Optional[datetime]) -> Optional[float]:
    if a is None or b is None:
        return None
    return (b - a).total_seconds() / 3600


def _avg(values):
    values = [v for v in values if v is not None]
    return round(sum(values) / len(values), 2) if values else None


@router.get("")
def dashboard(days: int = 30, db: Session = Depends(get_db), _: User = Depends(require_roles("tecnico", "admin"))):
    since = datetime.utcnow() - timedelta(days=days)
    all_tickets = db.execute(select(Ticket).where(Ticket.created_at >= since)).scalars().all()
    tickets = [t for t in all_tickets if not t.self_resolved]
    deflected = len(all_tickets) - len(tickets)

    resolved = [t for t in tickets if t.resolved_at]
    with_sla = [t for t in resolved if t.priority]
    sla_ok = sum(1 for t in with_sla if not sla_info(t)[1])
    open_breached = sum(1 for t in tickets if t.status in OPEN_STATUSES and sla_info(t)[1])

    # Volume diário
    per_day = Counter(t.created_at.date().isoformat() for t in tickets)
    daily = []
    for i in range(days - 1, -1, -1):
        d = (datetime.utcnow() - timedelta(days=i)).date().isoformat()
        daily.append({"date": d, "count": per_day.get(d, 0)})

    # Por técnico
    techs = {u.id: u for u in db.execute(select(User).where(User.role.in_(["tecnico", "admin"]))).scalars()}
    per_tech = defaultdict(lambda: {"open": 0, "resolved": 0, "hours": []})
    for t in tickets:
        if t.assignee_id in techs:
            row = per_tech[t.assignee_id]
            if t.status in OPEN_STATUSES:
                row["open"] += 1
            if t.resolved_at:
                row["resolved"] += 1
                row["hours"].append(_hours(t.created_at, t.resolved_at))
    technicians = sorted(
        ({"id": tid, "name": techs[tid].name, "specialty": techs[tid].specialty, "open": r["open"],
          "resolved": r["resolved"], "avg_resolution_hours": _avg(r["hours"])} for tid, r in per_tech.items()),
        key=lambda x: (-x["resolved"], x["name"]),
    )

    # Qualidade da IA (somente chamados revisados por humanos)
    reviewed = [t for t in tickets if t.classification_reviewed and t.ai_category]
    cat_hits = sum(1 for t in reviewed if t.ai_category == t.category)
    prio_hits = sum(1 for t in reviewed if t.ai_priority == t.priority)
    triage = sum(1 for t in tickets if t.ai_category and (t.ai_category_confidence or 0) < AI_CONFIDENCE_THRESHOLD)
    confusion = Counter((t.ai_category, t.category) for t in reviewed if t.ai_category != t.category)

    kb_top = db.execute(select(KBArticle).order_by(KBArticle.times_helpful.desc()).limit(5)).scalars().all()

    return {
        "period_days": days,
        "totals": {
            "tickets": len(tickets),
            "open": sum(1 for t in tickets if t.status in OPEN_STATUSES),
            "in_triage": sum(1 for t in tickets if t.status == "Triagem"),
            "resolved": len(resolved),
            "unassigned": sum(1 for t in tickets if t.status in OPEN_STATUSES and t.assignee_id is None),
            "deflected_by_kb": deflected,
        },
        "times": {
            "avg_first_assignment_hours": _avg([_hours(t.created_at, t.assigned_at) for t in tickets]),
            "avg_resolution_hours": _avg([_hours(t.created_at, t.resolved_at) for t in resolved]),
        },
        "sla": {
            "resolved_within_sla_pct": round(100 * sla_ok / len(with_sla), 1) if with_sla else None,
            "open_breached": open_breached,
        },
        "by_status": {s: sum(1 for t in tickets if t.status == s) for s in STATUSES},
        "by_category": {c: sum(1 for t in tickets if t.category == c) for c in CATEGORIES},
        "by_priority": {p: sum(1 for t in tickets if t.priority == p) for p in PRIORITIES},
        "daily": daily,
        "technicians": technicians,
        "ai": {
            "reviewed": len(reviewed),
            "category_accuracy_pct": round(100 * cat_hits / len(reviewed), 1) if reviewed else None,
            "priority_accuracy_pct": round(100 * prio_hits / len(reviewed), 1) if reviewed else None,
            "low_confidence_pct": round(100 * triage / len(tickets), 1) if tickets else None,
            "top_confusions": [{"ai": a, "human": h, "count": n} for (a, h), n in confusion.most_common(5)],
        },
        "kb_top": [{"id": a.id, "title": a.title, "helpful": a.times_helpful, "suggested": a.times_suggested}
                   for a in kb_top],
    }
