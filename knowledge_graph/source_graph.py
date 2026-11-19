"""Parse source APIs and infer nominal argument contracts without executing them."""

from __future__ import annotations

import ast
from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass
import json
from pathlib import Path
import re
from .return_trace import ReturnTracer

BUILTINS = {
    "int",
    "float",
    "complex",
    "bool",
    "str",
    "bytes",
    "object",
    "type",
    "list",
    "tuple",
    "dict",
    "set",
    "frozenset",
    "None",
    "NoneType",
}


CONTAINERS = {
    "builtins.list",
    "builtins.tuple",
    "builtins.dict",
    "builtins.set",
    "builtins.frozenset",
    "collections.abc.Sequence",
    "collections.abc.Iterable",
    "collections.abc.Collection",
    "collections.abc.Mapping",
}


TYPING_ALIASES = {
    "List": "builtins.list",
    "Tuple": "builtins.tuple",
    "Dict": "builtins.dict",
    "Set": "builtins.set",
    "Sequence": "collections.abc.Sequence",
    "Iterable": "collections.abc.Iterable",
    "Collection": "collections.abc.Collection",
    "Mapping": "collections.abc.Mapping",
    "Callable": "collections.abc.Callable",
}


def stable(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def module_name(path):
    parts = list(path.with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def dotted(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = dotted(node.value)
        return parent + "." + node.attr if parent else None
    return None


def module_statements(body):
    """Include TYPE_CHECKING and guarded imports, but never callable locals."""
    for node in body:
        yield node
        if isinstance(node, (ast.If, ast.Try)):
            for key in ("body", "orelse", "finalbody"):
                yield from module_statements(getattr(node, key, []))
            for handler in getattr(node, "handlers", []):
                yield from module_statements(handler.body)


def documentation(node):
    """Split source docstrings so argument/return prose is stored once."""
    text = ast.get_docstring(node) or ""
    description, arguments, returns = [], {}, []
    section, current = None, None
    for line in text.splitlines():
        if line and not line[0].isspace():
            section = {"Args:": "args", "Arguments:": "args", "Returns:": "returns"}.get(line)
            current = None
            if section:
                continue
        if section == "args":
            match = re.match(r"^ {4}([*\w]+)(?:\s*\([^)]*\))?:\s*(.*)$", line)
            if match:
                current = match[1].lstrip("*")
                arguments[current] = match[2]
            elif current and line.strip():
                arguments[current] += " " + line.strip()
        elif section == "returns":
            if line.strip():
                returns.append(line.strip())
        else:
            description.append(line)
    return {
        "description": "\n".join(description).strip(),
        "arguments": arguments,
        "returns": " ".join(returns),
        "full": text,
    }


def deprecated(node):
    """Match deprecation of this declaration, not references to older APIs."""
    doc = ast.get_docstring(node) or ""
    flat = " ".join(doc.split())
    if re.match(r"^\(?Deprecated\b", flat, re.I):
        return True
    if re.search(r"\bThis (?:class|function|method|property) is deprecated\b", flat, re.I):
        return True
    for decorator in getattr(node, "decorator_list", []):
        target = decorator.func if isinstance(decorator, ast.Call) else decorator
        if (dotted(target) or "").split(".")[-1] == "deprecated":
            return True
    return False


def internal_constructor(node):
    flat = " ".join((ast.get_docstring(node) or "").lower().split())
    return (
        "initialiser is for internal use" in flat
        or "initializer is for internal use" in flat
        or "not using this class initialiser" in flat
    )


def class_fields(cls):
    """Find declared storage and instance writes without entering nested scopes.

    Slots and writes include private storage. A write through another object,
    a static/class method, or a nested function is not an instance declaration.
    Evidence remains attached to the owning class, not a same-name parameter.
    """
    fields = {}

    def add(name, node, basis, annotation=None, description=None):
        if name.startswith("__") and name.endswith("__"):
            return
        item = fields.setdefault(name, {"node": node, "annotation": None, "sites": []})
        if annotation is not None:
            item["annotation"] = (
                annotation
                if item["annotation"] is None
                else ast.BinOp(left=item["annotation"], op=ast.BitOr(), right=annotation)
            )
        if description:
            item["description"] = description
        item["sites"].append({"basis": basis, "line": node.lineno})

    def walk(node):
        yield node
        for child in ast.iter_child_nodes(node):
            if not isinstance(
                child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)
            ):
                yield from walk(child)

    for member in cls.body:
        if isinstance(member, ast.AnnAssign) and isinstance(member.target, ast.Name):
            add(member.target.id, member, "class_annotation", member.annotation)
        if isinstance(member, (ast.Assign, ast.AnnAssign)):
            targets = member.targets if isinstance(member, ast.Assign) else [member.target]
            if any(isinstance(t, ast.Name) and t.id == "__slots__" for t in targets):
                try:
                    slots = ast.literal_eval(member.value)
                except (TypeError, ValueError):
                    continue
                names = (
                    [slots]
                    if isinstance(slots, str)
                    else slots if isinstance(slots, (tuple, list, set, dict)) else []
                )
                for name in names:
                    if isinstance(name, str):
                        add(
                            name,
                            member,
                            "slots",
                            description=(
                                slots.get(name)
                                if isinstance(slots, dict) and isinstance(slots.get(name), str)
                                else None
                            ),
                        )
        if not isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        decorators = {
            (dotted(d.func if isinstance(d, ast.Call) else d) or "").split(".")[-1]
            for d in member.decorator_list
        }
        if decorators & {"staticmethod", "classmethod"}:
            continue
        positional = list(member.args.posonlyargs) + list(member.args.args)
        if not positional:
            continue
        receiver = positional[0].arg
        for statement in member.body:
            if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            for node in walk(statement):
                if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                    for target in targets:
                        for part in ast.walk(target):
                            if (
                                isinstance(part, ast.Attribute)
                                and isinstance(part.ctx, ast.Store)
                                and isinstance(part.value, ast.Name)
                                and part.value.id == receiver
                            ):
                                add(
                                    part.attr,
                                    part,
                                    "instance_assignment",
                                    (
                                        node.annotation
                                        if isinstance(node, ast.AnnAssign) and part is target
                                        else None
                                    ),
                                )
    return fields


class SourceGraph:
    def __init__(self, python_root):
        self.root = Path(python_root)
        self.trees, self.paths, self.bindings, self.definitions = {}, {}, {}, {}
        self.aliases, self.excluded, self.unresolved, self.evidence = {}, [], [], {}
        self.nodes, self.edges = {}, {}
        self.nominal_classes = set()
        for path in sorted(self.root.rglob("*.py")):
            module = module_name(path.relative_to(self.root))
            self.paths[module] = path
            self.trees[module] = ast.parse(path.read_text(), filename=str(path))
        self.index()

    def index(self):
        exports = defaultdict(list)
        for module, tree in self.trees.items():
            bindings = self.bindings[module] = {}
            for node in module_statements(tree.body):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        bindings[alias.asname or alias.name.split(".")[0]] = (
                            alias.name if alias.asname else alias.name.split(".")[0]
                        )
                elif isinstance(node, ast.ImportFrom):
                    parent = node.module or ""
                    if node.level:
                        package = (
                            module
                            if self.paths[module].name == "__init__.py"
                            else module.rsplit(".", 1)[0]
                        )
                        prefix = package.split(".")[: len(package.split(".")) - node.level + 1]
                        parent = ".".join(prefix + ([parent] if parent else []))
                    for alias in node.names:
                        if alias.name == "*":
                            self.unresolved.append(
                                {"module": module, "kind": "star_import", "from": parent}
                            )
                            continue
                        name = alias.asname or alias.name
                        target = parent + "." + alias.name
                        bindings[name] = target
                        if self.paths[module].name == "__init__.py" and not name.startswith("_"):
                            exports[target].append(module + "." + name)
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    bindings[node.name] = module + "." + node.name
                    self.definitions[module + "." + node.name] = (module, node)
                elif (
                    isinstance(node, ast.Assign)
                    and len(node.targets) == 1
                    and isinstance(node.targets[0], ast.Name)
                ):
                    # A direct qualified-name assignment is an alias; TypeVar,
                    # arbitrary calls and dynamically computed aliases are not.
                    target = dotted(node.value)
                    if target:
                        first, *tail = target.split(".")
                        if first in bindings:
                            bindings[node.targets[0].id] = ".".join([bindings[first], *tail])
        for implementation, spellings in exports.items():
            if implementation in self.definitions:
                public = min(spellings, key=lambda name: (name.count("."), len(name), name))
                self.aliases[implementation] = public
                for spelling in spellings:
                    if spelling != public:
                        self.aliases[spelling] = public
        for name, (_, node) in self.definitions.items():
            if isinstance(node, ast.ClassDef):
                self.nominal_classes.add(self.canonical(name))

    def canonical(self, name):
        seen = set()
        while name in self.aliases and name not in seen:
            seen.add(name)
            name = self.aliases[name]
        return name

    def resolve(self, spelling, module):
        first, *tail = spelling.split(".")
        if first in BUILTINS:
            name = "builtins." + ("NoneType" if first == "None" else first)
        elif first in self.bindings[module]:
            name = self.bindings[module][first]
        elif first in {
            "dolfinx",
            "ufl",
            "basix",
            "numpy",
            "typing",
            "collections",
            "mpi4py",
            "petsc4py",
        }:
            name = first
        else:
            event = {"module": module, "spelling": spelling, "reason": "unresolved_type_name"}
            if event not in self.unresolved:
                self.unresolved.append(event)
            return "unresolved:" + module + ":" + spelling
        name = ".".join([name, *tail])
        if name.startswith("typing.") and name.rsplit(".", 1)[-1] in TYPING_ALIASES:
            name = TYPING_ALIASES[name.rsplit(".", 1)[-1]]
        return self.canonical(name)

    def annotation(self, node, module):
        if node is None:
            return None
        if isinstance(node, ast.Constant):
            if isinstance(node.value, str):
                try:
                    return self.annotation(ast.parse(node.value, mode="eval").body, module)
                except SyntaxError:
                    return {"kind": "opaque", "text": node.value}
            if node.value is None:
                return {"kind": "name", "name": "builtins.NoneType"}
            return {"kind": "literal", "value": "..." if node.value is Ellipsis else node.value}
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            items = []
            for sub in (self.annotation(node.left, module), self.annotation(node.right, module)):
                items.extend(sub["items"] if sub["kind"] == "union" else [sub])
            return {
                "kind": "union",
                "items": sorted({stable(x): x for x in items}.values(), key=stable),
            }
        if isinstance(node, ast.Subscript):
            base = self.resolve(dotted(node.value) or ast.unparse(node.value), module)
            slices = node.slice.elts if isinstance(node.slice, ast.Tuple) else [node.slice]
            args = [self.annotation(x, module) for x in slices]
            if base in {"typing.Union", "typing.Optional"}:
                if base == "typing.Optional":
                    args.append({"kind": "name", "name": "builtins.NoneType"})
                return {"kind": "union", "items": sorted(args, key=stable)}
            return {"kind": "generic", "base": base, "items": args}
        if dotted(node):
            return {"kind": "name", "name": self.resolve(dotted(node), module)}
        return {"kind": "opaque", "text": ast.unparse(node)}

    @staticmethod
    def render(spec):
        if spec is None:
            return None
        kind = spec["kind"]
        if kind == "name":
            return spec["name"]
        if kind == "union":
            return " | ".join(SourceGraph.render(x) for x in spec["items"])
        if kind == "generic":
            return (
                spec["base"] + "[" + ", ".join(SourceGraph.render(x) for x in spec["items"]) + "]"
            )
        if kind == "literal":
            return "..." if spec["value"] == "..." else repr(spec["value"])
        if kind == "unknown":
            return "unresolved[" + spec["reason"] + "]"
        if kind == "recursive_ref":
            return "recursive[" + spec["name"] + "]"
        return spec["text"]

    @staticmethod
    def nominal(spec):
        if not spec:
            return False
        if spec["kind"] == "name":
            name = spec["name"]
            return not (
                name.startswith(("builtins.", "numpy.", "typing.", "collections.", "unresolved:"))
            )
        if spec["kind"] == "generic":
            if spec["base"] in CONTAINERS:
                return any(SourceGraph.nominal(x) for x in spec["items"])
            return not spec["base"].startswith(
                ("builtins.", "numpy.", "typing.", "collections.", "unresolved:")
            )
        return False

    def flow_variants(self, spec, *, project=False, path=()):
        if not spec:
            return
        if spec["kind"] == "union":
            for sub in spec["items"]:
                yield from self.flow_variants(sub, project=project, path=path)
        elif self.nominal(spec):
            yield spec, path
            if project and spec["kind"] == "generic" and spec["base"] not in CONTAINERS:
                # A specialized instance may enter an explicitly unparameterized
                # class input. Its complete specialization is retained as well.
                yield {"kind": "name", "name": spec["base"]}, path
            # A fixed return tuple can expose its individual objects. A list,
            # sequence or variadic tuple is never treated as a single item.
            if (
                project
                and spec["kind"] == "generic"
                and spec["base"] == "builtins.tuple"
                and not any(
                    x["kind"] == "literal" and x.get("value") == "..." for x in spec["items"]
                )
            ):
                for i, sub in enumerate(spec["items"]):
                    yield from self.flow_variants(sub, project=True, path=path + (i,))

    def node(self, identity, kind, **attrs):
        if identity not in self.nodes:
            self.nodes[identity] = {"id": identity, "kind": kind, **attrs}
        return identity

    def edge(self, kind, source, target, **attrs):
        value = {"kind": kind, "src": source, "dst": target, **attrs}
        self.edges[stable(value)] = value

    def type_node(self, spec):
        text = self.render(spec)
        identity = text if text in self.nominal_classes else "type:" + text
        if identity in self.nodes:
            return identity
        # Classes are inserted before the flow graph is built.
        return self.node(identity, "type", name=text, external=text not in self.nominal_classes)

    def location(self, module, node, **extra):
        return {
            "file": str(self.paths[module].relative_to(self.root.parent.parent)),
            "line": node.lineno,
            "end_line": node.end_lineno,
            **extra,
        }

    def parameters(self, identity, fn, module, docs, variant=0):
        args = fn.args
        positional = list(args.posonlyargs) + list(args.args)
        default_values = [None] * (len(positional) - len(args.defaults)) + list(args.defaults)
        entries = [
            (
                arg,
                "positional_only" if i < len(args.posonlyargs) else "positional_or_keyword",
                default,
            )
            for i, (arg, default) in enumerate(zip(positional, default_values))
        ]
        if args.vararg:
            entries.append((args.vararg, "var_positional", None))
        entries += [
            (arg, "keyword_only", default)
            for arg, default in zip(args.kwonlyargs, args.kw_defaults)
        ]
        if args.kwarg:
            entries.append((args.kwarg, "var_keyword", None))
        position = 0
        for arg, parameter_kind, default in entries:
            if arg.arg in {"self", "cls"}:
                continue
            key = f"{identity}::arg:{variant}:{arg.arg}"
            annotation = self.annotation(arg.annotation, module)
            attrs = {
                "name": arg.arg,
                "position": position,
                "parameter_kind": parameter_kind,
                "required": default is None
                and parameter_kind not in {"var_positional", "var_keyword"},
            }
            if default is not None:
                attrs["default"] = ast.unparse(default)
            if docs["arguments"].get(arg.arg):
                attrs["description"] = docs["arguments"][arg.arg]
            if annotation is not None:
                attrs["annotation"] = self.render(annotation)
            self.node(key, "argument", **attrs)
            self.edge("HAS_ARGUMENT", identity, key, signature=variant)
            self.evidence[key] = self.location(module, arg, annotation=annotation)
            if annotation is None:
                self.unresolved.append(
                    {"api": identity, "parameter": arg.arg, "reason": "missing_annotation"}
                )
            else:
                for spec, _ in self.flow_variants(annotation):
                    self.edge("IS_VALID_INPUT_TO", self.type_node(spec), key)
            position += 1

    def callable(self, identity, fn, module, kind, owner=None, variant=0):
        if deprecated(fn):
            self.excluded.append(
                {"api": identity, "reason": "deprecated", **self.location(module, fn)}
            )
            return
        docs = documentation(fn)
        self.node(identity, kind, name=fn.name, description=docs["description"])
        if owner:
            self.edge("HAS_MEMBER", owner, identity)
        if identity not in self.evidence:
            self.evidence[identity] = self.location(module, fn)
        if kind != "property":
            self.parameters(identity, fn, module, docs, variant)
        value, trace = self.return_tracer.result(fn)
        annotation = value.spec
        expressions = list(dict.fromkeys(x["expression"] for x in trace["return_sites"]))
        result_attrs = {
            "resolution": trace["resolution"],
            "expressions": expressions
            or [
                (
                    "None (implicit fallthrough)"
                    if trace.get("normal_fallthrough")
                    else "no normal return established"
                )
            ],
        }
        if trace.get("unresolved"):
            result_attrs["unresolved"] = trace["unresolved"]
        if kind == "property":
            self.nodes[identity].update(result_attrs)
            if annotation:
                self.nodes[identity]["annotation"] = self.render(annotation)
                self.producer(identity, annotation)
            else:
                self.unresolved.append({"api": identity, "reason": "property_body_type_unresolved"})
        else:
            key = f"{identity}::return:{variant}"
            attrs = {"description": docs["returns"]} if docs["returns"] else {}
            attrs.update(result_attrs)
            if annotation:
                attrs["annotation"] = self.render(annotation)
            self.node(key, "return", **attrs)
            self.edge("HAS_RETURN", identity, key, signature=variant)
            self.evidence[key] = self.location(
                module, fn, annotation=annotation, return_trace=trace
            )
            if annotation:
                self.producer(key, annotation)
            else:
                self.unresolved.append({"api": identity, "reason": "return_body_type_unresolved"})

    def producer(self, identity, annotation):
        for spec, path in self.flow_variants(annotation, project=True):
            attrs = {"source_path": list(path)} if path else {}
            if annotation["kind"] == "union":
                attrs["conditional"] = "matching runtime union alternative"
            self.edge("HAS_TYPE", identity, self.type_node(spec), **attrs)

    def build(self):
        self.return_tracer = ReturnTracer(self)
        self.return_tracer.run()
        active_classes = []
        for name, (module, cls) in sorted(self.definitions.items()):
            if not isinstance(cls, ast.ClassDef) or cls.name.startswith("_"):
                continue
            identity = self.canonical(name)
            if deprecated(cls):
                self.excluded.append(
                    {"api": identity, "reason": "deprecated", **self.location(module, cls)}
                )
                continue
            constructor = next(
                (x for x in cls.body if isinstance(x, ast.FunctionDef) and x.name == "__init__"),
                None,
            )
            allowed = constructor is not None and not internal_constructor(constructor)
            class_doc = documentation(cls)
            description = class_doc["description"]
            if not description and constructor is not None:
                description = documentation(constructor)["description"]
            self.node(
                identity,
                "class",
                name=cls.name,
                description=description,
                constructor="public" if allowed else "internal" if constructor else "not_declared",
            )
            self.evidence[identity] = self.location(module, cls)
            if description and not class_doc["description"]:
                self.evidence[identity]["description_source"] = self.location(module, constructor)
            active_classes.append((identity, module, cls, constructor, allowed))
        for identity, module, cls, constructor, allowed in active_classes:
            field_docs = documentation(cls)["arguments"]
            descriptors = {
                member.name
                for member in cls.body
                if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef))
                and self.return_tracer.is_property(member, module)
            }
            if allowed:
                docs = documentation(constructor)
                self.parameters(identity, constructor, module, docs)
                if docs["description"] and docs["description"] != self.nodes[identity].get(
                    "description"
                ):
                    self.nodes[identity]["constructor_description"] = docs["description"]
            elif constructor:
                self.excluded.append(
                    {
                        "api": identity + ".__init__",
                        "reason": "internal_constructor_only",
                        "class_retained": True,
                        **self.location(module, constructor),
                    }
                )
            for member in cls.body:
                if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)) and (
                    not member.name.startswith("_") or member.name == "__call__"
                ):
                    # Ignore property setters: they do not replace getter types.
                    if any(
                        (dotted(d) or "").endswith((".setter", ".deleter"))
                        for d in member.decorator_list
                    ):
                        continue
                    member_kind = (
                        "property" if self.return_tracer.is_property(member, module) else "method"
                    )
                    self.callable(
                        identity + "." + member.name, member, module, member_kind, identity
                    )
            for name, declaration in sorted(class_fields(cls).items()):
                key = identity + "." + name
                # An attribute served by a descriptor stays a property/method;
                # assigning it does not create a second API node of another kind.
                if key in self.nodes or name in descriptors:
                    continue
                annotation = self.annotation(declaration["annotation"], module)
                captured = self.return_tracer.fields.get(identity, {}).get(name)
                inferred = None
                if annotation is None and captured and captured.spec and not captured.unknown:
                    inferred = captured.spec
                spec = annotation or inferred
                self.node(
                    key, "field", name=name, **({"annotation": self.render(spec)} if spec else {})
                )
                field_description = field_docs.get(name) or declaration.get("description")
                self.edge(
                    "HAS_MEMBER",
                    identity,
                    key,
                    **({"description": field_description} if field_description else {}),
                )
                self.evidence[key] = self.location(
                    module,
                    declaration["node"],
                    annotation=annotation,
                    inferred_type=inferred,
                    field_sites=declaration["sites"],
                )
                if spec:
                    self.producer(key, spec)
        for name, (module, fn) in sorted(self.definitions.items()):
            if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)) and not fn.name.startswith(
                "_"
            ):
                self.callable(self.canonical(name), fn, module, "function")
        for identity, module, fn, variant in self.return_tracer.registered:
            if identity in self.nodes:
                self.callable(identity, fn, module, "function", variant=variant)
        self.usage_evidence = {}
        for transfer in self.return_tracer.transfers.values():
            api = transfer["producer_api"]
            variant = transfer["producer_variant"]
            source = (
                api
                if api in self.nodes and self.nodes[api]["kind"] in {"class", "property", "field"}
                else f"{api}::return:{variant}"
            )
            target = (
                transfer["consumer_api"]
                if transfer["role"] == "receiver"
                else f"{transfer['consumer_api']}::arg:{transfer['consumer_variant']}:{transfer['argument']}"
            )
            if source not in self.nodes or target not in self.nodes:
                continue
            attrs = {"role": transfer["role"], "basis": "source_dataflow"}
            if transfer["source_path"]:
                attrs["source_path"] = transfer["source_path"]
            if transfer.get("target_path"):
                attrs["target_path"] = transfer["target_path"]
            self.edge("FEEDS", source, target, **attrs)
            identity = stable({"src": source, "dst": target, **attrs})
            self.usage_evidence.setdefault(identity, []).append(transfer)
        # A reference to a deprecated class does not resurrect it as a type hub.
        removed = {x["api"] for x in self.excluded if x["reason"] == "deprecated"}
        self.edges = {
            k: e
            for k, e in self.edges.items()
            if e["src"] not in removed and e["dst"] not in removed
        }
        self.nodes = {k: v for k, v in self.nodes.items() if k not in removed}
        for edge in self.edges.values():
            assert edge["src"] in self.nodes and edge["dst"] in self.nodes, edge
        return {
            "schema": "source_declared_object_types",
            "nodes": [self.nodes[k] for k in sorted(self.nodes)],
            "edges": [self.edges[k] for k in sorted(self.edges)],
        }

    def object_transfers(self, graph):
        """Expand type hubs for review only; these pairs are not stored as edges."""
        owners = {
            e["dst"]: e["src"]
            for e in graph["edges"]
            if e["kind"] in {"HAS_ARGUMENT", "HAS_RETURN"}
        }
        producers = defaultdict(list)
        for node in graph["nodes"]:
            if node["kind"] == "class":
                producers[node["id"]].append((node["id"], []))
        for e in graph["edges"]:
            if e["kind"] == "HAS_TYPE":
                producers[e["dst"]].append((e["src"], e.get("source_path", [])))
        pairs = []
        for e in graph["edges"]:
            if e["kind"] != "IS_VALID_INPUT_TO":
                continue
            for source, path in producers[e["src"]]:
                type_node = self.nodes[e["src"]]
                type_name = type_node["id"] if type_node["kind"] == "class" else type_node["name"]
                pairs.append(
                    {
                        "producer_api": owners.get(source, source),
                        "produced_value": source,
                        "source_path": path,
                        "object_type": type_name,
                        "consumer_api": owners[e["dst"]],
                        "argument": self.nodes[e["dst"]]["name"],
                    }
                )
        return sorted(pairs, key=stable)


