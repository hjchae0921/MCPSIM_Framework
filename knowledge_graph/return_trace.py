"""Conservative source-body return and value-transfer analysis.

This module never executes a library function. It follows Python assignments,
calls, fields, branches, tuple projections, local helpers and finite recursive
input shapes. External/dynamic operations retain explicit unresolved evidence.
"""

import ast
import builtins
from dataclasses import dataclass, field, replace
import json


def key(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=repr)


def named(name):
    return {"kind": "name", "name": name}


def union(specs):
    flat = []
    for spec in specs:
        if spec:
            flat.extend(spec["items"] if spec["kind"] == "union" else [spec])
    values = sorted({key(x): x for x in flat}.values(), key=key)
    return values[0] if len(values) == 1 else {"kind": "union", "items": values} if values else None


def unresolved_components(spec):
    if not spec:
        return []
    if spec["kind"] in {"unknown", "recursive_ref"}:
        return [spec.get("reason", spec.get("name"))]
    if spec["kind"] == "name" and spec["name"].startswith("unresolved:"):
        return [spec["name"]]
    return [reason for child in spec.get("items", []) for reason in unresolved_components(child)]


@dataclass
class Value:
    spec: dict | None = None
    symbol: str | None = None
    origins: tuple = ()
    unknown: tuple = ()
    items: tuple = ()
    element: object = None
    literal: object = None
    literal_known: bool = False
    provenance: tuple = ()

    def fingerprint(self):
        return [
            self.spec,
            self.symbol,
            self.origins,
            self.unknown,
            self.literal if self.literal_known else "<nonliteral>",
            [v.fingerprint() for v in self.items],
            self.element.fingerprint() if self.element else None,
        ]


def missing(reason):
    return Value(unknown=(reason,))


def merge(values):
    if not values:
        return missing("no_return_value_established")
    origins, unknown, provenance = [], [], []
    for v in values:
        origins.extend(v.origins)
        unknown.extend(v.unknown)
        provenance.extend(v.provenance)
    symbols = {v.symbol for v in values}
    literal = all(v.literal_known for v in values) and len({key(v.literal) for v in values}) == 1
    lengths = {len(v.items) for v in values}
    items = (
        tuple(merge([v.items[i] for v in values]) for i in range(next(iter(lengths))))
        if len(lengths) == 1 and next(iter(lengths))
        else ()
    )
    return Value(
        union([v.spec for v in values]),
        next(iter(symbols)) if len(symbols) == 1 else None,
        tuple(dict.fromkeys(origins)),
        tuple(dict.fromkeys(unknown)),
        items,
        merge([v.element for v in values if v.element]) if any(v.element for v in values) else None,
        values[0].literal if literal else None,
        literal,
        tuple(dict.fromkeys(provenance)),
    )


@dataclass
class Routine:
    key: str
    module: str
    node: object
    owner: str | None = None
    api: str | None = None
    variant: int = 0
    parent: str | None = None
    closure: dict | None = None


@dataclass
class State:
    env: dict
    guards: tuple = ()


@dataclass
class Exit:
    state: State
    kind: str = "normal"
    value: Value = field(default_factory=Value)
    line: int | None = None
    column: int | None = None


