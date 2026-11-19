"""Static notebook value transfers into existing API argument contracts.

No notebook or library code is imported or executed. Library call results use
the source graph's existing return summaries. Notebook helpers are interpreted
as AST, with branch joins and zero/one abstract loop iterations. Evidence stays
outside the coder graph. This module never adds nominal compatibility edges.
"""

from __future__ import annotations

import ast
from collections import Counter
from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import re

from .source_graph import module_statements, stable
from .return_trace import Exit, ReturnTracer, Routine, State, Value, merge, missing, named


def notebook_source(path):
    """Combine cells without losing their notebook positions; never run magics."""
    data = json.loads(path.read_text())
    body, locations, errors = [], {}, []
    offset, cells = 0, 0
    for index, cell in enumerate(data.get("cells", [])):
        if cell.get("cell_type") != "code":
            continue
        cells += 1
        source = "".join(cell.get("source", []))
        lines = source.splitlines()
        for line in range(1, len(lines) + 1):
            locations[offset + line] = {"cell_index": index, "cell_line": line}
        try:
            tree = ast.parse(source)
        except SyntaxError as error:
            errors.append({"cell_index": index, "cell_line": error.lineno, "reason": error.msg})
            # No remaining cell may inherit stale bindings past an opaque cell.
            return None, locations, cells, errors
        ast.increment_lineno(tree, offset)
        body.extend(tree.body)
        offset += max(1, len(lines)) + 1
    tree = ast.Module(body=body, type_ignores=[])
    return tree, locations, cells, errors


