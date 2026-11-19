"""Regras determinísticas de prioridade.

A IA sugere a prioridade, mas existem situações em que o erro do modelo
é caro demais (incidente de segurança, empresa inteira parada). Para esses
casos, regras explícitas e auditáveis estabelecem um PISO de prioridade:
elas podem elevar a sugestão da IA, nunca reduzi-la.
"""
import re
from typing import Optional, Tuple

from ..config import PRIORITIES
from .text import strip_accents

# (padrão regex sobre texto sem acento e minúsculo, prioridade mínima, motivo)
PRIORITY_FLOOR_RULES = [
    (r"\b(virus|ransomware|malware|invasao|invadid\w*|hacke\w*|phishing|vazamento|roubaram)\b",
     "Crítica", "Possível incidente de segurança"),
    (r"\b(todos (os )?(usuarios|computadores|funcionarios|colaboradores|do (setor|predio|andar))|"
     r"todos estao|toda a empresa|todo o (predio|andar|setor)|ninguem (consegue|da empresa)|"
     r"nenhum (computador|usuario|pedido))\b",
     "Crítica", "Impacto em vários usuários"),
    (r"\b(fora do ar|parad[oa]s?|caiu para todos)\b.*\b(empresa|setor|loja|vendas|producao)\b",
     "Crítica", "Operação do negócio parada"),
    (r"\b(nao consigo trabalhar|impedid[oa]|urgente|reuniao em \d+|prazo hoje|entregar hoje)\b",
     "Alta", "Usuário impedido de trabalhar / urgência declarada"),
]

_compiled = [(re.compile(p), prio, reason) for p, prio, reason in PRIORITY_FLOOR_RULES]


def priority_floor(title: str, description: str) -> Tuple[Optional[str], Optional[str]]:
    """Retorna (prioridade mínima, motivo) ou (None, None)."""
    text = strip_accents(f"{title} {description}".lower())
    best, reason = None, None
    for pattern, prio, why in _compiled:
        if pattern.search(text):
            if best is None or PRIORITIES.index(prio) > PRIORITIES.index(best):
                best, reason = prio, why
    return best, reason


def apply_floor(ai_priority: str, floor: Optional[str]) -> str:
    if floor is None:
        return ai_priority
    return max(ai_priority, floor, key=PRIORITIES.index)
