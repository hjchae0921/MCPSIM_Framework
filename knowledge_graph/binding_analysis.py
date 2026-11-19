"""Join generic binding declarations to source-proven Python forwarding paths."""

from __future__ import annotations

import ast
from collections import defaultdict
from copy import deepcopy
import json

from .cpp_syntax import CppSource
from pathlib import Path


def annotation_compatible(annotation, value):
    """Reject overloads contradicted by an explicit primitive Python annotation."""
    try:
        expression = ast.parse(annotation, mode="eval").body
    except SyntaxError:
        return True

    def atoms(node):
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            return atoms(node.left) | atoms(node.right)
        text = ast.unparse(node)
        return {text if text.startswith("builtins.") else "builtins." + text}

    declared = atoms(expression)
    primitives = {
        "builtins.bool",
        "builtins.int",
        "builtins.float",
        "builtins.complex",
        "builtins.str",
        "builtins.bytes",
    }
    if not declared or not declared <= primitives:
        return True
    return bool(declared & set(value["type"].split(" | ")))


def py_symbol(node, module, builder):
    if isinstance(node, ast.Name):
        return builder.bindings[module].get(node.id, node.id)
    if isinstance(node, ast.Attribute):
        parent = py_symbol(node.value, module, builder)
        return parent + "." + node.attr if parent else None
    if isinstance(node, ast.Subscript):
        return py_symbol(node.value, module, builder)
    return None


def scoped_nodes(routine):
    """Do not mistake a nested callback's locals for the enclosing API's inputs."""

    def visit(node):
        yield node
        for child in ast.iter_child_nodes(node):
            if not isinstance(
                child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)
            ):
                yield from visit(child)

    for statement in routine.body:
        if not isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            yield from visit(statement)


def class_mapping(builder, syntax):
    native = {row["python"]: base for base, rows in syntax.registered_types.items() for row in rows}
    wrappers, fields = defaultdict(set), defaultdict(set)

    def cpp_types(annotation, module):
        return (
            {
                native[symbol]
                for node in ast.walk(annotation)
                if (symbol := py_symbol(node, module, builder)) in native
            }
            if annotation
            else set()
        )

    for identity, (module, cls) in builder.definitions.items():
        if not isinstance(cls, ast.ClassDef):
            continue
        public = builder.canonical(identity)
        for item in cls.body:
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                values = cpp_types(item.annotation, module)
                fields[public, item.target.id].update(values)
                wrappers[public].update(values)
            if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                annotations = {
                    arg.arg: cpp_types(arg.annotation, module)
                    for arg in item.args.posonlyargs + item.args.args + item.args.kwonlyargs
                }
                for assign in scoped_nodes(item):
                    if not isinstance(assign, ast.Assign) or not isinstance(assign.value, ast.Name):
                        continue
                    for target in assign.targets:
                        if (
                            isinstance(target, ast.Attribute)
                            and isinstance(target.value, ast.Name)
                            and target.value.id == "self"
                        ):
                            values = annotations.get(assign.value.id, set())
                            fields[public, target.attr].update(values)
                            wrappers[public].update(values)
    reverse = defaultdict(set)
    for public, values in wrappers.items():
        if len(values) == 1:
            reverse[next(iter(values))].add(public)
    overrides = {cpp: next(iter(values)) for cpp, values in reverse.items() if len(values) == 1}
    # Imported native enum/class aliases also establish public spellings.
    aliases = defaultdict(set)
    for module, bindings in builder.bindings.items():
        for name, target in bindings.items():
            if not name.startswith("_") and target in native:
                aliases[native[target]].add(module + "." + name)
    for cpp, spellings in aliases.items():
        if cpp not in overrides:
            overrides[cpp] = min(spellings, key=lambda x: (x.count("."), len(x), x))
    return overrides, fields, native


