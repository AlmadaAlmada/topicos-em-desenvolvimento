"""Configurações centrais do HelpDesk Inteligente.

Valores podem ser sobrescritos por variáveis de ambiente, o que permite
usar configurações diferentes em desenvolvimento, teste e produção.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_URL = os.getenv("HELPDESK_DATABASE_URL", f"sqlite:///{BASE_DIR / 'helpdesk.db'}")

# Em produção, SECRET_KEY obrigatoriamente vem do ambiente.
SECRET_KEY = os.getenv("HELPDESK_SECRET_KEY", "dev-secret-helpdesk-inteligente-trocar-em-producao")
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRATION_MINUTES = int(os.getenv("HELPDESK_TOKEN_MINUTES", "480"))

# Onde o modelo de IA treinado é salvo (versionado por data/hora).
MODEL_DIR = Path(os.getenv("HELPDESK_MODEL_DIR", str(BASE_DIR / "models")))

# Abaixo deste nível de confiança, a classificação da IA não é aplicada
# automaticamente: o chamado vai para triagem humana.
AI_CONFIDENCE_THRESHOLD = float(os.getenv("HELPDESK_AI_THRESHOLD", "0.45"))

# Similaridade mínima para um artigo da base de conhecimento ser sugerido.
KB_SIMILARITY_THRESHOLD = float(os.getenv("HELPDESK_KB_THRESHOLD", "0.12"))

CORS_ORIGINS = os.getenv("HELPDESK_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")

CATEGORIES = ["Hardware", "Software", "Rede", "Acesso", "E-mail", "Impressora"]
PRIORITIES = ["Baixa", "Média", "Alta", "Crítica"]
STATUSES = ["Triagem", "Aberto", "Em atendimento", "Aguardando usuário", "Resolvido", "Fechado"]
ROLES = ["solicitante", "tecnico", "admin"]

# SLA (horas) por prioridade: regra de negócio fixa, sem IA.
SLA_HOURS = {"Crítica": 4, "Alta": 8, "Média": 24, "Baixa": 72}
