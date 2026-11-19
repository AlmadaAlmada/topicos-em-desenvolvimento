"""Pré-processamento de texto em português."""
import re
import unicodedata

# Lista curta de stopwords; palavras como "não", "todos" e "ninguém" são
# mantidas de propósito porque carregam informação de impacto/prioridade.
STOPWORDS = {
    "a", "o", "as", "os", "um", "uma", "uns", "umas", "de", "do", "da", "dos", "das",
    "em", "no", "na", "nos", "nas", "por", "para", "pra", "com", "e", "ou", "que",
    "se", "me", "meu", "minha", "meus", "minhas", "eu", "ele", "ela", "isso", "esse",
    "essa", "este", "esta", "ao", "aos", "à", "às", "mas", "mais", "foi", "ser", "ja",
    "tem", "estou", "esta", "estao", "sobre", "favor", "ola", "bom", "dia", "boa", "tarde",
}

_non_alnum = re.compile(r"[^a-z0-9@\s]")
_spaces = re.compile(r"\s+")


def strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(c for c in normalized if not unicodedata.combining(c))


# Sinônimos e grafias alternativas comuns em chamados.
SYNONYMS = [
    (re.compile(r"\bwi\s*-?\s*fi\b|\bwireless\b|\bwlan\b"), "wifi"),
    (re.compile(r"\be\s*-?\s*mails?\b"), "email"),
    (re.compile(r"\bnet\b"), "internet"),
    (re.compile(r"\bpc\b|\bdesktop\b|\bmaquina\b"), "computador"),
    (re.compile(r"\bnotebook\b|\blaptop\b"), "notebook"),
    (re.compile(r"\bsenhas?\b|\bpassword\b"), "senha"),
    (re.compile(r"\bimpress\w*\b"), "impressora"),
]


# Minimização de dados (LGPD): dados pessoais são substituídos por marcadores
# antes de qualquer processamento pela IA, portanto nunca entram no vocabulário
# do modelo salvo em disco.
PII_PATTERNS = [
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), " dadoemail "),
    (re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b"), " dadocpf "),
    (re.compile(r"(\+?55\s?)?\(?\d{2}\)?\s?9?\d{4}-?\d{4}\b"), " dadotelefone "),
]


def mask_pii(text: str) -> str:
    for pattern, repl in PII_PATTERNS:
        text = pattern.sub(repl, text)
    return text


def normalize(text: str) -> str:
    text = strip_accents(mask_pii(text or "").lower())
    for pattern, repl in SYNONYMS:
        text = pattern.sub(repl, text)
    text = _non_alnum.sub(" ", text)
    tokens = [t for t in _spaces.split(text) if t and t not in STOPWORDS]
    return " ".join(tokens)


def ticket_text(title: str, description: str) -> str:
    # O título é repetido para ter peso maior: costuma resumir o problema.
    return normalize(f"{title} {title} {description}")