class DemoTracer(ReturnTracer):
    """Reuse source expression semantics while treating library APIs as summaries."""

    def __init__(self, builder, graph):
        super().__init__(builder)
        self.source = builder.return_tracer
        self.fields = deepcopy(self.source.fields)
        self.api_nodes = {n["id"]: n for n in graph["nodes"]}
        self.arguments = {}
        for edge in graph["edges"]:
            if edge["kind"] == "HAS_ARGUMENT":
                self.arguments.setdefault((edge["src"], edge.get("signature", 0)), set()).add(
                    self.api_nodes[edge["dst"]]["name"]
                )
        self.calls, self.skipped = {}, Counter()
        self.demo_modules, self.globals = set(), {}
        self.top = None

    def register_helpers(self, body, module, parent):
        for node in body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                identity = parent + ".<locals>." + node.name + "@" + str(node.lineno)
                routine = Routine(identity, module, node, parent=parent)
                self.routines[identity] = routine
                self.by_node[id(node)] = routine
                self.register_helpers(node.body, module, identity)
            elif isinstance(node, ast.ClassDef):
                # Dynamic/local classes are not library API declarations.
                continue
            else:
                for key in ("body", "orelse", "finalbody"):
                    self.register_helpers(getattr(node, key, []), module, parent)
                for handler in getattr(node, "handlers", []):
                    self.register_helpers(handler.body, module, parent)

    def analyze(self, routine, bindings=None):
        if routine.module not in self.demo_modules:
            if routine.api not in self.api_nodes:
                return missing("library_callable_not_in_graph")
            result, _ = self.source.result(routine.node)
            # Keep only the return contract, not the API implementation's local
            # origins or example-independent internal value transfers.
            return Value(spec=result.spec, unknown=result.unknown)
        env = self.initial(routine)
        if routine.parent == self.top.key:
            parameters = {p.arg for p in self.parameters(routine)}
            env.update({k: v for k, v in self.globals.items() if k not in parameters})
        if bindings:
            env.update(bindings)
        identity = (routine.key, stable({k: v.fingerprint() for k, v in sorted(env.items())}))
        if any(key[0] == routine.key for key in self.stack):
            self.skipped["recursive_notebook_helper"] += 1
            return missing("recursive_notebook_helper")
        self.stack.add(identity)
        try:
            exits = self.block(routine.node.body, [Exit(State(env))], routine)
            values = [
                x.value if x.kind == "return" else Value(named("builtins.NoneType"))
                for x in exits
                if x.kind in {"normal", "return"}
            ]
            return merge(values)
        finally:
            self.stack.remove(identity)

    def block(self, body, exits, routine):
        for stmt in body:
            outcomes = []
            for item in exits:
                if item.kind != "normal":
                    outcomes.append(item)
                    continue
                if routine is self.top:
                    self.globals = dict(item.state.env)
                outcomes.extend(self.statement(stmt, item.state, routine))
            normal = [x for x in outcomes if x.kind == "normal"]
            exits = [x for x in outcomes if x.kind != "normal"]
            if normal:
                names = set().union(*(x.state.env for x in normal))
                env = {
                    name: merge(
                        [x.state.env.get(name, missing("not_bound_on_all_paths")) for x in normal]
                    )
                    for name in names
                }
                common = tuple(
                    g for g in normal[0].state.guards if all(g in x.state.guards for x in normal)
                )
                exits.append(Exit(State(env, common)))
        return exits

    def statement(self, stmt, state, routine):
        if isinstance(stmt, ast.ClassDef):
            out = State(dict(state.env), state.guards)
            out.env[stmt.name] = missing("notebook_class_not_an_api")
            self.skipped["notebook_class_definition"] += 1
            return [Exit(out)]
        return super().statement(stmt, state, routine)

    def expr(self, node, state, routine):
        if isinstance(node, ast.Attribute):
            base = self.expr(node.value, state, routine)
            if base.spec and base.spec.get("kind") == "union":
                parts = [x for x in base.spec["items"] if x != named("builtins.NoneType")]
                if parts and len(parts) != len(base.spec["items"]):
                    # Attribute access can only continue along the non-None
                    # paths. This does not promise the access cannot raise.
                    narrowed = replace(
                        base,
                        spec=parts[0] if len(parts) == 1 else {"kind": "union", "items": parts},
                    )
                    env = {**state.env, "__flow_receiver__": narrowed}
                    target = ast.copy_location(
                        ast.Attribute(
                            value=ast.Name(id="__flow_receiver__", ctx=ast.Load()),
                            attr=node.attr,
                            ctx=node.ctx,
                        ),
                        node,
                    )
                    result = super().expr(target, State(env, state.guards), routine)
                    return (
                        replace(result, symbol=self.graph.canonical(result.symbol))
                        if result.symbol
                        else result
                    )
        result = super().expr(node, state, routine)
        return (
            replace(result, symbol=self.graph.canonical(result.symbol)) if result.symbol else result
        )

    def valid_call(self, callee, node, state, routine, bound):
        """Reject unknown expansions and calls inconsistent with source signatures."""
        positional = 0
        for arg in node.args:
            if isinstance(arg, ast.Starred):
                value = self.expr(arg.value, state, routine)
                if not value.items:
                    return False
                positional += len(value.items)
            else:
                positional += 1
        if any(k.arg is None for k in node.keywords):
            return False
        args = callee.node.args
        params = list(args.posonlyargs) + list(args.args)
        if bound and params:
            params = params[1:]
        keys = [k.arg for k in node.keywords]
        if len(keys) != len(set(keys)):
            return False
        if positional > len(params) and args.vararg is None:
            return False
        names = [p.arg for p in params]
        posonly = {p.arg for p in args.posonlyargs}
        if set(keys) & (set(names[:positional]) | posonly):
            return False
        allowed = set(names) | {p.arg for p in args.kwonlyargs}
        if set(keys) - allowed and args.kwarg is None:
            return False
        required = len(params) - len(args.defaults)
        supplied = set(names[:positional]) | set(keys)
        if any(p.arg not in supplied for p in params[: max(0, required)]):
            return False
        return all(
            p.arg in supplied
            for p, default in zip(args.kwonlyargs, args.kw_defaults)
            if default is None
        )

    def call(self, node, state, routine):
        fn = self.expr(node.func, state, routine)
        symbol = self.graph.canonical(fn.symbol) if fn.symbol else None
        if symbol is None and fn.spec:
            specs = fn.spec["items"] if fn.spec["kind"] == "union" else [fn.spec]
            types = {s.get("name") if s["kind"] == "name" else s.get("base") for s in specs}
            if len(types) == 1:
                cls = next(iter(types))
                if cls and cls + ".__call__" in self.api_nodes:
                    target = ast.copy_location(
                        ast.Attribute(value=node.func, attr="__call__", ctx=ast.Load()), node.func
                    )
                    rewritten = ast.copy_location(
                        ast.Call(func=target, args=node.args, keywords=node.keywords), node
                    )
                    return self.call(rewritten, state, routine)
        candidates = self.by_symbol.get(symbol, [])
        constructor = symbol in self.classes
        if constructor:
            if self.api_nodes.get(symbol, {}).get("constructor") != "public":
                self.skipped["constructor_not_exported"] += 1
                return missing("constructor_not_exported")
            candidates = self.by_symbol.get(symbol + ".__init__", [])
        if candidates:
            bound = constructor or (
                isinstance(node.func, ast.Attribute) and candidates[0].owner is not None
            )
            if not any(self.valid_call(c, node, state, routine, bound) for c in candidates):
                self.skipped["ambiguous_or_invalid_call_signature"] += 1
                for value in [*node.args, *(k.value for k in node.keywords)]:
                    self.expr(
                        value.value if isinstance(value, ast.Starred) else value, state, routine
                    )
                return missing("ambiguous_or_invalid_call_signature")
        return super().call(node, state, routine)

    def capture_transfers(self, callee, bindings, node, state, caller):
        if caller.module not in self.demo_modules or callee.api not in self.api_nodes:
            return
        self.calls[
            stable(
                {
                    "module": caller.module,
                    "line": node.lineno,
                    "api": callee.api,
                    "signature": callee.variant,
                }
            )
        ] = {
            "module": caller.module,
            "line": node.lineno,
            "api": callee.api,
            "signature": callee.variant,
        }
        allowed = self.arguments.get((callee.api, callee.variant), set())
        filtered = {k: v for k, v in bindings.items() if k in allowed or k in {"self", "cls"}}
        super().capture_transfers(callee, filtered, node, state, caller)

    def trace(self, tree, module):
        self.demo_modules.add(module)
        self.graph.bindings[module] = {}
        for node in module_statements(tree.body):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.graph.bindings[module][alias.asname or alias.name.split(".")[0]] = (
                        alias.name if alias.asname else alias.name.split(".")[0]
                    )
            elif isinstance(node, ast.ImportFrom) and node.module:
                for alias in node.names:
                    if alias.name != "*":
                        self.graph.bindings[module][alias.asname or alias.name] = (
                            node.module + "." + alias.name
                        )
        top = ast.FunctionDef(
            name="__notebook__",
            args=ast.arguments(posonlyargs=[], args=[], kwonlyargs=[], kw_defaults=[], defaults=[]),
            body=tree.body,
            decorator_list=[],
            returns=None,
        )
        ast.fix_missing_locations(top)
        self.top = Routine(module + ".__notebook__", module, top)
        self.register_helpers(tree.body, module, self.top.key)
        self.globals = {}
        return self.analyze(self.top)


