"""Compara técnicas candidatas para o classificador de chamados.

Uso:  python -m scripts.evaluate_model
Gera a tabela usada no relatório para justificar a escolha do modelo.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np  # noqa: E402
from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.metrics import classification_report, confusion_matrix  # noqa: E402
from sklearn.model_selection import StratifiedKFold, cross_val_predict, cross_val_score  # noqa: E402
from sklearn.naive_bayes import ComplementNB  # noqa: E402
from sklearn.pipeline import FeatureUnion, Pipeline  # noqa: E402
from sklearn.svm import LinearSVC  # noqa: E402
from sklearn.dummy import DummyClassifier  # noqa: E402

from app.ai.classifier import _build_pipeline  # noqa: E402
from app.ai.text import ticket_text  # noqa: E402
from app.ai.training_data import SEED_TICKETS  # noqa: E402


def words():
    return TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)


def words_chars():
    return FeatureUnion([
        ("w", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)),
        ("c", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True)),
    ])


CANDIDATES = {
    "Baseline (classe mais frequente)": lambda: Pipeline([("f", words()), ("m", DummyClassifier(strategy="most_frequent"))]),
    "TF-IDF palavras + Naive Bayes": lambda: Pipeline([("f", words()), ("m", ComplementNB())]),
    "TF-IDF palavras + Regressão Logística": lambda: Pipeline([("f", words()), ("m", LogisticRegression(C=20, max_iter=2000, class_weight="balanced"))]),
    "TF-IDF palavras+caracteres + SVM linear": lambda: Pipeline([("f", words_chars()), ("m", LinearSVC(C=1.0, class_weight="balanced"))]),
    "TF-IDF palavras+caracteres + Regressão Logística (escolhido)": _build_pipeline,
}


def main():
    texts = [ticket_text(t, d) for t, d, _, _ in SEED_TICKETS]
    targets = {
        "categoria": [c for _, _, c, _ in SEED_TICKETS],
        "prioridade": [p for _, _, _, p in SEED_TICKETS],
    }
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    print(f"Amostras: {len(texts)}\n")
    for target, y in targets.items():
        print(f"=== Alvo: {target} ===")
        for name, factory in CANDIDATES.items():
            scores = cross_val_score(factory(), texts, y, cv=cv)
            print(f"{name:<62} acurácia = {scores.mean():.3f} ± {scores.std():.3f}")
        print()

    y = targets["categoria"]
    pred = cross_val_predict(_build_pipeline(), texts, y, cv=cv)
    labels = sorted(set(y))
    print("=== Relatório por classe (categoria, modelo escolhido) ===")
    print(classification_report(y, pred, labels=labels, digits=3, zero_division=0))
    print("Matriz de confusão (linhas = real, colunas = previsto):", labels)
    print(np.array(confusion_matrix(y, pred, labels=labels)))

    y = targets["prioridade"]
    pred = cross_val_predict(_build_pipeline(), texts, y, cv=cv)
    from app.ai.rules import apply_floor, priority_floor
    floored = [apply_floor(p, priority_floor(t, d)[0]) for p, (t, d, _, _) in zip(pred, SEED_TICKETS)]
    acc_ml = np.mean(np.array(pred) == np.array(y))
    acc_rules = np.mean(np.array(floored) == np.array(y))
    crit_idx = [i for i, v in enumerate(y) if v == "Crítica"]
    rec_ml = np.mean([pred[i] == "Crítica" for i in crit_idx])
    rec_rules = np.mean([floored[i] == "Crítica" for i in crit_idx])
    print("\n=== Prioridade: IA sozinha x IA + regras de piso ===")
    print(f"Acurácia IA sozinha:        {acc_ml:.3f}   Recall 'Crítica': {rec_ml:.3f}")
    print(f"Acurácia IA + regras:       {acc_rules:.3f}   Recall 'Crítica': {rec_rules:.3f}")


if __name__ == "__main__":
    main()
