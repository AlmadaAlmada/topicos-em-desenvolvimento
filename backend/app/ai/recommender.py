"""Sugestão de soluções da base de conhecimento.

Técnica: recuperação de informação por similaridade de cosseno entre
vetores TF-IDF (texto do chamado x título + problema dos artigos).
Não gera texto novo: só devolve artigos escritos e revisados por técnicos,
o que elimina o risco de "alucinação" de uma IA generativa.
"""
import threading
from typing import List, Optional, Sequence, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from ..config import KB_SIMILARITY_THRESHOLD
from .text import normalize


class KBRecommender:
    def __init__(self):
        self._lock = threading.Lock()
        self._stamp = None
        self._ids: List[int] = []
        self._categories: List[Optional[str]] = []
        self._vectorizer = None
        self._matrix = None

    def index(self, articles: Sequence, stamp) -> None:
        """(Re)constrói o índice se a base mudou. `articles` são KBArticle."""
        with self._lock:
            if stamp == self._stamp:
                return
            self._ids = [a.id for a in articles]
            self._categories = [a.category for a in articles]
            docs = [normalize(f"{a.title} {a.title} {a.problem}") for a in articles]
            if docs:
                self._vectorizer = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)
                self._matrix = self._vectorizer.fit_transform(docs)
            else:
                self._vectorizer, self._matrix = None, None
            self._stamp = stamp

    def search(
        self, text: str, top_k: int = 3, category: Optional[str] = None, min_score: float = KB_SIMILARITY_THRESHOLD
    ) -> List[Tuple[int, float]]:
        with self._lock:
            if self._vectorizer is None or not text.strip():
                return []
            query = self._vectorizer.transform([normalize(text)])
            sims = cosine_similarity(query, self._matrix)[0]
            results = []
            for idx, score in enumerate(sims):
                # Pequeno bônus quando a categoria prevista coincide com a do artigo.
                if category and self._categories[idx] == category:
                    score = score * 1.15
                if score >= min_score:
                    results.append((self._ids[idx], round(float(min(score, 1.0)), 4)))
            results.sort(key=lambda x: -x[1])
            return results[:top_k]


recommender = KBRecommender()
