"""Normalize graph identities, export the coder payload, and validate its contracts."""

from __future__ import annotations

import ast
from collections import Counter, defaultdict
from copy import deepcopy
import json

CALL_ATTRIBUTES = {"position", "required", "parameter_kind", "default"}


PROSE = {"constructor_description"}


CALLABLE_DESCRIPTION_KINDS = {"function", "method", "class"}


def normalize_graph(graph):
    nodes = {n["id"]: deepcopy(n) for n in graph["nodes"]}
    original_ids = set(nodes)
    edges = deepcopy(graph["edges"])
    for e in edges:
        if e["kind"] == "HAS_ARGUMENT":
            for key in CALL_ATTRIBUTES:
                if key in nodes[e["dst"]]:
                    e[key] = deepcopy(nodes[e["dst"]][key])
        if e["kind"] in {"HAS_ARGUMENT", "HAS_RETURN"}:
            description = nodes[e["dst"]].get("description")
            if description:
                e.setdefault("description", description)
    for n in nodes.values():
        for key in PROSE | {"snapshot", "caption", "sources"}:
            n.pop(key, None)
        if n["kind"] not in CALLABLE_DESCRIPTION_KINDS or not n.get("description"):
            n.pop("description", None)
        if n["kind"] == "argument":
            for key in CALL_ATTRIBUTES:
                n.pop(key, None)
    groups = defaultdict(list)
    for old, n in nodes.items():
        if n["kind"] == "argument" and n.get("annotation"):
            groups[(n["name"], n["annotation"])].append(old)
    representatives = {identity: identity for identity in nodes}
    for ids in groups.values():
        for identity in ids:
            representatives[identity] = min(ids)
    # A shared parameter has several consumers. Preserve the specific consumer
    # of an actual source transfer on the FEEDS endpoint, not on the shared port.
    bindings = defaultdict(list)
    for e in edges:
        if e["kind"] == "HAS_ARGUMENT":
            bindings[e["dst"]].append(e)
    rewritten = []
    for e in edges:
        if e["kind"] == "FEEDS" and e.get("role") == "argument":
            for binding in bindings[e["dst"]]:
                rewritten.append(
                    {
                        **e,
                        "dst": binding["src"],
                        "argument": nodes[e["dst"]]["name"],
                        "signature": binding.get("signature", 0),
                    }
                )
        else:
            rewritten.append(e)
    edges = [
        {**e, "src": representatives[e["src"]], "dst": representatives[e["dst"]]} for e in rewritten
    ]
    nodes = {identity: n for identity, n in nodes.items() if representatives[identity] == identity}
    original_ids = set(nodes)
    module_edges = set()
    for identity in sorted(original_ids):
        n = nodes[identity]
        if n["kind"] not in {"function", "class"}:
            continue
        module, _, local = identity.rpartition(".")
        if not module:
            raise ValueError("Public API has no module: " + identity)
        n["name"] = local
        components = module.split(".")
        for i in range(1, len(components) + 1):
            name = ".".join(components[:i])
            module_id = "module:" + name
            nodes.setdefault(module_id, {"id": module_id, "kind": "module", "name": name})
            if i > 1:
                parent = "module:" + ".".join(components[: i - 1])
                module_edges.add(("HAS_MODULE", parent, module_id))
        module_edges.add(("EXPORTS", "module:" + module, identity))
    edges += [{"kind": kind, "src": src, "dst": dst} for kind, src, dst in sorted(module_edges)]
    compact = {old: "n" + str(i) for i, old in enumerate(sorted(nodes))}
    id_map = {old: compact[representative] for old, representative in representatives.items()}
    id_map.update({old: compact[old] for old in nodes if old not in id_map})
    review_nodes = [{**n, "id": id_map[old]} for old, n in sorted(nodes.items())]
    review_edges = [{**e, "src": id_map[e["src"]], "dst": id_map[e["dst"]]} for e in edges]
    review_edges = list({json.dumps(e, sort_keys=True): e for e in review_edges}.values())
    candidates = [
        {"name": name, "annotation": annotation, "count": len(ids), "declarations": sorted(ids)}
        for (name, annotation), ids in groups.items()
        if len(ids) > 1
    ]
    candidates.sort(key=lambda x: (-x["count"], x["name"], x["annotation"]))
    return (
        {"schema": "source_object_types_review", "nodes": review_nodes, "edges": review_edges},
        id_map,
        candidates,
    )


SCHEMA = "source_object_types_coder"


NODE_PROPERTIES = frozenset({"name", "annotation", "constructor", "description"})


SIGNATURE_PROPERTIES = frozenset({"signature", "producer_signature"})