class ReturnTracer:
    def __init__(self, graph):
        self.graph = graph
        self.routines, self.by_node, self.by_symbol = {}, {}, {}
        self.classes, self.fields, self.properties = {}, {}, {}
        self.members, self.registered = {}, []
        self.cache, self.stack, self.contexts, self.transfers = {}, set(), {}, {}
        self.capture_fields = False
        self._index()

    def _index(self):
        counters = {}

        def visit(body, module, owner=None, parent=None):
            for node in body:
                if isinstance(node, ast.ClassDef):
                    identity = self.graph.canonical(module + "." + node.name)
                    self.classes[identity] = (module, node)
                    self.fields[identity] = {}
                    for member in node.body:
                        if isinstance(member, ast.AnnAssign) and isinstance(
                            member.target, ast.Name
                        ):
                            self.fields[identity][member.target.id] = Value(
                                self.graph.annotation(member.annotation, module)
                            )
                    visit(node.body, module, identity)
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    registered = next(
                        (
                            d.value
                            for d in node.decorator_list
                            if isinstance(d, ast.Attribute) and d.attr == "register"
                        ),
                        None,
                    )
                    api = (
                        self.graph.canonical(module + "." + node.name)
                        if owner is None and parent is None
                        else owner + "." + node.name if owner and parent is None else None
                    )
                    variant = 0
                    if registered is not None and parent is None:
                        api = self.symbol_name(registered, module)
                        variant = counters.get(api, 0) + 1
                        counters[api] = variant
                        self.registered.append((api, module, node, variant))
                    elif node.name.startswith("_") and node.name not in {"__init__", "__call__"}:
                        api = None
                    if node.name == "__init__" and owner:
                        api = owner
                    if any(
                        isinstance(d, ast.Attribute) and d.attr in {"setter", "deleter"}
                        for d in node.decorator_list
                    ):
                        api = None
                    identity = (
                        (
                            parent + ".<locals>."
                            if parent
                            else owner + "." if owner else module + "."
                        )
                        + node.name
                        + "@"
                        + str(node.lineno)
                    )
                    routine = Routine(
                        identity,
                        module,
                        node,
                        owner if parent is None else None,
                        api,
                        variant,
                        parent,
                    )
                    self.routines[identity] = routine
                    self.by_node[id(node)] = routine
                    if parent is None:
                        symbol = (
                            api
                            if registered is not None
                            else (
                                owner + "." + node.name
                                if owner
                                else self.graph.canonical(module + "." + node.name)
                            )
                        )
                        self.by_symbol.setdefault(symbol, []).append(routine)
                        if owner:
                            self.members[(owner, node.name)] = routine
                            if self.is_property(node, module):
                                self.properties[(owner, node.name)] = routine
                    visit(node.body, module, None, identity)
                elif isinstance(node, (ast.If, ast.Try)):
                    for attr in ("body", "orelse", "finalbody"):
                        visit(getattr(node, attr, []), module, owner, parent)
                    for handler in getattr(node, "handlers", []):
                        visit(handler.body, module, owner, parent)

        for module, tree in self.graph.trees.items():
            visit(tree.body, module)

    def is_property(self, node, module):
        """Recognize imported descriptors, including qualified names and aliases."""
        return any(
            self.symbol_name(d, module) in {"builtins.property", "functools.cached_property"}
            for d in node.decorator_list
        )

    def symbol_name(self, node, module):
        if isinstance(node, ast.Name):
            if node.id in self.graph.bindings[module]:
                return self.graph.canonical(self.graph.bindings[module][node.id])
            if node.id in vars(builtins):
                return "builtins." + node.id
            return None
        if isinstance(node, ast.Attribute):
            base = self.symbol_name(node.value, module)
            return self.graph.canonical(base + "." + node.attr) if base else None
        return None

    def parameters(self, routine):
        return (
            list(routine.node.args.posonlyargs)
            + list(routine.node.args.args)
            + list(routine.node.args.kwonlyargs)
        )

    def initial(self, routine):
        env = dict(routine.closure or {})
        for arg in self.parameters(routine):
            if arg.arg in {"self", "cls"} and routine.owner:
                env[arg.arg] = Value(
                    named(routine.owner), symbol=routine.owner if arg.arg == "cls" else None
                )
            else:
                env[arg.arg] = Value(
                    self.graph.annotation(arg.annotation, routine.module),
                    unknown=() if arg.annotation else ("unannotated_parameter:" + arg.arg,),
                )
        return env

    @staticmethod
    def own_returns(node):
        def walk(body):
            for child in body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    continue
                if isinstance(child, ast.Return):
                    yield child
                for _, value in ast.iter_fields(child):
                    if isinstance(value, list):
                        yield from walk([x for x in value if isinstance(x, ast.AST)])
                    elif isinstance(value, ast.AST):
                        yield from walk([value])

        return list(walk(node.body))

    def analyze(self, routine, bindings=None):
        env = self.initial(routine)
        if bindings:
            env.update(bindings)
        cache_key = (routine.key, key({n: v.fingerprint() for n, v in sorted(env.items())}))
        declared = self.graph.annotation(routine.node.returns, routine.module)
        if cache_key in self.stack:
            return Value(
                declared or {"kind": "recursive_ref", "name": routine.key},
                unknown=("recursive_context:" + routine.key,),
            )
        if routine.parent is None and cache_key in self.cache and not self.capture_fields:
            return self.cache[cache_key]
        self.stack.add(cache_key)
        try:
            exits = self.block(routine.node.body, [Exit(State(env))], routine)
            returned = [x for x in exits if x.kind in {"return", "normal"}]
            values = [
                (
                    x.value
                    if x.kind == "return"
                    else Value(
                        named("builtins.NoneType"),
                        literal=None,
                        literal_known=True,
                        provenance=("implicit_none",),
                    )
                )
                for x in returned
            ]
            body = merge(values) if values else missing("no_normal_return")
            components = unresolved_components(body.spec)
            if components:
                body = replace(
                    body,
                    unknown=tuple(
                        dict.fromkeys(
                            body.unknown
                            + tuple("unresolved_type_component:" + x for x in components)
                        )
                    ),
                )
            if declared and all(
                isinstance(x, (ast.Pass, ast.Expr))
                and (not isinstance(x, ast.Expr) or isinstance(x.value, ast.Constant))
                for x in routine.node.body
            ):
                body = missing("declaration_stub_body")
            effective = declared or body.spec
            result = replace(body, spec=effective)
            sites = self.own_returns(routine.node)
            records = [
                {
                    "line": n.lineno,
                    "expression": ast.unparse(n.value) if n.value is not None else "None",
                    "column": n.col_offset,
                    "effective_in_context": any(
                        x.line == n.lineno and x.column == n.col_offset and x.kind == "return"
                        for x in exits
                    ),
                }
                for n in sites
            ]
            evidence = {
                "api": routine.api,
                "variant": routine.variant,
                "file": str(
                    self.graph.paths[routine.module].relative_to(self.graph.root.parent.parent)
                ),
                "line": routine.node.lineno,
                "declared_type": declared,
                "body_type": body.spec,
                "effective_type": effective,
                "unresolved": list(body.unknown),
                "provenance": list(body.provenance),
                "return_sites": records,
                "normal_fallthrough": any(x.kind == "normal" for x in exits),
                "all_normal_paths_resolved": not body.unknown,
                "resolution": (
                    (
                        "declared_body_partial"
                        if body.unknown and body.spec
                        else (
                            "declared_body_unresolved"
                            if body.unknown
                            else "declared_and_body_resolved"
                        )
                    )
                    if declared
                    else (
                        "body_inferred"
                        if body.spec and not body.unknown
                        else "partially_inferred" if body.spec else "unresolved"
                    )
                ),
            }
            self.contexts[cache_key] = evidence
            if routine.parent is None and not self.capture_fields:
                self.cache[cache_key] = result
            return result
        finally:
            self.stack.remove(cache_key)

    def state_key(self, state):
        return key({n: v.fingerprint() for n, v in sorted(state.env.items())})

    def block(self, body, exits, routine):
        for stmt in body:
            next_exits = []
            for item in exits:
                next_exits.extend(
                    self.statement(stmt, item.state, routine) if item.kind == "normal" else [item]
                )
            # Join equivalent abstract states, preserving all distinct exits.
            unique = {}
            for item in next_exits:
                identity = (
                    item.kind,
                    item.line,
                    item.column,
                    self.state_key(item.state),
                    key(item.value.fingerprint()),
                )
                unique.setdefault(identity, item)
            exits = list(unique.values())
        return exits

    def assign(self, target, value, state, routine):
        value = replace(
            value,
            provenance=tuple(
                dict.fromkeys(
                    value.provenance + ("assign:" + ast.unparse(target) + "@" + str(target.lineno),)
                )
            ),
        )
        if isinstance(target, ast.Name):
            state.env[target.id] = value
        elif isinstance(target, (ast.Tuple, ast.List)):
            for i, item in enumerate(target.elts):
                self.assign(item, self.project(value, i), state, routine)
        elif (
            isinstance(target, ast.Attribute)
            and isinstance(target.value, ast.Name)
            and target.value.id == "self"
            and routine.owner
            and self.capture_fields
        ):
            old = self.fields[routine.owner].get(target.attr)
            # Unknown assignments do not erase a declared field contract.
            if value.spec or old is None:
                self.fields[routine.owner][target.attr] = (
                    merge([old, value]) if old and old.spec else value
                )

    def statement(self, stmt, state, routine):
        state = State(dict(state.env), state.guards)
        if isinstance(stmt, ast.Return):
            value = (
                self.expr(stmt.value, state, routine)
                if stmt.value
                else Value(named("builtins.NoneType"), literal_known=True)
            )
            if value.spec is None and value.symbol and not value.unknown:
                value = replace(
                    value, unknown=("referenced_symbol_type_unresolved:" + value.symbol,)
                )
            return [Exit(state, "return", value, stmt.lineno, stmt.col_offset)]
        if isinstance(stmt, ast.Raise):
            if stmt.exc:
                self.expr(stmt.exc, state, routine)
            return [Exit(state, "raise", line=stmt.lineno)]
        if isinstance(stmt, ast.Assign):
            value = self.expr(stmt.value, state, routine)
            for target in stmt.targets:
                self.assign(target, value, state, routine)
        elif isinstance(stmt, ast.AnnAssign):
            value = self.expr(stmt.value, state, routine) if stmt.value else Value()
            annotation = self.graph.annotation(stmt.annotation, routine.module)
            self.assign(stmt.target, replace(value, spec=value.spec or annotation), state, routine)
        elif isinstance(stmt, ast.AugAssign):
            self.assign(
                stmt.target,
                merge(
                    [self.expr(stmt.target, state, routine), self.expr(stmt.value, state, routine)]
                ),
                state,
                routine,
            )
        elif isinstance(stmt, ast.Expr):
            self.expr(stmt.value, state, routine)
        elif isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            child = self.by_node[id(stmt)]
            child.closure = state.env
            state.env[stmt.name] = Value(symbol=child.key)
        elif isinstance(stmt, ast.If):
            outcomes = []
            for truth, body in [(True, stmt.body), (False, stmt.orelse)]:
                narrowed = self.narrow(stmt.test, state, routine, truth)
                if narrowed is not None:
                    outcomes += self.block(body, [Exit(narrowed)], routine)
            return outcomes
        elif isinstance(stmt, ast.Try):
            outcomes = self.block(stmt.body, [Exit(state)], routine)
            normal = self.block(stmt.orelse, [x for x in outcomes if x.kind == "normal"], routine)
            outcomes = [x for x in outcomes if x.kind != "normal"] + normal
            # Calls may raise before a later explicit return. Each handler is a
            # separate possible exception path, not assumed to execute in order.
            can_raise = any(
                isinstance(
                    x, (ast.Call, ast.Attribute, ast.Subscript, ast.Raise, ast.BinOp, ast.Assert)
                )
                for part in stmt.body
                for x in ast.walk(part)
            )
            for handler in stmt.handlers if can_raise else []:
                caught = State(
                    dict(state.env),
                    state.guards
                    + ("except:" + ast.unparse(handler.type) if handler.type else "except:*",),
                )
                if handler.name:
                    caught.env[handler.name] = missing("exception_object")
                outcomes += self.block(handler.body, [Exit(caught)], routine)
            if stmt.finalbody:
                final = []
                for item in outcomes:
                    for last in self.block(stmt.finalbody, [Exit(item.state)], routine):
                        final.append(
                            Exit(last.state, item.kind, item.value, item.line, item.column)
                            if last.kind == "normal"
                            else last
                        )
                outcomes = final
            return outcomes
        elif isinstance(stmt, (ast.For, ast.AsyncFor, ast.While)):
            loop = State(dict(state.env), state.guards + ("loop:" + str(stmt.lineno),))
            if isinstance(stmt, (ast.For, ast.AsyncFor)):
                self.assign(
                    stmt.target, self.element(self.expr(stmt.iter, loop, routine)), loop, routine
                )
                if isinstance(stmt.iter, (ast.List, ast.Tuple)) and not stmt.iter.elts:
                    return self.block(stmt.orelse, [Exit(state)], routine)
            else:
                test_value = self.expr(stmt.test, loop, routine)
                if test_value.literal_known and not bool(test_value.literal):
                    return self.block(stmt.orelse, [Exit(state)], routine)
            outcomes = self.block(stmt.body, [Exit(loop)], routine)
            # Zero iterations and an abstract iteration are distinct paths.
            literal_forever = (
                isinstance(stmt, ast.While)
                and isinstance(stmt.test, ast.Constant)
                and bool(stmt.test.value)
            )
            carried = ([] if literal_forever else [Exit(state)]) + [
                Exit(x.state)
                for x in outcomes
                if x.kind in {"normal", "continue"} and not literal_forever
            ]
            broken = [Exit(x.state) for x in outcomes if x.kind == "break"]
            return (
                [x for x in outcomes if x.kind in {"return", "raise"}]
                + broken
                + self.block(stmt.orelse, carried, routine)
            )
        elif isinstance(stmt, (ast.With, ast.AsyncWith)):
            for item in stmt.items:
                value = self.expr(item.context_expr, state, routine)
                if item.optional_vars:
                    self.assign(
                        item.optional_vars,
                        missing("context_manager_enter:" + ast.unparse(item.context_expr)),
                        state,
                        routine,
                    )
            return self.block(stmt.body, [Exit(state)], routine)
        elif isinstance(stmt, (ast.Import, ast.ImportFrom)):
            if isinstance(stmt, ast.Import):
                for alias in stmt.names:
                    state.env[alias.asname or alias.name.split(".")[0]] = Value(
                        symbol=alias.name if alias.asname else alias.name.split(".")[0]
                    )
            else:
                for alias in stmt.names:
                    state.env[alias.asname or alias.name] = Value(
                        symbol=(stmt.module or "") + "." + alias.name
                    )
        elif isinstance(stmt, ast.Break):
            return [Exit(state, "break")]
        elif isinstance(stmt, ast.Continue):
            return [Exit(state, "continue")]
        elif isinstance(stmt, ast.Assert):
            narrowed = self.narrow(stmt.test, state, routine, True)
            return [Exit(narrowed)] if narrowed else [Exit(state, "raise")]
        elif isinstance(stmt, ast.Delete):
            for target in stmt.targets:
                if isinstance(target, ast.Name):
                    state.env.pop(target.id, None)
        elif isinstance(stmt, (ast.Pass, ast.Global, ast.Nonlocal)):
            pass
        else:
            # Preserve unsupported statements and visit their expressions. This
            # diagnostic is carried only if it can affect a returned value.
            for node in ast.iter_child_nodes(stmt):
                if isinstance(node, ast.expr):
                    self.expr(node, state, routine)
        return [Exit(state)]

    def narrow(self, test, state, routine, truth):
        out = State(
            dict(state.env), state.guards + (("" if truth else "not ") + ast.unparse(test),)
        )
        if (
            isinstance(test, ast.Call)
            and isinstance(test.func, ast.Name)
            and test.func.id == "isinstance"
            and len(test.args) == 2
            and isinstance(test.args[0], ast.Name)
        ):
            variable = test.args[0].id
            value = state.env.get(variable, missing("unbound:" + variable))
            targets = test.args[1].elts if isinstance(test.args[1], ast.Tuple) else [test.args[1]]
            target_names = [self.symbol_name(x, routine.module) for x in targets]
            specs = (
                value.spec["items"]
                if value.spec and value.spec["kind"] == "union"
                else [value.spec]
            )
            selected = []
            for spec in specs:
                match = self.instance_match(spec, target_names)
                if match is None or match == truth:
                    selected.append(spec)
            if not selected:
                return None
            out.env[variable] = replace(value, spec=union(selected))
            return out
        if (
            isinstance(test, ast.Compare)
            and len(test.ops) == 1
            and isinstance(test.left, ast.Name)
            and isinstance(test.comparators[0], ast.Constant)
            and test.comparators[0].value is None
            and isinstance(test.ops[0], (ast.Is, ast.IsNot))
        ):
            variable = test.left.id
            value = state.env.get(variable, missing("unbound:" + variable))
            keep_none = truth == isinstance(test.ops[0], ast.Is)
            if value.spec:
                specs = value.spec["items"] if value.spec["kind"] == "union" else [value.spec]
                selected = [s for s in specs if (s == named("builtins.NoneType")) == keep_none]
                if not selected:
                    return None
                out.env[variable] = replace(value, spec=union(selected))
                return out
        value = self.expr(test, out, routine)
        if value.literal_known and bool(value.literal) != truth:
            return None
        return out

    def instance_match(self, spec, targets):
        if not spec:
            return None
        name = spec.get("name") if spec["kind"] == "name" else spec.get("base")
        if name in targets:
            return True
        containers = {
            "builtins.list",
            "builtins.tuple",
            "builtins.set",
            "builtins.dict",
            "collections.abc.Sequence",
            "collections.abc.Iterable",
            "collections.abc.Iterator",
        }
        if name in containers and any(
            t in {"collections.abc.Iterable", "typing.Iterable"} for t in targets
        ):
            return True
        if name in containers and any(
            t in {"collections.abc.Sequence", "typing.Sequence"} for t in targets
        ):
            return name in {"builtins.list", "builtins.tuple", "collections.abc.Sequence"}
        # Nominal classes from different external packages cannot be ruled out
        # as subclasses without their declarations. Containers and builtins can.
        if name in containers or name and name.startswith("builtins."):
            return False
        if name and any(t in containers for t in targets):
            return False if name in self.classes else None
        return None

    def project(self, value, index):
        if value.items and -len(value.items) <= index < len(value.items):
            child = value.items[index]
        elif (
            value.spec
            and value.spec["kind"] == "generic"
            and value.spec["base"] == "builtins.tuple"
        ):
            specs = value.spec["items"]
            if specs and specs[-1].get("kind") == "literal" and specs[-1].get("value") == "...":
                child = Value(specs[0])
            elif -len(specs) <= index < len(specs):
                child = Value(specs[index])
            else:
                child = missing("tuple_index_outside_declared_shape")
        else:
            child = self.element(value)
        return replace(
            child,
            origins=tuple(
                (api, path + (index,), variant, line) for api, path, variant, line in value.origins
            )
            or child.origins,
            provenance=value.provenance + child.provenance,
        )

    def element(self, value):
        if value.element:
            return value.element
        if value.items:
            return merge(list(value.items))
        if value.spec and value.spec["kind"] == "union":
            return merge([self.element(Value(x)) for x in value.spec["items"]])
        if value.spec and value.spec["kind"] == "generic":
            items = value.spec["items"]
            if (
                value.spec["base"]
                in {
                    "builtins.list",
                    "builtins.tuple",
                    "collections.abc.Sequence",
                    "collections.abc.Iterable",
                    "collections.abc.Iterator",
                }
                and items
            ):
                return (
                    Value(items[0])
                    if value.spec["base"] != "builtins.tuple"
                    else Value(union([x for x in items if x["kind"] != "literal"]))
                )
        return missing("unknown_iterable_element")

    def expr(self, node, state, routine):
        if node is None:
            return Value(named("builtins.NoneType"), literal_known=True)
        if isinstance(node, ast.Constant):
            return Value(
                named(
                    "builtins.NoneType"
                    if node.value is None
                    else "builtins." + type(node.value).__name__
                ),
                literal=node.value,
                literal_known=True,
            )
        if isinstance(node, ast.Name):
            return (
                state.env[node.id]
                if node.id in state.env
                else Value(
                    symbol=self.symbol_name(node, routine.module),
                    unknown=(
                        ()
                        if self.symbol_name(node, routine.module)
                        else ("unbound_name:" + node.id,)
                    ),
                )
            )
        if isinstance(node, ast.Attribute):
            base = self.expr(node.value, state, routine)
            if base.symbol:
                symbol = self.graph.canonical(base.symbol + "." + node.attr)
                return Value(symbol=symbol, provenance=base.provenance)
            specs = (
                base.spec["items"] if base.spec and base.spec["kind"] == "union" else [base.spec]
            )
            values = []
            for spec in specs:
                cls = (
                    spec.get("name")
                    if spec and spec["kind"] == "name"
                    else spec.get("base") if spec else None
                )
                if cls and (cls, node.attr) in self.properties:
                    getter = self.properties[(cls, node.attr)]
                    value = self.analyze(getter, {"self": base})
                    value = replace(
                        value,
                        origins=(
                            ((getter.api, (), 0, node.lineno),) if getter.api else value.origins
                        ),
                    )
                elif cls and node.attr in self.fields.get(cls, {}):
                    value = self.fields[cls][node.attr]
                    public_field = cls + "." + node.attr
                    if not node.attr.startswith("_"):
                        value = replace(value, origins=((public_field, (), 0, node.lineno),))
                elif cls and (cls, node.attr) in self.members:
                    value = Value(symbol=cls + "." + node.attr)
                else:
                    value = Value(
                        symbol=(cls + "." + node.attr) if cls else None,
                        unknown=(
                            "external_or_dynamic_attribute:"
                            + (cls or ast.unparse(node.value))
                            + "."
                            + node.attr,
                        ),
                    )
                values.append(value)
            return merge(values)
        if isinstance(node, ast.Call):
            return self.call(node, state, routine)
        if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
            items = tuple(self.expr(x, state, routine) for x in node.elts)
            base = {
                ast.Tuple: "builtins.tuple",
                ast.List: "builtins.list",
                ast.Set: "builtins.set",
            }[type(node)]
            element = merge(list(items)) if items else missing("empty_container_element")
            spec_items = (
                [v.spec or {"kind": "unknown", "reason": ";".join(v.unknown)} for v in items]
                if isinstance(node, ast.Tuple)
                else [element.spec or {"kind": "unknown", "reason": "unknown_container_element"}]
            )
            return Value(
                {"kind": "generic", "base": base, "items": spec_items},
                items=items if isinstance(node, (ast.Tuple, ast.List)) else (),
                element=element,
                unknown=tuple(dict.fromkeys(x for v in items for x in v.unknown)),
            )
        if isinstance(node, ast.Dict):
            keys = merge([self.expr(x, state, routine) for x in node.keys if x is not None])
            values = merge([self.expr(x, state, routine) for x in node.values])
            return Value(
                {
                    "kind": "generic",
                    "base": "builtins.dict",
                    "items": [
                        keys.spec or {"kind": "unknown", "reason": "dict_key"},
                        values.spec or {"kind": "unknown", "reason": "dict_value"},
                    ],
                },
                element=keys,
            )
        if isinstance(node, ast.Subscript):
            value = self.expr(node.value, state, routine)
            if (
                value.spec
                and value.spec["kind"] == "generic"
                and value.spec["base"] == "builtins.dict"
            ):
                return Value(
                    value.spec["items"][1],
                    unknown=value.unknown,
                    provenance=value.provenance + ("dictionary_value:" + ast.unparse(node),),
                )
            if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, int):
                return self.project(value, node.slice.value)
            if value.symbol in self.classes:
                return value  # Runtime generic class subscription.
            return self.element(value)
        if isinstance(node, ast.IfExp):
            values = []
            for truth, expr in [(True, node.body), (False, node.orelse)]:
                branch = self.narrow(node.test, state, routine, truth)
                if branch:
                    values.append(self.expr(expr, branch, routine))
            return merge(values)
        if isinstance(node, (ast.ListComp, ast.SetComp, ast.GeneratorExp)):
            inner = State(dict(state.env), state.guards)
            for generator in node.generators:
                self.assign(
                    generator.target,
                    self.element(self.expr(generator.iter, inner, routine)),
                    inner,
                    routine,
                )
            value = self.expr(node.elt, inner, routine)
            base = (
                "builtins.list"
                if isinstance(node, ast.ListComp)
                else "builtins.set" if isinstance(node, ast.SetComp) else "collections.abc.Iterator"
            )
            return Value(
                {
                    "kind": "generic",
                    "base": base,
                    "items": [value.spec or {"kind": "unknown", "reason": "comprehension_element"}],
                },
                element=value,
                unknown=value.unknown,
            )
        if isinstance(node, ast.Lambda):
            synthetic = ast.copy_location(
                ast.FunctionDef(
                    name="<lambda>",
                    args=node.args,
                    body=[ast.copy_location(ast.Return(value=node.body), node)],
                    decorator_list=[],
                    returns=None,
                ),
                node,
            )
            synthetic.end_lineno = node.end_lineno
            identity = routine.key + ".lambda@" + str(node.lineno) + ":" + str(node.col_offset)
            local = Routine(
                identity, routine.module, synthetic, parent=routine.key, closure=state.env
            )
            self.routines[identity] = local
            return Value(symbol=identity)
        if isinstance(node, ast.NamedExpr):
            value = self.expr(node.value, state, routine)
            self.assign(node.target, value, state, routine)
            return value
        if isinstance(node, ast.Compare):
            return Value(named("builtins.bool"))
        if isinstance(node, ast.UnaryOp):
            value = self.expr(node.operand, state, routine)
            return (
                Value(
                    named("builtins.bool"),
                    literal=not value.literal if value.literal_known else None,
                    literal_known=value.literal_known,
                )
                if isinstance(node.op, ast.Not)
                else value
            )
        if isinstance(node, ast.BoolOp):
            return merge([self.expr(x, state, routine) for x in node.values])
        if isinstance(node, ast.BinOp):
            left, right = self.expr(node.left, state, routine), self.expr(
                node.right, state, routine
            )
            numeric = {"builtins.bool", "builtins.int", "builtins.float", "builtins.complex"}
            a, b = left.spec, right.spec
            if a and b and a.get("name") in numeric and b.get("name") in numeric:
                name = (
                    "builtins.complex"
                    if "builtins.complex" in {a["name"], b["name"]}
                    else (
                        "builtins.float"
                        if "builtins.float" in {a["name"], b["name"]}
                        or isinstance(node.op, ast.Div)
                        else "builtins.int"
                    )
                )
                return Value(named(name))
            if a == b == named("builtins.str") and isinstance(node.op, ast.Add):
                return Value(named("builtins.str"))
            return missing("unresolved_operator_result:" + ast.unparse(node))
        if isinstance(node, ast.JoinedStr):
            return Value(named("builtins.str"))
        return missing("unsupported_expression:" + type(node).__name__ + ":" + ast.unparse(node))

    def bind(self, callee, positional, keywords, receiver=None):
        params = self.parameters(callee)
        env = {}
        if receiver and params and params[0].arg in {"self", "cls"}:
            env[params[0].arg] = receiver
            params = params[1:]
        pos_names = [
            p.arg
            for p in list(callee.node.args.posonlyargs) + list(callee.node.args.args)
            if p.arg not in {"self", "cls"}
        ]
        for name, value in zip(pos_names, positional):
            env[name] = value
        for name, value in keywords.items():
            if name in {p.arg for p in params}:
                env[name] = value
        return env

    def call(self, node, state, routine):
        fn = self.expr(node.func, state, routine)
        symbol = fn.symbol
        positional = []
        for arg in node.args:
            if isinstance(arg, ast.Starred):
                spread = self.expr(arg.value, state, routine)
                if spread.items:
                    positional.extend(spread.items)
                else:
                    return missing("dynamic_star_arguments:" + ast.unparse(node))
            else:
                positional.append(self.expr(arg, state, routine))
        keywords = {x.arg: self.expr(x.value, state, routine) for x in node.keywords if x.arg}
        if symbol == "typing.cast" and len(node.args) == 2:
            return replace(
                positional[1],
                spec=self.graph.annotation(node.args[0], routine.module),
                provenance=positional[1].provenance + ("typing.cast",),
            )
        if symbol in {"builtins.list", "builtins.tuple", "builtins.set", "builtins.iter"}:
            element = (
                self.element(positional[0]) if positional else missing("empty_container_element")
            )
            base = "collections.abc.Iterator" if symbol == "builtins.iter" else symbol
            if symbol == "builtins.tuple" and positional and positional[0].items:
                items = positional[0].items
                return Value(
                    {
                        "kind": "generic",
                        "base": base,
                        "items": [
                            v.spec or {"kind": "unknown", "reason": "tuple_item"} for v in items
                        ],
                    },
                    items=items,
                    element=element,
                    unknown=tuple(dict.fromkeys(x for v in items for x in v.unknown)),
                )
            specs = [element.spec or {"kind": "unknown", "reason": "container_element"}]
            if symbol == "builtins.tuple":
                specs.append({"kind": "literal", "value": "..."})
            return Value(
                {"kind": "generic", "base": base, "items": specs},
                element=element,
                unknown=element.unknown,
            )
        if symbol == "builtins.next" and positional:
            return self.element(positional[0])
        if symbol == "builtins.map" and len(positional) >= 2:
            local = self.routines.get(positional[0].symbol)
            element = self.element(positional[1])
            result = (
                self.analyze(local, self.bind(local, [element], {}))
                if local
                else missing("dynamic_map_callable")
            )
            return Value(
                {
                    "kind": "generic",
                    "base": "collections.abc.Iterator",
                    "items": [result.spec or {"kind": "unknown", "reason": "map_result"}],
                },
                element=result,
                unknown=result.unknown,
            )
        if symbol in {
            "builtins.len",
            "builtins.int",
            "builtins.float",
            "builtins.str",
            "builtins.bool",
            "builtins.complex",
        }:
            return Value(named("builtins.int" if symbol == "builtins.len" else symbol))
        if symbol in self.classes:
            candidates = self.by_symbol.get(symbol + ".__init__", [])
            if candidates:
                bindings = self.bind(candidates[0], positional, keywords, Value(named(symbol)))
                self.capture_transfers(candidates[0], bindings, node, state, routine)
            return Value(
                named(symbol),
                origins=((symbol, (), 0, node.lineno),),
                provenance=("construct:" + symbol + "@" + str(node.lineno),),
            )
        candidates = self.by_symbol.get(symbol, [])
        if symbol in self.routines:
            candidates = [self.routines[symbol]]
        receiver = (
            self.expr(node.func.value, state, routine)
            if isinstance(node.func, ast.Attribute) and candidates and candidates[0].owner
            else None
        )
        if candidates:
            # Prefer the registered dispatch whose first explicit parameter has
            # the same declared object type. Otherwise retain the primary call.
            selected = candidates[0]
            if positional:
                for candidate in candidates[1:]:
                    params = [p for p in self.parameters(candidate) if p.arg not in {"self", "cls"}]
                    annotation = (
                        self.graph.annotation(params[0].annotation, candidate.module)
                        if params
                        else None
                    )
                    if annotation and annotation == positional[0].spec:
                        selected = candidate
                        break
            bindings = self.bind(selected, positional, keywords, receiver)
            self.capture_transfers(selected, bindings, node, state, routine)
            result = self.analyze(selected, bindings)
            if selected.api:
                result = replace(
                    result,
                    origins=((selected.api, (), selected.variant, node.lineno),),
                    provenance=("call:" + selected.api + "@" + str(node.lineno),)
                    + result.provenance,
                )
            return result
        return Value(
            unknown=tuple(
                dict.fromkeys(
                    fn.unknown + ("external_or_dynamic_call:" + (symbol or ast.unparse(node.func)),)
                )
            )
        )

    def capture_transfers(self, callee, bindings, node, state, caller):
        if not callee.api:
            return

        def origins(value, target_path=()):
            if value.origins:
                for source in value.origins:
                    yield source, target_path
            else:
                for i, item in enumerate(value.items):
                    yield from origins(item, target_path + (i,))

        for name, value in bindings.items():
            for (producer, path, signature, producer_line), target_path in origins(value):
                record = {
                    "producer_api": producer,
                    "producer_variant": signature,
                    "source_path": list(path),
                    "consumer_api": callee.api,
                    "target_path": list(target_path),
                    "consumer_variant": callee.variant,
                    "argument": name,
                    "role": "receiver" if name in {"self", "cls"} else "argument",
                    "module": caller.module,
                    "line": node.lineno,
                    "producer_line": producer_line,
                    "expression": ast.unparse(node),
                    "guards": list(state.guards),
                }
                self.transfers[key(record)] = record

    def run(self):
        # Establish constructor field types before getters and callers use them.
        constructors = [r for r in self.routines.values() if r.node.name == "__init__" and r.owner]
        seen = set()
        while True:
            before = key(
                {
                    c: {n: v.spec for n, v in sorted(fs.items())}
                    for c, fs in sorted(self.fields.items())
                }
            )
            if before in seen:
                break
            seen.add(before)
            self.capture_fields = True
            for routine in constructors:
                self.analyze(routine)
            self.capture_fields = False
            after = key(
                {
                    c: {n: v.spec for n, v in sorted(fs.items())}
                    for c, fs in sorted(self.fields.items())
                }
            )
            if before == after:
                break
        self.cache.clear()
        for routine in list(self.routines.values()):
            if routine.parent is None:
                self.analyze(routine)
        # Uncalled local helpers are still scanned. Their unknown closure names
        # remain explicit rather than silently omitting their return statements.
        for routine in list(self.routines.values()):
            if not any(k[0] == routine.key for k in self.contexts):
                self.analyze(routine)

    def result(self, node):
        routine = self.by_node[id(node)]
        env = self.initial(routine)
        value = self.analyze(routine)
        cache_key = (routine.key, key({n: v.fingerprint() for n, v in sorted(env.items())}))
        record = self.contexts.get(cache_key)
        if record is None:
            record = {
                "resolution": "unresolved",
                "unresolved": ["recursive_root"],
                "return_sites": [],
            }
        return value, record

    def report(self):
        contexts = sorted(
            self.contexts.values(), key=lambda x: (x["file"], x["line"], key(x["body_type"]))
        )
        sites = {
            (r.module, n.lineno, n.col_offset)
            for r in self.routines.values()
            if not r.node.name.startswith("<lambda")
            for n in self.own_returns(r.node)
        }
        recorded = {
            (
                next(
                    m
                    for m, p in self.graph.paths.items()
                    if str(p.relative_to(self.graph.root.parent.parent)) == r["file"]
                ),
                n["line"],
                n["column"],
            )
            for r in contexts
            for n in r["return_sites"]
        }
        return {
            "summary": {
                "source_return_statements": len(sites),
                "recorded_return_statements": len(sites & recorded),
                "unrecorded_return_sites": sorted(sites - recorded),
                "analyzed_contexts": len(contexts),
                "source_call_transfers": len(self.transfers),
                "scientific_code_executed": False,
                "policy": "All Python return sites are recorded. Types can be declared, body-inferred, partial or unresolved. Loops use zero/abstract-iteration paths; external calls and unsupported constructs remain explicit. Source call transfers are static possible flows, not runtime observations.",
            },
            "contexts": contexts,
            "transfers": sorted(self.transfers.values(), key=key),
        }