def enrich_graph(builder, graph, source):
    syntax = CppSource(source)
    names, fields, native = class_mapping(builder, syntax)
    records, unresolved = syntax.records(names)
    methods, functions = defaultdict(list), defaultdict(list)
    for record in records:
        if record["registration_kind"] not in {"def", "def_static"}:
            continue
        if record["owner_python"]:
            methods[record["owner_python"], record["binding"]].append(record)
        elif not record["owner"] and record["python_module"]:
            functions[record["python_module"] + "." + record["binding"]].append(record)
    nodes = {n["id"]: n for n in graph["nodes"]}
    known_symbols = set(native) | set(functions)
    known_symbols |= {
        ".".join(s.split(".")[:i]) for s in list(known_symbols) for i in range(1, len(s.split(".")))
    }
    args, positions = defaultdict(dict), defaultdict(dict)
    for edge in graph["edges"]:
        if edge["kind"] == "HAS_ARGUMENT":
            arg = nodes[edge["dst"]]
            args[edge["src"]][arg["name"]] = arg
            positions[edge["src"]][arg["name"]] = edge.get("position", arg.get("position", 0))
    evidence, bridge_unresolved, contracts = [], [], defaultdict(dict)
    routines = []
    for identity, (module, node) in builder.definitions.items():
        public = builder.canonical(identity)
        if isinstance(node, ast.FunctionDef):
            routines.append((public, module, node, None))
        elif isinstance(node, ast.ClassDef):
            routines.extend(
                (public if fn.name == "__init__" else public + "." + fn.name, module, fn, public)
                for fn in node.body
                if isinstance(fn, ast.FunctionDef)
            )
    for api, module, routine, owner in routines:
        if api not in nodes:
            continue
        public_args = args[api]
        annotations = {}
        for name, argument in public_args.items():
            try:
                expression = ast.parse(argument.get("annotation", ""), mode="eval")
                annotations[name] = {
                    ast.unparse(n)
                    for n in ast.walk(expression)
                    if isinstance(n, (ast.Name, ast.Attribute))
                }
            except SyntaxError:
                annotations[name] = set()
        origins = {name: {name} for name in public_args}
        symbols = defaultdict(set)
        arrays = set()
        body = list(scoped_nodes(routine))

        def symbol_set(node):
            if isinstance(node, ast.Name):
                return symbols.get(node.id, {builder.bindings[module].get(node.id, node.id)})
            if isinstance(node, ast.Attribute):
                return {p + "." + node.attr for p in symbol_set(node.value)}
            if isinstance(node, ast.Subscript):
                return symbol_set(node.value)
            return set()

        def origin(node):
            if isinstance(node, ast.Name):
                return origins.get(node.id, set())
            if isinstance(node, ast.Attribute):
                values = origin(node.value)
                result = set()
                for name in values:
                    for (wrapper, field), cpp in fields.items():
                        if cpp and field == node.attr and wrapper in annotations[name]:
                            result.add(name)
                return result
            if isinstance(node, ast.ListComp) and len(node.generators) == 1:
                loop = node.generators[0]
                if (
                    not loop.ifs
                    and isinstance(loop.target, ast.Name)
                    and isinstance(node.elt, ast.Attribute)
                    and isinstance(node.elt.value, ast.Name)
                    and node.elt.value.id == loop.target.id
                ):
                    values = origin(loop.iter)
                    return {
                        n
                        for n in values
                        if any(
                            cpp and field == node.elt.attr and wrapper in annotations[n]
                            for (wrapper, field), cpp in fields.items()
                        )
                    }
            return set()

        changed = True
        while changed:
            changed = False
            for assign in body:
                if not isinstance(assign, ast.Assign):
                    continue
                syms = symbol_set(assign.value) & known_symbols
                value_origins = origin(assign.value)
                if (
                    isinstance(assign.value, ast.Call)
                    and py_symbol(assign.value.func, module, builder)
                    in {"numpy.asarray", "numpy.array"}
                    and assign.value.args
                ):
                    value_origins = origin(assign.value.args[0])
                    arrays.update(value_origins)
                for target in assign.targets:
                    if not isinstance(target, ast.Name):
                        continue
                    old = (len(symbols[target.id]), len(origins.get(target.id, set())))
                    symbols[target.id].update(syms)
                    origins.setdefault(target.id, set()).update(value_origins)
                    changed |= old != (len(symbols[target.id]), len(origins[target.id]))

        for call in (n for n in body if isinstance(n, ast.Call)):
            candidates = []
            for symbol in symbol_set(call.func):
                if symbol in native:
                    public = names.get(native[symbol])
                    if public:
                        candidates.extend(methods[public, "__init__"])
                candidates.extend(functions.get(symbol, []))
            if (
                owner
                and isinstance(call.func, ast.Attribute)
                and isinstance(call.func.value, ast.Attribute)
            ):
                receiver = call.func.value
                if isinstance(receiver.value, ast.Name) and receiver.value.id == "self":
                    for cpp in fields.get((owner, receiver.attr), set()):
                        if cpp in names:
                            candidates.extend(methods[names[cpp], call.func.attr])
            if not candidates:
                continue
            if call.keywords or any(isinstance(v, ast.Starred) for v in call.args):
                bridge_unresolved.append(
                    {"api": api, "line": call.lineno, "reason": "keyword_or_star_forwarding"}
                )
                continue
            for record in candidates:
                if len(record["inputs"]) != len(call.args):
                    continue
                mapped = []
                for supplied, value in zip(call.args, record["inputs"]):
                    values = origin(supplied)
                    if len(values) != 1:
                        break
                    name = next(iter(values))
                    item = {"name": name, **deepcopy(value)}
                    if not annotation_compatible(public_args[name].get("annotation", ""), value):
                        break
                    if name in arrays and value["type"] == "numpy.ndarray":
                        annotation = public_args[name].get("annotation", "")
                        numeric = [
                            t for t in ("builtins.float", "builtins.complex") if t in annotation
                        ]
                        if value.get("constraints") and (
                            numeric or "ndarray" not in annotation.lower()
                        ):
                            break
                        item["type"] = " | ".join(["numpy.ndarray"] + numeric)
                    mapped.append(item)
                else:
                    direct_return = any(isinstance(n, ast.Return) and n.value is call for n in body)
                    if (not mapped and public_args) or len({v["name"] for v in mapped}) != len(
                        mapped
                    ):
                        continue
                    variant = {"inputs": sorted(mapped, key=lambda v: positions[api][v["name"]])}
                    if direct_return and record["return_value"]:
                        variant["returns"] = [record["return_value"]]
                    key = json.dumps(variant, sort_keys=True)
                    contracts[api][key] = variant
                    evidence.append(
                        {
                            "api": api,
                            "python_module": module,
                            "python_line": call.lineno,
                            "cpp_file": record["file"],
                            "cpp_line": record["line"],
                            "contract": variant,
                        }
                    )

    def informative(value):
        if isinstance(value, dict):
            return "constraints" in value or any(informative(v) for v in value.values())
        return isinstance(value, list) and any(informative(v) for v in value)

    retained = {}
    for api, variants in contracts.items():
        if len(variants) > 1 or any(informative(v) for v in variants.values()):
            retained[api] = variants
    edge_count = attach_binding_cases(graph, retained)
    return graph, {
        "contracts": evidence,
        "resolved_registrations": records,
        "unresolved": unresolved,
        "bridge_unresolved": bridge_unresolved,
        "cpp_signatures_resolved": len(records),
        "apis_enriched": len(retained),
        "call_combinations_resolved": sum(len(v) for v in retained.values()),
        "binding_edges_enriched": edge_count,
        "class_type_mapping": names,
        "structural_inventory": syntax.report,
        "scope": "Registration-grammar and source-declaration analysis over the full input corpus. Direct Python forwarding only; unresolved and non-exhaustive paths remain explicit.",
    }


