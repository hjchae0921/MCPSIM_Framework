"""Cosine ranking shared by document and graph retrieval."""

import numpy as np

TOP_K = 3


def rank_queries(ids, normalized, queries, vectors):
    rankings = []
    for query in queries:
        vector = np.asarray(vectors[query], dtype=np.float64)
        norm = np.linalg.norm(vector)
        if vector.shape != (normalized.shape[1],) or not np.isfinite(vector).all() or not norm:
            raise ValueError("Invalid Procedure embedding")
        scores = normalized @ (vector / norm)
        indices = np.argsort(-scores, kind="stable")[:TOP_K]
        hits = [{"id": ids[i], "cosine_similarity": float(scores[i])} for i in indices]
        rankings.append({"query": query, "top_3": hits})
    return rankings
