"""Classificação automática de categoria e prioridade de chamados.

Técnica: aprendizado supervisionado clássico.
- Representação: TF-IDF de palavras (1-2 gramas) + TF-IDF de caracteres
  (3-5 gramas, robusto a erros de digitação e variações de palavras).
- Modelo: Regressão Logística multiclasse (gera probabilidades, usadas
  como confiança para decidir se a sugestão é aplicada ou vai para triagem).
- Avaliação: validação cruzada estratificada (5 folds).

Escolha justificada: poucos dados disponíveis, necessidade de rodar
localmente (dados dos chamados não saem da organização), baixo custo,
treino em segundos e resultado explicável (pesos por termo).
"""
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import FeatureUnion, Pipeline

from ..config import AI_CONFIDENCE_THRESHOLD, MODEL_DIR
from .rules import apply_floor, priority_floor
from .text import ticket_text
from .training_data import SEED_TICKETS


def _build_pipeline() -> Pipeline:
    features = FeatureUnion([
        ("words", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=1)),
        ("chars", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True, min_df=1)),
    ])
    clf = LogisticRegression(C=20.0, max_iter=2000, class_weight="balanced")
    return Pipeline([("features", features), ("clf", clf)])


@dataclass
class Classification:
    category: str
    category_confidence: float
    category_scores: Dict[str, float]
    ai_priority: str
    priority_confidence: float
    priority: str  # após aplicar o piso das regras
    priority_rule: Optional[str]
    needs_triage: bool
    model_version: str


@dataclass
class TrainReport:
    version: str
    samples: int
    samples_from_tickets: int
    category_accuracy: float
    priority_accuracy: float


class TicketClassifier:
    def __init__(self):
        self._lock = threading.Lock()
        self.category_model: Optional[Pipeline] = None
        self.priority_model: Optional[Pipeline] = None
        self.version: Optional[str] = None

    # ---------- treino ----------

    @staticmethod
    def _cv_accuracy(texts: List[str], labels: List[str]) -> float:
        counts = np.unique(labels, return_counts=True)[1]
        folds = int(min(5, counts.min()))
        if folds < 2:
            return float("nan")
        cv = StratifiedKFold(n_splits=folds, shuffle=True, random_state=42)
        return float(cross_val_score(_build_pipeline(), texts, labels, cv=cv).mean())

    def train(self, extra: Optional[List[Tuple[str, str, str, str]]] = None) -> TrainReport:
        """Treina com a semente + chamados confirmados por humanos (extra)."""
        extra = extra or []
        data = list(SEED_TICKETS) + list(extra)
        texts = [ticket_text(t, d) for t, d, _, _ in data]
        cats = [c for _, _, c, _ in data]
        prios = [p for _, _, _, p in data]

        cat_acc = self._cv_accuracy(texts, cats)
        prio_acc = self._cv_accuracy(texts, prios)

        cat_model = _build_pipeline().fit(texts, cats)
        prio_model = _build_pipeline().fit(texts, prios)
        version = datetime.utcnow().strftime("v%Y%m%d-%H%M%S%f")[:-3]

        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {"category": cat_model, "priority": prio_model, "version": version},
            MODEL_DIR / f"model-{version}.joblib",
        )
        with self._lock:
            self.category_model, self.priority_model, self.version = cat_model, prio_model, version

        return TrainReport(version, len(data), len(extra), cat_acc, prio_acc)

    def load(self, version: str) -> bool:
        path = MODEL_DIR / f"model-{version}.joblib"
        if not path.exists():
            return False
        bundle = joblib.load(path)
        with self._lock:
            self.category_model = bundle["category"]
            self.priority_model = bundle["priority"]
            self.version = bundle["version"]
        return True

    @property
    def ready(self) -> bool:
        return self.category_model is not None

    # ---------- inferência ----------

    @staticmethod
    def _predict(model: Pipeline, text: str) -> Tuple[str, float, Dict[str, float]]:
        probs = model.predict_proba([text])[0]
        classes = list(model.classes_)
        best = int(np.argmax(probs))
        scores = {c: round(float(p), 4) for c, p in sorted(zip(classes, probs), key=lambda x: -x[1])}
        return classes[best], float(probs[best]), scores

    def classify(self, title: str, description: str) -> Classification:
        if not self.ready:
            raise RuntimeError("Modelo de classificação não carregado")
        text = ticket_text(title, description)
        with self._lock:
            category, cat_conf, cat_scores = self._predict(self.category_model, text)
            ai_prio, prio_conf, _ = self._predict(self.priority_model, text)
            version = self.version
        floor, reason = priority_floor(title, description)
        final_prio = apply_floor(ai_prio, floor)
        return Classification(
            category=category,
            category_confidence=round(cat_conf, 4),
            category_scores=cat_scores,
            ai_priority=ai_prio,
            priority_confidence=round(prio_conf, 4),
            priority=final_prio,
            priority_rule=reason if final_prio != ai_prio else None,
            needs_triage=cat_conf < AI_CONFIDENCE_THRESHOLD,
            model_version=version,
        )


classifier = TicketClassifier()