TRUE = ((),)


def contract_key(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def install_public_aliases(graph, metadata, package):
    """Use a package initializer as alias metadata, not executable input."""
    tree = ast.parse(metadata.read_text())
    exported = None
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets
        ):
            try:
                exported = set(ast.literal_eval(node.value))
            except (ValueError, TypeError):
                pass
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and not node.level:
            for alias in node.names:
                name = alias.asname or alias.name
                target = (node.module or "") + "." + alias.name
                if target in graph.definitions and (
                    name in exported if exported is not None else not name.startswith("_")
                ):
                    graph.aliases[target] = package + "." + name
    graph.nominal_classes = {
        graph.canonical(k) for k, (_, n) in graph.definitions.items() if isinstance(n, ast.ClassDef)
    }


@dataclass
class ContractRoutine:
    name: str
    module: str
    node: ast.FunctionDef
    owner: str | None = None

    @property
    def parameters(self):
        return (
            list(self.node.args.posonlyargs)
            + list(self.node.args.args)
            + list(self.node.args.kwonlyargs)
        )


class Contracts:
    """Infer an upper bound on nominal types along normal execution paths.

    A DNF clause is a conjunction of allowed-type sets. It remains a DNF in
    evidence if it cannot be faithfully expressed as a union annotation.
    Compatibility never promises shape, value or numerical preconditions.
    """

    def __init__(self, graph):
        self.graph = graph
        self.classes, self.routines, self.parents = {}, {}, {}
        self.mros, self.summaries, self.facts = {}, {}, {}
        self.diagnostics = set()
        for identity, (module, node) in graph.definitions.items():
            identity = graph.canonical(identity)
            if isinstance(node, ast.ClassDef):
                self.classes[identity] = (module, node)
                bases = []
                for base in node.bases:
                    target = base.value if isinstance(base, ast.Subscript) else base
                    name = self.symbol(target, module)
                    if name:
                        bases.append(name)
                self.parents[identity] = bases
                for member in node.body:
                    if isinstance(member, ast.FunctionDef):
                        self.routines[identity + "." + member.name] = ContractRoutine(
                            identity + "." + member.name, module, member, identity
                        )
            elif isinstance(node, ast.FunctionDef):
                self.routines[identity] = ContractRoutine(identity, module, node)

    def symbol(self, node, module):
        if isinstance(node, ast.Name):
            if node.id in self.graph.bindings[module]:
                return self.graph.canonical(self.graph.bindings[module][node.id])
            if node.id in {"isinstance", "int", "str", "bool", "float", "tuple", "list", "object"}:
                return "builtins." + node.id
        elif isinstance(node, ast.Attribute):
            parent = self.symbol(node.value, module)
            if parent:
                return self.graph.canonical(parent + "." + node.attr)
        return None

    def mro(self, cls, stack=()):
        if cls in self.mros:
            return self.mros[cls]
        if cls in stack:
            raise ValueError("Cyclic source inheritance: " + cls)
        bases = self.parents.get(cls, [])
        sequences = [list(self.mro(b, stack + (cls,))) for b in bases] + [list(bases)]
        result = [cls]
        while any(sequences):
            sequences = [s for s in sequences if s]
            head = next(
                (s[0] for s in sequences if not any(s[0] in t[1:] for t in sequences)), None
            )
            if head is None:
                raise ValueError("Inconsistent C3 source inheritance: " + cls)
            result.append(head)
            sequences = [[x for x in s if x != head] for s in sequences]
        self.mros[cls] = result
        return result

    def subtype(self, child, parent):
        return parent in self.mro(child)

    def method(self, cls, member):
        return next(
            (
                self.routines[c + "." + member]
                for c in self.mro(cls)
                if c + "." + member in self.routines
            ),
            None,
        )

    def normalize(self, clauses):
        out = set()
        for clause in clauses:
            constraints = set()
            for choices in clause:
                choices = set(choices)
                choices = {
                    x for x in choices if not any(x != y and self.subtype(x, y) for y in choices)
                }
                if choices:
                    constraints.add(tuple(sorted(choices)))
            constraints = {
                c
                for c in constraints
                if not any(
                    c != d and all(any(self.subtype(x, y) for y in c) for x in d)
                    for d in constraints
                )
            }
            out.add(tuple(sorted(constraints)))
        if () in out:
            return TRUE
        # If A implies B, A adds nothing to the disjunction A or B.
        out = {
            a
            for a in out
            if not any(
                a != b
                and all(
                    any(all(any(self.subtype(x, y) for y in bc) for x in ac) for ac in a)
                    for bc in b
                )
                for b in out
            )
        }
        return tuple(sorted(out))

    def declared(self, node, module):
        spec = self.graph.annotation(node, module)
        if spec is None:
            return TRUE
        parts = spec["items"] if spec["kind"] == "union" else [spec]
        # Parameterized collections and structural typing need other rules.
        if not all(p["kind"] == "name" for p in parts):
            return TRUE
        return self.normalize([((p["name"],),) for p in parts])

    def record(self, routine, origin, rule, node, **details):
        fact = {
            "routine": routine.name,
            "parameter": origin,
            "rule": rule,
            "module": routine.module,
            "line": node.lineno,
            **details,
        }
        self.facts.setdefault((routine.name, origin), {})[contract_key(fact)] = fact

    def initial(self, routine):
        states = [{"aliases": {p.arg: p.arg for p in routine.parameters}, "bounds": {}}]
        for p in routine.parameters:
            if p.annotation is not None:
                states = self.constrain(states, p.arg, self.declared(p.annotation, routine.module))
        return states

    def constrain(self, states, origin, dnf):
        out = []
        for state in states:
            for clause in dnf:
                child = deepcopy(state)
                child["bounds"][origin] = tuple(
                    sorted(set(child["bounds"].get(origin, ())) | set(clause))
                )
                out.append(child)
        return self.limit(out)

    def limit(self, states):
        unique = {contract_key(s): s for s in states}
        if len(unique) > 128:
            self.diagnostics.add("path_limit:nominal_contract_not_inferred")
            # A less constrained path is safe; preserve only common aliases.
            values = list(unique.values())
            aliases = {
                k: v
                for k, v in values[0]["aliases"].items()
                if all(s["aliases"].get(k) == v for s in values)
            }
            return [{"aliases": aliases, "bounds": {}}]
        return list(unique.values())

    def narrowed(self, states, test, truth, routine):
        if isinstance(test, ast.Constant):
            return states if bool(test.value) == truth else []
        if isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not):
            return self.narrowed(states, test.operand, not truth, routine)
        if isinstance(test, ast.BoolOp) and (
            (truth and isinstance(test.op, ast.And)) or (not truth and isinstance(test.op, ast.Or))
        ):
            for sub in test.values:
                states = self.narrowed(states, sub, truth, routine)
            return states
        if (
            truth
            and isinstance(test, ast.Call)
            and self.symbol(test.func, routine.module) == "builtins.isinstance"
            and len(test.args) == 2
            and isinstance(test.args[0], ast.Name)
        ):
            targets = test.args[1].elts if isinstance(test.args[1], ast.Tuple) else [test.args[1]]
            names = [self.symbol(t, routine.module) for t in targets]
            if all(names):
                out = []
                for state in states:
                    origin = state["aliases"].get(test.args[0].id)
                    if origin:
                        self.record(
                            routine, origin, "successful_isinstance_branch", test, types=names
                        )
                        out.extend(self.constrain([state], origin, ((tuple(sorted(names)),),)))
                    else:
                        out.append(state)
                return self.limit(out)
        return states

    def callee(self, call, routine):
        symbol = self.symbol(call.func, routine.module)
        constructor = symbol in self.classes
        bound = False
        if constructor:
            target = self.method(symbol, "__init__")
            bound = True
        else:
            target = self.routines.get(symbol)
            if (
                target is None
                and isinstance(call.func, ast.Attribute)
                and isinstance(call.func.value, ast.Name)
                and call.func.value.id == "self"
                and routine.owner
            ):
                target = self.method(routine.owner, call.func.attr)
                bound = True
        if target is None or any(isinstance(a, ast.Starred) for a in call.args):
            return None, {}
        params = list(target.node.args.posonlyargs) + list(target.node.args.args)
        if bound and params and params[0].arg in {"self", "cls"}:
            params = params[1:]
        mapping = {p.arg: a for p, a in zip(params, call.args)}
        mapping.update({k.arg: k.value for k in call.keywords if k.arg})
        return target, mapping

    def expression(self, node, states, routine):
        if node is None:
            return states
        if isinstance(
            node, (ast.Lambda, ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)
        ):
            # These bodies may execute zero times. They cannot impose a
            # necessary nominal bound on the caller's input by themselves.
            return states
        if isinstance(node, ast.IfExp):
            states = self.expression(node.test, states, routine)
            yes = self.expression(
                node.body, self.narrowed(deepcopy(states), node.test, True, routine), routine
            )
            no = self.expression(
                node.orelse, self.narrowed(deepcopy(states), node.test, False, routine), routine
            )
            return self.limit(yes + no)
        if isinstance(node, ast.BoolOp):
            # Short-circuiting: later terms are not guaranteed to execute.
            return self.expression(node.values[0], states, routine)
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.expr):
                states = self.expression(child, states, routine)
        if isinstance(node, ast.Call):
            target, mapping = self.callee(node, routine)
            if target:
                for formal, actual in mapping.items():
                    if not isinstance(actual, ast.Name):
                        continue
                    dnf = self.summaries.get((target.name, formal), TRUE)
                    if dnf == TRUE:
                        continue
                    out = []
                    for state in states:
                        origin = state["aliases"].get(actual.id)
                        if origin:
                            self.record(
                                routine,
                                origin,
                                "direct_argument_forwarding",
                                node,
                                callee=target.name,
                                callee_parameter=formal,
                            )
                            out.extend(self.constrain([state], origin, dnf))
                        else:
                            out.append(state)
                    states = self.limit(out)
        return states

    def block(self, statements, states, routine):
        completed = []
        for stmt in statements:
            if not states:
                break
            if isinstance(stmt, ast.Raise):
                states = []
            elif isinstance(stmt, ast.Return):
                completed += self.expression(stmt.value, states, routine)
                states = []
            elif isinstance(stmt, ast.If):
                states = self.expression(stmt.test, states, routine)
                normal, done = [], []
                for truth, body in [(True, stmt.body), (False, stmt.orelse)]:
                    a, b = self.block(
                        body, self.narrowed(deepcopy(states), stmt.test, truth, routine), routine
                    )
                    normal += a
                    done += b
                states = self.limit(normal)
                completed += done
            elif isinstance(stmt, (ast.Assign, ast.AnnAssign)):
                states = self.expression(stmt.value, states, routine)
                targets = stmt.targets if isinstance(stmt, ast.Assign) else [stmt.target]
                for state in states:
                    origin = (
                        state["aliases"].get(stmt.value.id)
                        if isinstance(stmt.value, ast.Name)
                        else None
                    )
                    for target in targets:
                        for n in ast.walk(target):
                            if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store):
                                state["aliases"][n.id] = origin
            elif isinstance(stmt, ast.Expr):
                states = self.expression(stmt.value, states, routine)
            elif isinstance(stmt, ast.Assert):
                states = self.narrowed(
                    self.expression(stmt.test, states, routine), stmt.test, True, routine
                )
            elif isinstance(stmt, (ast.For, ast.While, ast.Try, ast.With, ast.Match)):
                # Unknown exceptional, looping and context-manager paths may
                # return normally without executing their apparent guard.
                self.diagnostics.add("opaque_control_flow:" + routine.name + ":" + str(stmt.lineno))
                completed += deepcopy(states)
                assigned = {
                    n.id
                    for n in ast.walk(stmt)
                    if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)
                }
                for state in states:
                    for name in assigned:
                        state["aliases"][name] = None
        return states, completed

    def run(self):
        for cls in self.classes:
            self.mro(cls)
        for routine in self.routines.values():
            for p in routine.parameters:
                self.summaries[routine.name, p.arg] = self.declared(p.annotation, routine.module)
        for iteration in range(len(self.routines) + 1):
            updated = {}
            for routine in self.routines.values():
                live, completed = self.block(routine.node.body, self.initial(routine), routine)
                paths = live + completed
                for p in routine.parameters:
                    updated[routine.name, p.arg] = (
                        self.normalize([s["bounds"].get(p.arg, ()) for s in paths])
                        if paths
                        else TRUE
                    )
            if updated == self.summaries:
                self.iterations = iteration + 1
                return
            self.summaries = updated
        raise RuntimeError("Nominal input contracts did not reach a fixed point")

    def annotation(self, dnf):
        if not dnf or dnf == TRUE or any(len(clause) != 1 for clause in dnf):
            return None
        names = sorted({name for clause in dnf for name in clause[0]})
        parts = [{"kind": "name", "name": n} for n in names]
        return parts[0] if len(parts) == 1 else {"kind": "union", "items": parts}

    def accepts_type(self, dnf, actual):
        return bool(
            dnf
            and dnf != TRUE
            and any(
                all(any(self.subtype(actual, target) for target in choices) for choices in clause)
                for clause in dnf
            )
        )

    def proof(self, routine, parameter, visited=()):
        identity = (routine, parameter)
        if identity in visited:
            return []
        out = dict(self.facts.get(identity, {}))
        for fact in list(out.values()):
            if fact["rule"] == "direct_argument_forwarding":
                for item in self.proof(
                    fact["callee"], fact["callee_parameter"], visited + (identity,)
                ):
                    out[contract_key(item)] = item
        return [out[k] for k in sorted(out)]