def augment_from_demos(builder, graph, demos):
    """Add only witnessed source transfers; retain every supporting source site."""
    result = deepcopy(graph)
    edges = {stable({k: v for k, v in e.items() if k != "basis"}): e for e in result["edges"]}
    before = len(edges)
    evidence, calls, notebooks = {}, [], []
    for path in sorted(Path(demos).glob("*.ipynb")):
        tree, locations, cells, errors = notebook_source(path)
        record = {
            "path": str(path),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "code_cells": cells,
            "parse_errors": errors,
        }
        notebooks.append(record)
        if tree is None:
            record["skipped"] = True
            continue
        tracer = DemoTracer(builder, graph)
        module = "demo." + re.sub(r"\W", "_", path.stem)
        tracer.trace(tree, module)
        record["recognized_api_calls"] = len(tracer.calls)
        record["analysis_boundaries"] = dict(tracer.skipped)
        nodes = tracer.api_nodes
        for call in tracer.calls.values():
            calls.append({**call, "path": str(path), **locations.get(call["line"], {})})
        for transfer in tracer.transfers.values():
            api = transfer["producer_api"]
            source = (
                api
                if nodes.get(api, {}).get("kind") in {"class", "property", "field"}
                else f"{api}::return:{transfer['producer_variant']}"
            )
            target = (
                transfer["consumer_api"]
                if transfer["role"] == "receiver"
                else f"{transfer['consumer_api']}::arg:{transfer['consumer_variant']}:{transfer['argument']}"
            )
            if source not in nodes or target not in nodes:
                continue
            edge = {"kind": "FEEDS", "src": source, "dst": target, "role": transfer["role"]}
            for key in ("source_path", "target_path"):
                if transfer.get(key):
                    edge[key] = transfer[key]
            identity = stable(edge)
            if identity not in edges:
                edges[identity] = {**edge, "basis": "demo_dataflow"}
            item = {
                **transfer,
                "path": str(path),
                "sha256": record["sha256"],
                **locations.get(transfer["line"], {}),
            }
            evidence.setdefault(identity, {"edge": edge, "sites": []})["sites"].append(item)
        builder.bindings.pop(module, None)
    result["edges"] = [edges[k] for k in sorted(edges)]
    result["schema"] = "source_object_types_with_guard_contracts_and_demo_flows"
    report = {
        "notebooks": notebooks,
        "recognized_api_calls": len(calls),
        "demo_transfer_relations": len(evidence),
        "new_FEEDS_edges": len(edges) - before,
        "already_present_relations": len(evidence) - (len(edges) - before),
        "api_nodes_added_from_demos": 0,
        "compatibility_edges_added": 0,
        "scientific_code_executed": False,
        "llm_calls": 0,
        "limitations": [
            "Static possible flows do not prove runtime execution or numerical validity.",
            "Library calls use existing source return summaries; opaque operator results remain unknown.",
            "Dynamic stars, dynamic keyword unpacking and unmodeled local classes are not guessed.",
            "Branches are joined and loops use zero/one abstract iterations; helper recursion is not expanded.",
            "Demo versions are not inferred from file names; checksums identify the exact local inputs.",
        ],
    }
    return result, report, list(evidence.values()), calls
