"""Description search, structural expansion and source-derived API context."""

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re

import numpy as np

from .api_context import API_KINDS, build_records, compressed, facts_only

MODEL = "text-embedding-3-large"


@dataclass
class RetrievedGraph:
    fragment: dict
    payload: dict
    text: str
    rankings: list
    original_ids: dict

    @property
    def node_count(self):
        return len(self.fragment["nodes"])

    @property
    def edge_count(self):
        return len(self.fragment["edges"])


ASSETS = Path(__file__).with_name("assets")
TOP_K = 3
DEFINITIONS = {"HAS_ARGUMENT", "HAS_RETURN", "HAS_TYPE"}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def configuration():
    return {
        "payload_format": "api_contracts_with_dataflow",
        "top_k": TOP_K,
        "hops": 1,
        "expansion_policy": "FEEDS neighbors: argument, return and type definitions",
        "embedding_model": MODEL,
        "assets": {p.name: sha(p) for p in sorted(ASSETS.iterdir()) if p.is_file()},
    }


def expand(graph, seeds):
    selected, frontier = set(seeds), set()
    for edge in graph["edges"]:
        for a, b in (("src", "dst"), ("dst", "src")):
            if edge[a] in seeds:
                selected.add(edge[b])
                if edge["kind"] == "FEEDS":
                    frontier.add(edge[b])
    frontier -= seeds
    for edge in graph["edges"]:
        if edge["kind"] in DEFINITIONS:
            if edge["src"] in frontier:
                selected.add(edge["dst"])
            if edge["dst"] in frontier:
                selected.add(edge["src"])
    return {
        "schema": graph["schema"],
        "nodes": [n for n in graph["nodes"] if n["id"] in selected],
        "edges": [e for e in graph["edges"] if e["src"] in selected and e["dst"] in selected],
    }


def without_descriptions(value):
    if isinstance(value, dict):
        return {k: without_descriptions(v) for k, v in value.items() if k != "description"}
    if isinstance(value, list):
        return [without_descriptions(v) for v in value]
    return value


def render_context(fragment, graph, names):
    selected = {n["id"] for n in fragment["nodes"] if n["kind"] in API_KINDS}
    records = build_records(fragment, names, selected)
    records = facts_only(records)
    payload = without_descriptions(records)
    for source, target in zip(records["apis"], payload["apis"]):
        if source.get("description"):
            target["description"] = re.split(r"\n\s*\n", source["description"].strip(), maxsplit=1)[
                0
            ]
        for argument, output in zip(source.get("inputs", []), target.get("inputs", [])):
            if argument.get("description"):
                output["description"] = argument["description"]
    text = compressed(payload, graph=fragment)
    return payload, text


class GraphRetriever:
    def __init__(self, graph, names, ids, texts, vectors, queries):
        self.graph, self.names, self.ids = graph, names, list(ids)
        self.vectors = np.asarray(vectors, dtype=np.float64)
        self.query_vectors = dict(queries)
        nodes = {n["id"]: n for n in graph["nodes"]}
        if len(ids) != len(set(ids)) or len(ids) != len(texts):
            raise ValueError("Duplicate or incomplete API search records")
        for identity, text in zip(ids, texts):
            node = nodes[identity]
            if node["kind"] not in API_KINDS or text != node.get("description", ""):
                raise ValueError("API embeddings do not match graph descriptions")
        if self.vectors.ndim != 2 or len(self.vectors) != len(ids):
            raise ValueError("Invalid API embedding dimensions")
        norms = np.linalg.norm(self.vectors, axis=1)
        if not np.isfinite(self.vectors).all() or np.any(norms == 0):
            raise ValueError("Invalid API embeddings")
        self.normalized = self.vectors / norms[:, None]

    @classmethod
    def load(cls, expected=None):
        if expected is not None and expected != configuration():
            raise ValueError("Retrieval assets changed after the run was created")
        graph = json.loads((ASSETS / "api_graph.json").read_text())
        names = {v: k for k, v in json.loads((ASSETS / "api_names.json").read_text()).items()}
        if any(e["kind"] == "IS_VALID_INPUT_TO" for e in graph["edges"]):
            raise ValueError("This retrieval configuration uses source dataflow, not type links")
        with np.load(ASSETS / "procedure_embeddings.npz", allow_pickle=False) as data:
            queries = dict(zip(data["texts"].tolist(), data["vectors"]))
        with np.load(ASSETS / "api_embeddings.npz", allow_pickle=False) as data:
            return cls(
                graph, names, data["ids"].tolist(), data["texts"].tolist(), data["vectors"], queries
            )

    def retrieve(self, queries, *, query_vectors=None, client=None):
        queries = list(queries)
        if not queries:
            raise ValueError("At least one Procedure query is required")
        vectors = {**self.query_vectors, **(query_vectors or {})}
        missing = list(dict.fromkeys(q for q in queries if q not in vectors))
        if missing:
            if client is None:
                raise ValueError("An embedding client is required for new Procedure queries")
            response = client.embeddings.create(model=MODEL, input=missing)
            data = sorted(response.data, key=lambda item: item.index)
            if [item.index for item in data] != list(range(len(missing))):
                raise ValueError("Embedding response indices do not match the queries")
            vectors.update((q, item.embedding) for q, item in zip(missing, data))
            self.query_vectors.update({q: vectors[q] for q in missing})
        rankings, seeds = [], set()
        for query in queries:
            vector = np.asarray(vectors[query], dtype=np.float64)
            if (
                vector.shape != (self.vectors.shape[1],)
                or not np.isfinite(vector).all()
                or not np.linalg.norm(vector)
            ):
                raise ValueError("Invalid Procedure embedding")
            scores = self.normalized @ (vector / np.linalg.norm(vector))
            indices = np.argsort(-scores, kind="stable")[:TOP_K]
            hits = [{"id": self.ids[i], "cosine_similarity": float(scores[i])} for i in indices]
            rankings.append({"query": query, "top_3": hits})
            seeds.update(item["id"] for item in hits)
        fragment = expand(self.graph, seeds)
        payload, text = render_context(fragment, self.graph, self.names)
        return RetrievedGraph(
            fragment,
            payload,
            text,
            rankings,
            {n["id"]: self.names.get(n["id"], n.get("name", n["id"])) for n in fragment["nodes"]},
        )