def augment(builder, graph, analysis):
    builder.nodes = {n["id"]: deepcopy(n) for n in graph["nodes"]}
    builder.edges = {stable(e): deepcopy(e) for e in graph["edges"]}
    proofs = {}
    for child, parents in sorted(analysis.parents.items()):
        if child not in builder.nodes:
            continue
        for parent in parents:
            parent_node = builder.type_node({"kind": "name", "name": parent})
            builder.edge("IS_SUBCLASS_OF", child, parent_node)
    inferred = []
    for edge in list(builder.edges.values()):
        if edge["kind"] != "HAS_ARGUMENT" or edge.get("signature", 0) != 0:
            continue
        api, parameter = builder.nodes[edge["src"]], builder.nodes[edge["dst"]]
        if parameter.get("annotation"):
            continue
        routine = (
            analysis.method(api["id"], "__init__")
            if api["kind"] == "class"
            else analysis.routines.get(api["id"])
        )
        if routine is None:
            continue
        dnf = analysis.summaries.get((routine.name, parameter["name"]), TRUE)
        spec = analysis.annotation(dnf)
        if spec is None:
            continue
        proof = analysis.proof(routine.name, parameter["name"])
        parameter["annotation"] = builder.render(spec)
        parameter["type_basis"] = "source_guard_and_forwarding"
        record = {
            "api": api["id"],
            "argument_node": parameter["id"],
            "parameter": parameter["name"],
            "declared_annotation": None,
            "inferred_type": parameter["annotation"],
            "contract_dnf": dnf,
            "proof": proof,
        }
        inferred.append(record)
        proofs[parameter["id"]] = record
        for variant, _ in builder.flow_variants(spec):
            builder.edge("IS_VALID_INPUT_TO", builder.type_node(variant), parameter["id"])
    result = {
        "schema": "source_object_types_with_guard_contracts",
        "nodes": [builder.nodes[k] for k in sorted(builder.nodes)],
        "edges": [builder.edges[k] for k in sorted(builder.edges)],
    }
    return result, inferred, proofs


