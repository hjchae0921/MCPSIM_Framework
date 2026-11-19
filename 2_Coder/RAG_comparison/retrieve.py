"""Print the document context presented to a coding stage, or its per-query ranking."""

import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

from codegen.cards import STAGES, templates
from codegen.ranking import rank_queries
from codegen.runner import procedure

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent / "knowledge_graph" / "assets"


def retrieve(queries):
    index = json.loads((HERE / "api_index.json").read_text())
    names = {row["embedding_id"]: name for name, row in index.items()}
    with np.load(ASSETS / "api_embeddings.npz", allow_pickle=False) as data:
        ids = data["ids"].tolist()
        if set(ids) != names.keys() or len(ids) != len(index):
            raise ValueError("Document candidates and API embeddings differ")
        if data["texts"].tolist() != [index[names[i]]["ranking_description"] for i in ids]:
            raise ValueError("Document index and embedded descriptions differ")
        vectors = np.asarray(data["vectors"], dtype=np.float64)
    with np.load(ASSETS / "procedure_embeddings.npz", allow_pickle=False) as data:
        query_vectors = dict(zip(data["texts"].tolist(), data["vectors"], strict=True))
    for query in queries:
        if query not in query_vectors:
            raise ValueError(f"No saved embedding for procedure: {query}")
    norms = np.linalg.norm(vectors, axis=1)
    if not np.isfinite(norms).all() or np.any(norms == 0):
        raise ValueError("Invalid API embedding")

    rankings = rank_queries(ids, vectors / norms[:, None], queries, query_vectors)
    selected = {}
    for row in rankings:
        for hit in row["top_3"]:
            name = names[hit["id"]]
            hit["api"] = name
            if name in selected:
                continue
            record = index[name]
            data = (HERE / record["chunk"]).read_bytes()
            if hashlib.sha256(data).hexdigest() != record["sha256"]:
                raise ValueError(f"Indexed document checksum mismatch: {name}")
            selected[name] = data.decode("utf-8").strip()
    return rankings, "\n\n".join(selected.values()) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, prog="python main.py rag-context")
    parser.add_argument("stage", choices=[name for name, _ in STAGES])
    parser.add_argument(
        "--rankings", action="store_true", help="Show ranked APIs and cosine scores"
    )
    args = parser.parse_args(argv)
    rankings, text = retrieve(procedure(templates()[args.stage]))
    sys.stdout.write(json.dumps(rankings, indent=2) + "\n" if args.rankings else text)
