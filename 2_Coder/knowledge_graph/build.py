"""Build the API graph from pinned Python sources, demos and C++ bindings."""

import argparse
import hashlib
import json
from pathlib import Path
import urllib.request

import numpy as np

from .binding_analysis import add_export_metadata, enrich_graph
from .retrieval import MODEL
from .demo_flow import augment_from_demos
from .graph_view import normalize_graph, project, validate
from .source_graph import Contracts, SourceGraph, augment, install_public_aliases

HERE = Path(__file__).resolve().parent


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def acquire(source):
    """Download only the pinned upstream files, checking each recorded digest."""
    inventory = read(HERE / "sources.json")
    for item in inventory["files"]:
        target = source / Path(item["file"]).relative_to("referenced_sources")
        if not target.exists():
            url = item["source"].replace(
                "https://github.com/", "https://raw.githubusercontent.com/"
            )
            url = url.replace("/blob/", "/")
            with urllib.request.urlopen(url, timeout=60) as response:
                content = response.read()
            if hashlib.sha256(content).hexdigest() != item["sha256"]:
                raise ValueError("Upstream source checksum mismatch: " + item["source"])
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        if hashlib.sha256(target.read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError("Local source checksum mismatch: " + str(target))
    write(source / "binding_sources.json", inventory)


def build(source, output):
    inventory = read(HERE / "sources.json")
    for item in inventory["files"]:
        path = source / Path(item["file"]).relative_to("referenced_sources")
        if hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError("Source checksum mismatch: " + str(path))
    builder = SourceGraph(source / "python")
    install_public_aliases(builder, source / "metadata/ufl/__init__.py", "ufl")
    for item in read(source / "binding_sources.json")["files"]:
        if item["role"] == "prepared_public_export_metadata":
            package = ".".join(Path(item["source_path"]).parts[1:-1])
            install_public_aliases(builder, source.parent / item["file"], package)
    graph = builder.build()
    analysis = Contracts(builder)
    analysis.run()
    graph, _, _ = augment(builder, graph, analysis)
    graph, _, _, _ = augment_from_demos(builder, graph, source / "demos")
    graph, _ = enrich_graph(builder, graph, source)
    graph, _ = add_export_metadata(builder, graph, source)
    graph, names, _ = normalize_graph(graph)
    graph, _ = project(graph)
    graph["edges"] = [e for e in graph["edges"] if e["kind"] != "IS_VALID_INPUT_TO"]
    validate(graph)
    output.mkdir(parents=True, exist_ok=True)
    write(output / "api_graph.json", graph)
    write(output / "api_names.json", names)
    print(json.dumps({"nodes": len(graph["nodes"]), "edges": len(graph["edges"])}))


def embed(output):
    """Index descriptions only; call contracts remain in the graph."""
    from common.client import client, require_credentials
    from codegen.cards import templates
    from codegen.runner import procedure

    require_credentials(client)
    graph = read(output / "api_graph.json")
    rows = [
        n
        for n in graph["nodes"]
        if n["kind"] in {"function", "class", "method", "property"} and n.get("description")
    ]
    rows.sort(key=lambda n: n["id"])

    def vectors(texts):
        result = []
        for start in range(0, len(texts), 64):
            batch = texts[start : start + 64]
            response = client.embeddings.create(model=MODEL, input=batch)
            items = sorted(response.data, key=lambda d: d.index)
            if [item.index for item in items] != list(range(len(batch))):
                raise ValueError("Embedding response does not match the batch")
            result.extend(item.embedding for item in items)
        return np.asarray(result, dtype=np.float64)

    texts = [n["description"] for n in rows]
    np.savez_compressed(
        output / "api_embeddings.npz",
        ids=np.array([n["id"] for n in rows]),
        texts=np.array(texts),
        vectors=vectors(texts),
    )
    queries = list(dict.fromkeys(q for text in templates().values() for q in procedure(text)))
    np.savez_compressed(
        output / "procedure_embeddings.npz",
        ids=np.array(queries),
        texts=np.array(queries),
        vectors=vectors(queries),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", type=Path, default=HERE / "referenced_sources")
    parser.add_argument("--output", type=Path, default=HERE / "assets")
    parser.add_argument("--download", action="store_true", help="Fetch pinned upstream sources")
    parser.add_argument(
        "--embed", action="store_true", help="Regenerate OpenAI description embeddings"
    )
    args = parser.parse_args()
    if args.download:
        acquire(args.sources.resolve())
    build(args.sources.resolve(), args.output.resolve())
    if args.embed:
        embed(args.output.resolve())


if __name__ == "__main__":
    main()