def allocation_boundaries(builder, analysis, graph):
    """Flag dynamic __new__ behavior that nominal constructor inference skips."""
    boundaries = {}
    for cls in analysis.classes:
        allocator = analysis.method(cls, "__new__")
        if allocator:
            alternatives = sorted(
                {
                    analysis.symbol(n.value.func, allocator.module)
                    for n in ast.walk(allocator.node)
                    if isinstance(n, ast.Return)
                    and isinstance(n.value, ast.Call)
                    and analysis.symbol(n.value.func, allocator.module) in analysis.classes
                }
            )
            boundaries[cls] = {
                "allocator": allocator.name,
                "module": allocator.module,
                "line": allocator.node.lineno,
                "conditional_constructor_targets": alternatives,
                "status": "allocation_branch_not_evaluated",
            }
    affected = []
    for node in graph["nodes"]:
        if node["kind"] != "return":
            continue
        annotation = node.get("annotation", "")
        matching = {c: b for c, b in boundaries.items() if c in annotation}
        if matching:
            node["resolution"] = "partially_inferred"
            reasons = node.setdefault("unresolved", [])
            for cls in matching:
                reason = "dynamic_allocation_not_resolved:" + cls
                if reason not in reasons:
                    reasons.append(reason)
            affected.append(
                {"return_node": node["id"], "nominal_type": annotation, "boundaries": matching}
            )
    return affected