EDGE_PROPERTIES = frozenset(
    {
        "position",
        "required",
        "default",
        "parameter_kind",
        "source_path",
        "target_path",
        "conditional",
        "argument",
        "role",
        "description",
        "cases",
    }
)


DIAGNOSTIC_TYPE_MARKERS = ("unresolved[", "unresolved:", "recursive[")


MEMBER_RELATIONS = {"method": "HAS_METHOD", "property": "HAS_PROPERTY", "field": "HAS_FIELD"}


def diagnostic_type(text):
    return isinstance(text, str) and any(marker in text for marker in DIAGNOSTIC_TYPE_MARKERS)


def type_key(text):
    """Compare type spelling without changing tuple or generic argument order."""
    try:
        return ast.unparse(ast.parse(text, mode="eval").body)
    except SyntaxError:
        return text


def tuple_and_union_parts(text):
    """Expose fixed tuple positions and alternatives, never flatten a list."""
    try:
        root = ast.parse(text, mode="eval").body
    except SyntaxError:
        return

    def walk(node, path=(), condition=()):
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):

            def alternatives(n):
                if isinstance(n, ast.BinOp) and isinstance(n.op, ast.BitOr):
                    yield from alternatives(n.left)
                    yield from alternatives(n.right)
                else:
                    yield n

            for alternative in alternatives(node):
                value = ast.unparse(alternative)
                guard = condition + ("return alternative: " + value,)
                yield value, path, guard
                yield from walk(alternative, path, guard)
        elif isinstance(node, ast.Subscript) and ast.unparse(node.value) in {
            "builtins.tuple",
            "tuple",
        }:
            parts = node.slice.elts if isinstance(node.slice, ast.Tuple) else [node.slice]
            if any(isinstance(n, ast.Constant) and n.value is Ellipsis for n in parts):
                return
            for index, part in enumerate(parts):
                position = path + (index,)
                yield ast.unparse(part), position, condition
                yield from walk(part, position, condition)

    yield from walk(root)


def fold_returns(graph):
    """Share known result types and retain producer-specific ports on edges.

    Unknown full contracts keep their own ports. Actual value transfers move
    to their producer APIs, never to a shared type that would conflate producers.
    """
    nodes = {n["id"]: deepcopy(n) for n in graph["nodes"]}
    index = {type_key(n["name"]): n["id"] for n in nodes.values() if n["kind"] == "type"}
    for edge in graph["edges"]:
        if edge["kind"] == "EXPORTS":
            module, api = nodes[edge["src"]], nodes[edge["dst"]]
            if module["kind"] == "module" and api["kind"] == "class":
                index[type_key(module["name"] + "." + api["name"])] = api["id"]
    owners = {}
    for edge in graph["edges"]:
        if edge["kind"] == "HAS_RETURN" and nodes[edge["dst"]]["kind"] == "return":
            owners.setdefault(edge["dst"], []).append(edge)
    cursor = 0

    def shared_type(text):
        nonlocal cursor
        key = type_key(text)
        if key not in index:
            while "t" + str(cursor) in nodes:
                cursor += 1
            identity = "t" + str(cursor)
            cursor += 1
            nodes[identity] = {"id": identity, "kind": "type", "name": key}
            index[key] = identity
        return index[key]

    replacements, bindings = {}, {}
    created_before = len(nodes)
    for port in list(nodes.values()):
        if port["kind"] == "return" and port.get("annotation"):
            owner = owners.get(port["id"], [])
            if len(owner) != 1:
                raise ValueError("Expected one producer for each analysis return port")
            target = shared_type(port["annotation"])
            replacements[port["id"]] = target
            bindings[port["id"]] = {
                "producer": owner[0]["src"],
                "signature": owner[0].get("signature", 0),
                "type_node": target,
                "type_expression": port["annotation"],
                "return_edge_attributes": {
                    k: deepcopy(v) for k, v in owner[0].items() if k not in {"kind", "src", "dst"}
                },
            }

    edges = []
    projected = set()
    # Full-value contracts and explicit tuple/alternative projections.
    for port, binding in bindings.items():
        edges.append(
            {
                "kind": "HAS_RETURN",
                "src": binding["producer"],
                "dst": binding["type_node"],
                "signature": binding["signature"],
                **binding["return_edge_attributes"],
            }
        )
        for text, path, guard in tuple_and_union_parts(binding["type_expression"]):
            target = shared_type(text)
            edge = {
                "kind": "HAS_RETURN",
                "src": binding["producer"],
                "dst": target,
                "signature": binding["signature"],
            }
            if path:
                edge["source_path"] = list(path)
            if guard:
                edge["conditional"] = "; ".join(guard)
            edges.append(edge)
            projected.add((binding["producer"], target, binding["signature"], tuple(path)))

    flows_rewritten = 0
    for source in graph["edges"]:
        edge = deepcopy(source)
        if edge["kind"] == "HAS_RETURN" and edge["dst"] in replacements:
            continue
        if edge["kind"] == "HAS_TYPE" and edge["src"] in replacements:
            binding = bindings[edge["src"]]
            if edge["dst"] == binding["type_node"] and not edge.get("source_path"):
                continue
            key = (
                binding["producer"],
                edge["dst"],
                binding["signature"],
                tuple(edge.get("source_path", [])),
            )
            if key in projected:
                continue
            edge.update(kind="HAS_RETURN", src=binding["producer"], signature=binding["signature"])
        elif edge["kind"] == "FEEDS" and edge["src"] in replacements:
            binding = bindings[edge["src"]]
            edge["src"] = binding["producer"]
            edge["producer_signature"] = binding["signature"]
            flows_rewritten += 1
        elif edge["src"] in replacements or edge["dst"] in replacements:
            raise ValueError("Unsupported relation on a removed return port: " + edge["kind"])
        edges.append(edge)
    nodes = {k: n for k, n in nodes.items() if k not in replacements}
    unique = {json.dumps(e, sort_keys=True): e for e in edges}
    result = {"schema": SCHEMA, "nodes": list(nodes.values()), "edges": list(unique.values())}
    return result, {
        "return_ports_shared": len(replacements),
        "shared_type_nodes_created": len(nodes) + len(replacements) - created_before,
        "incomplete_return_ports_retained": sum(n["kind"] == "return" for n in nodes.values()),
        "source_flows_retargeted_to_producer": flows_rewritten,
        "return_bindings": bindings,
    }