def attach_binding_cases(graph, contracts):
    """Keep each port's constraints and its sibling-input guards on that binding edge."""
    nodes = {node["id"]: node for node in graph["nodes"]}
    changed = 0
    for edge in graph["edges"]:
        if edge["src"] not in contracts or edge["kind"] not in {"HAS_ARGUMENT", "HAS_RETURN"}:
            continue
        if edge["kind"] == "HAS_RETURN" and edge.get("source_path"):
            continue
        name = nodes[edge["dst"]].get("name") if edge["kind"] == "HAS_ARGUMENT" else None
        cases = {}
        for variant in contracts[edge["src"]].values():
            inputs = {
                item["name"]: {k: v for k, v in item.items() if k != "name"}
                for item in variant["inputs"]
            }
            values = [inputs[name]] if name in inputs else []
            if name is None:
                values = variant.get("returns", [])
            for value in values:
                guard = {k: v for k, v in inputs.items() if k != name}
                case = {**deepcopy(value), **({"when": deepcopy(guard)} if guard else {})}
                cases[json.dumps(case, sort_keys=True)] = case
        if cases:
            edge["cases"] = [cases[key] for key in sorted(cases)]
            changed += 1
    return changed


def add_export_metadata(builder, graph, source):
    """Join explicit initializer exports to existing API/type/module nodes only."""
    nodes = {n["id"]: n for n in graph["nodes"]}
    for node in list(nodes.values()):
        if node["kind"] not in {"function", "class"}:
            continue
        components = node["id"].split(".")[:-1]
        for size in range(1, len(components) + 1):
            name = ".".join(components[:size])
            identity = "module:" + name
            if identity not in nodes:
                nodes[identity] = {"id": identity, "kind": "module", "name": name}
                graph["nodes"].append(nodes[identity])
    by_name = {n.get("name"): n["id"] for n in graph["nodes"] if n["kind"] == "type"}
    by_name.update({identity: identity for identity in nodes})
    for node in graph["nodes"]:
        if node["kind"] in {"function", "class"}:
            by_name[node["id"]] = node["id"]
    evidence = []
    known = {(e["kind"], e["src"], e["dst"]) for e in graph["edges"]}
    inventory = json.loads((source / "binding_sources.json").read_text())
    for row in inventory["files"]:
        if "public_export_metadata" not in row["role"]:
            continue
        path = source.parent / row["file"]
        tree = ast.parse(path.read_text())
        package = ".".join(Path(row["source_path"]).parts[1:-1])
        exported = None
        for stmt in tree.body:
            if isinstance(stmt, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "__all__" for t in stmt.targets
            ):
                try:
                    exported = set(ast.literal_eval(stmt.value))
                except (ValueError, TypeError):
                    pass
        imports = [n for n in tree.body if isinstance(n, ast.ImportFrom) and not n.level]
        for stmt in imports:
            for alias in stmt.names:
                name = alias.asname or alias.name
                if name.startswith("_") or (exported is not None and name not in exported):
                    continue
                target = builder.canonical((stmt.module or "") + "." + alias.name)
                public = package + "." + name
                dst = by_name.get(target) or by_name.get(public)
                if dst is None and "module:" + target in nodes:
                    dst = "module:" + target
                if dst is None:
                    continue
                module_id = "module:" + package
                if module_id not in nodes:
                    graph["nodes"].append({"id": module_id, "kind": "module", "name": package})
                    nodes[module_id] = graph["nodes"][-1]
                edge = ("EXPORTS", module_id, dst)
                if edge not in known:
                    graph["edges"].append({"kind": edge[0], "src": edge[1], "dst": edge[2]})
                    known.add(edge)
                    evidence.append(
                        {
                            "file": row["file"],
                            "line": stmt.lineno,
                            "module": package,
                            "name": name,
                            "target": dst,
                        }
                    )
    return graph, evidence