def without_signatures(graph):
    """Remove call-variant numbers, preserving all other facts and node IDs.

    This intentionally removes overload grouping; it does not select a preferred
    overload or invent a merged call. Only edges made identical by removing
    these two properties are deduplicated. Source analysis keeps its private
    call bindings until return folding is finished.
    """
    result = deepcopy(graph)
    removed = Counter()
    for item in result["nodes"] + result["edges"]:
        for key in SIGNATURE_PROPERTIES:
            if key in item:
                removed[key] += 1
                del item[key]
    original_count = len(result["edges"])
    result["edges"] = list(
        {json.dumps(edge, sort_keys=True): edge for edge in result["edges"]}.values()
    )
    return result, {
        "removed_signature_properties": dict(sorted(removed.items())),
        "identical_edges_deduplicated": original_count - len(result["edges"]),
    }


def validate(graph):
    if graph.get("schema") != SCHEMA:
        raise ValueError("Expected the source coder projection")
    ids = [n["id"] for n in graph["nodes"]]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate coder node IDs")
    ids = set(ids)
    nodes = {n["id"]: n for n in graph["nodes"]}

    def check_binding(value):
        if not isinstance(value, dict) or set(value) - {"name", "type", "constraints", "items"}:
            raise ValueError("Invalid binding value descriptor")
        if not isinstance(value.get("type"), str) or not value["type"]:
            raise ValueError("Binding values require an established type")
        if "constraints" in value:
            constraints = value["constraints"]
            if (
                not isinstance(constraints, dict)
                or not constraints
                or set(constraints) - {"ndim", "length"}
                or any(type(v) is not int or v < 0 for v in constraints.values())
            ):
                raise ValueError("Invalid binding array or container constraint")
        if "items" in value:
            items = value["items"] if isinstance(value["items"], list) else [value["items"]]
            if not items:
                raise ValueError("Empty binding item descriptors")
            for item in items:
                check_binding(item)

    for node in graph["nodes"]:
        if set(node) - NODE_PROPERTIES - {"id", "kind"}:
            raise ValueError("Analysis-only or unapproved node property")
        if "description" in node and node["kind"] not in {"function", "method", "class"}:
            raise ValueError("Parameter/return documentation must be on its API binding edge")
        if diagnostic_type(node.get("annotation")) or (
            node["kind"] == "type" and diagnostic_type(node.get("name"))
        ):
            raise ValueError("Analysis diagnostic embedded in a type")
    for edge in graph["edges"]:
        if set(edge) - EDGE_PROPERTIES - {"kind", "src", "dst"}:
            raise ValueError("Analysis-only or unapproved edge property")
        if "description" in edge and edge["kind"] not in {
            "HAS_ARGUMENT",
            "HAS_RETURN",
            "HAS_FIELD",
        }:
            raise ValueError(
                "Descriptions are supported only on argument, return and field bindings"
            )
        if edge["src"] not in ids or edge["dst"] not in ids:
            raise ValueError("Missing coder edge endpoint")
        if "cases" in edge:
            if edge["kind"] not in {"HAS_ARGUMENT", "HAS_RETURN"}:
                raise ValueError("Binding cases require an argument or return edge")
            if not isinstance(edge["cases"], list) or not edge["cases"]:
                raise ValueError("Empty binding cases")
            for case in edge["cases"]:
                if not isinstance(case, dict) or "name" in case:
                    raise ValueError("Invalid binding case")
                check_binding({k: v for k, v in case.items() if k != "when"})
                if "when" in case:
                    guard = case["when"]
                    if not isinstance(guard, dict) or not guard:
                        raise ValueError("Empty binding guard")
                    for name, value in guard.items():
                        if not isinstance(name, str) or not name.isidentifier():
                            raise ValueError("Binding guards use Python parameter names")
                        if edge["kind"] == "HAS_ARGUMENT" and name == nodes[edge["dst"]]["name"]:
                            raise ValueError("A binding guard cannot repeat its own argument")
                        check_binding(value)
        if edge["kind"] == "HAS_MEMBER":
            raise ValueError("Generic member edges must be classified before coder export")
        if edge["kind"] in MEMBER_RELATIONS.values():
            target_kind = nodes[edge["dst"]]["kind"]
            if (
                nodes[edge["src"]]["kind"] != "class"
                or MEMBER_RELATIONS.get(target_kind) != edge["kind"]
            ):
                raise ValueError("Class-member relationship does not match its endpoint kinds")


def project(graph):
    if graph.get("schema") not in {"source_object_types_review", SCHEMA}:
        raise ValueError("Normalize structural IDs and argument bindings before coder export")
    nodes, omitted_ids = [], set()
    node_fields, edge_fields = Counter(), Counter()
    omitted_annotations = []
    for original in graph["nodes"]:
        if original["kind"] == "type" and diagnostic_type(original.get("name")):
            omitted_ids.add(original["id"])
            continue
        node = {
            k: deepcopy(v) for k, v in original.items() if k in NODE_PROPERTIES | {"id", "kind"}
        }
        if node["kind"] not in {"function", "method", "class"}:
            node.pop("description", None)
        node_fields.update(set(original) - set(node))
        # Do not replace unknown fragments with invented concrete types or
        # silently present a subset of a union as an exhaustive return type.
        # Known HAS_TYPE alternatives and the unresolved return port remain.
        if diagnostic_type(node.get("annotation")):
            omitted_annotations.append(node["id"])
            node.pop("annotation")
        nodes.append(node)
    edges, omitted_edges = [], 0
    for original in graph["edges"]:
        if original["src"] in omitted_ids or original["dst"] in omitted_ids:
            omitted_edges += 1
            continue
        # Return folding must use the source call bindings before their numeric
        # identifiers are removed from the final coder/Neo4j graph.
        edge = {
            k: deepcopy(v)
            for k, v in original.items()
            if k in EDGE_PROPERTIES | SIGNATURE_PROPERTIES | {"kind", "src", "dst"}
        }
        edge_fields.update(set(original) - set(edge))
        edges.append(edge)
    result, folding = fold_returns({"schema": SCHEMA, "nodes": nodes, "edges": edges})
    result, signature_removal = without_signatures(result)
    kinds = {n["id"]: n["kind"] for n in result["nodes"]}
    member_edges_replaced = 0
    for edge in result["edges"]:
        if edge["kind"] == "HAS_MEMBER":
            relation = MEMBER_RELATIONS.get(kinds[edge["dst"]])
            if relation is None:
                raise ValueError("Unsupported class-member target kind: " + kinds[edge["dst"]])
            edge["kind"] = relation
            member_edges_replaced += 1
    validate(result)
    report = {
        "input_nodes": len(graph["nodes"]),
        "input_edges": len(graph["edges"]),
        "coder_nodes": len(result["nodes"]),
        "coder_edges": len(result["edges"]),
        "omitted_node_properties": dict(sorted(node_fields.items())),
        "omitted_edge_properties": dict(sorted(edge_fields.items())),
        "diagnostic_type_nodes_omitted": sorted(omitted_ids),
        "diagnostic_type_edges_omitted": omitted_edges,
        "incomplete_annotation_properties_omitted": omitted_annotations,
        "argument_and_component_positions_preserved": True,
        "call_variant_identifiers_in_payload": False,
        **signature_removal,
        "generic_member_edges_replaced": member_edges_replaced,
        "member_relations": dict(
            Counter(e["kind"] for e in result["edges"] if e["kind"] in MEMBER_RELATIONS.values())
        ),
        **folding,
        "retrieval_algorithm_changed": False,
        "source_analysis_modified": False,
    }
    return result, report
