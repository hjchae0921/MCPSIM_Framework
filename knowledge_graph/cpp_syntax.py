"""Source-wide nanobind/pybind registration and declaration analysis.

Rules depend on binding syntax, C++ type constructors and source declarations,
never on API identifiers, benchmark outcomes or exception messages.
"""

from __future__ import annotations

from collections import Counter, defaultdict, deque
from copy import deepcopy
import ast
import json
from pathlib import Path
import re


def walk(node):
    yield node
    for child in node.named_children:
        yield from walk(child)


def split_type(text):
    text = re.sub(r"\b(?:const|volatile|typename|class|struct)\b", "", text)
    text = re.sub(r"\s+", " ", text).strip().strip("&* ")
    opening = text.find("<")
    if opening < 0:
        return text.replace(" ::", "::").replace(":: ", "::"), []
    depth, start, parts = 0, opening + 1, []
    for index in range(opening, len(text)):
        character = text[index]
        if character == "<":
            depth += 1
        elif character == ">":
            depth -= 1
            if depth == 0:
                if text[index + 1 :].strip():
                    # A dependent member type needs declaration-level substitution.
                    return text, []
                parts.append(text[start:index].strip())
                return text[:opening].strip(), parts
        elif character == "," and depth == 1:
            parts.append(text[start:index].strip())
            start = index + 1
    return text, []


def integer(text, substitutions):
    text = substitutions.get(text.strip(), text.strip())
    text = re.sub(r"(?<=\d)[uUlL]+\b", "", text)
    try:
        value = ast.literal_eval(text)
    except (SyntaxError, ValueError):
        return None
    return value if type(value) is int else None


def callable_name(text):
    """Remove template arguments without discarding a following ::member name."""
    output, depth = [], 0
    for character in text.strip().lstrip("&"):
        if character == "<":
            depth += 1
        elif character == ">":
            depth -= 1
        elif depth == 0:
            output.append(character)
    return "".join(output).strip()


class CppSource:
    METHODS = {
        "def",
        "def_static",
        "def_prop_ro",
        "def_prop_rw",
        "def_ro",
        "def_rw",
        "def_prop_ro_static",
        "def_prop_rw_static",
        "def_ro_static",
        "def_rw_static",
        "def_property",
        "def_property_readonly",
        "def_readonly",
        "def_readwrite",
        "def_property_static",
        "def_property_readonly_static",
        "def_readonly_static",
        "def_readwrite_static",
    }

    def __init__(self, source):
        from tree_sitter import Language, Parser
        import tree_sitter_cpp

        self.source = Path(source)
        self.inventory = json.loads((self.source / "binding_sources.json").read_text())
        parser = Parser(Language(tree_sitter_cpp.language()))
        self.files, self.functions, self.function_names = {}, [], defaultdict(list)
        self.aliases, self.registered_types = defaultdict(list), defaultdict(list)
        self.declared_types = set()
        self.fields = defaultdict(list)
        self.contexts, self.registrations = [], []
        self.parse_recovery = []
        for row in self.inventory["files"]:
            if not row["role"].startswith("prepared_cpp"):
                continue
            data = (self.source.parent / row["file"]).read_bytes()
            root = parser.parse(data).root_node
            file = {
                "path": row["file"],
                "data": data,
                "root": root,
                "package": row.get("repository", "").split("/")[-1],
                "framework_aliases": {"nanobind", "pybind11"},
                "using_namespaces": [],
            }
            for alias in walk(root):
                if alias.type == "namespace_alias_definition":
                    match = re.fullmatch(
                        r"namespace\s+(\w+)\s*=\s*(nanobind|pybind11)\s*;", self.text(file, alias)
                    )
                    if match:
                        file["framework_aliases"].add(match[1])
                if alias.type == "using_declaration" and alias.parent.type == "translation_unit":
                    match = re.fullmatch(
                        r"using\s+namespace\s+([\w:]+)\s*;", self.text(file, alias)
                    )
                    if match:
                        file["using_namespaces"].append(match[1])
            self.files[row["file"]] = file
            if root.has_error:
                self.parse_recovery.append(row["file"])
            self._index(file)
        self._includes()
        self._contexts()
        self._types()

    @staticmethod
    def text(file, node):
        return file["data"][node.start_byte : node.end_byte].decode() if node else ""

    @staticmethod
    def scope(node):
        names = []
        parent = node.parent
        while parent:
            if parent.type in {"namespace_definition", "class_specifier", "struct_specifier"}:
                name = parent.child_by_field_name("name")
                if name:
                    names.append(name.text.decode())
            parent = parent.parent
        return "::".join(reversed(names))

    @staticmethod
    def local_key(node, name):
        parent = node.parent
        while parent:
            if parent.type == "compound_statement":
                return (parent.start_byte, name)
            parent = parent.parent
        return name

    @staticmethod
    def framework(base, file):
        return base.split("::", 1)[0] in file["framework_aliases"]

    def _index(self, file):
        for node in walk(file["root"]):
            if node.type in {"class_specifier", "struct_specifier", "enum_specifier"}:
                name = node.child_by_field_name("name")
                if name:
                    self.declared_types.add(
                        "::".join(filter(None, [self.scope(node), self.text(file, name)]))
                    )
            if node.type in {"alias_declaration", "type_definition"}:
                name = node.child_by_field_name("name") or node.child_by_field_name("declarator")
                typ = node.child_by_field_name("type")
                if name and typ:
                    key = "::".join(filter(None, [self.scope(node), self.text(file, name)]))
                    self.aliases[key].append((file["path"], self.text(file, typ)))
            if node.type not in {"function_definition", "declaration", "field_declaration"}:
                continue
            declarator = node.child_by_field_name("declarator")
            if not declarator:
                continue
            if node.type == "field_declaration" and declarator.type in {
                "identifier",
                "field_identifier",
            }:
                name = "::".join(filter(None, [self.scope(node), self.text(file, declarator)]))
                self.fields[name].append((file, self.text(file, node.child_by_field_name("type"))))
            while declarator.type in {"pointer_declarator", "reference_declarator"}:
                declarator = declarator.child_by_field_name("declarator")
                if not declarator:
                    break
            if not declarator or declarator.type != "function_declarator":
                continue
            name_node = declarator.child_by_field_name("declarator")
            name = self.text(file, name_node)
            parameters = declarator.child_by_field_name("parameters")
            if not parameters or parameters.has_error:
                continue
            names, types = [], []
            for parameter in parameters.named_children:
                if parameter.type not in {
                    "parameter_declaration",
                    "optional_parameter_declaration",
                }:
                    continue
                typ = parameter.child_by_field_name("type")
                dec = parameter.child_by_field_name("declarator")
                identifiers = (
                    [self.text(file, p) for p in walk(dec) if p.type == "identifier"] if dec else []
                )
                names.append(identifiers[0] if len(identifiers) == 1 else None)
                types.append(self.text(file, typ))
            templates = []
            parent = node.parent
            if parent and parent.type == "template_declaration":
                template_parameters = parent.child_by_field_name("parameters")
                for parameter in template_parameters.named_children if template_parameters else []:
                    ids = [
                        self.text(file, n)
                        for n in parameter.named_children
                        if n.type in {"type_identifier", "identifier"}
                    ]
                    if ids:
                        templates.append(ids[-1])
            parent_scope = self.scope(node)
            qualified = name.lstrip("::")
            if (
                parent_scope
                and not qualified.startswith(parent_scope + "::")
                and not name.startswith("::")
            ):
                qualified = parent_scope + "::" + qualified
            qualified = callable_name(qualified)
            record = {
                "file": file,
                "node": node,
                "name": name,
                "qualified": qualified,
                "names": names,
                "types": types,
                "templates": templates,
                "body": node.child_by_field_name("body"),
                "return_type": self.text(file, node.child_by_field_name("type")),
            }
            self.functions.append(record)
            self.function_names[callable_name(name).rsplit("::", 1)[-1]].append(record)

    def _includes(self):
        self.available = {}
        direct = {}
        for path, file in self.files.items():
            matches = []
            for include in re.findall(
                r'^\s*#include\s+["<]([^">]+)[">]', file["data"].decode(), re.M
            ):
                matches.extend(
                    p
                    for p in self.files
                    if p == str(Path(path).parent / include) or p.endswith("/" + include)
                )
            direct[path] = set(matches)
        for path, file in self.files.items():
            reachable, queue = {path}, [path]
            while queue:
                current = queue.pop()
                for match in direct[current]:
                    if match not in reachable:
                        reachable.add(match)
                        queue.append(match)
            self.available[path] = reachable

    def _callee(self, expression, current):
        _, arguments = split_type(expression)
        base = callable_name(expression)
        if not expression.strip().endswith(">"):
            arguments = []
        basename = base.rsplit("::", 1)[-1]
        candidates = self.function_names.get(basename, [])
        visible = self.available[current["file"]["path"]]
        if "::" in base:
            candidates = [
                f
                for f in candidates
                if f["qualified"] == base
                and f["body"]
                and f["file"]["package"] == current["file"]["package"]
            ]
        else:
            candidates = [f for f in candidates if f["file"]["path"] in visible and f["body"]]
            local = [f for f in candidates if f["file"] is current["file"]]
            if local:
                candidates = local
        return candidates, arguments

    def value(self, node, file, env):
        if not node:
            return None
        text = self.text(file, node)
        if node.type == "identifier":
            parent = node.parent
            while parent:
                if parent.type == "compound_statement" and (parent.start_byte, text) in env:
                    return env[parent.start_byte, text]
                parent = parent.parent
            return env.get(text)
        if node.type == "string_literal":
            try:
                return ("string", json.loads(text))
            except ValueError:
                return None
        if node.type == "binary_expression":
            left = self.value(node.child_by_field_name("left"), file, env)
            right = self.value(node.child_by_field_name("right"), file, env)
            operator = node.child_by_field_name("operator")
            if (
                left
                and right
                and left[0] == right[0] == "string"
                and self.text(file, operator) == "+"
            ):
                return ("string", left[1] + right[1])
        if node.type == "call_expression":
            func = node.child_by_field_name("function")
            args = node.child_by_field_name("arguments")
            values = args.named_children if args else []
            if func and func.type == "field_expression":
                member = self.text(file, func.child_by_field_name("field"))
                receiver = self.value(func.child_by_field_name("argument"), file, env)
                if receiver and member == "c_str":
                    return receiver
                if receiver and receiver[0] == "module" and member == "def_submodule" and values:
                    name = self.value(values[0], file, env)
                    if name and name[0] == "string":
                        return ("module", receiver[1] + "." + name[1])
            if self.text(file, func) == "std::string" and len(values) == 1:
                return self.value(values[0], file, env)
            if self.text(file, func) == "std::format" and values:
                strings = [self.value(v, file, env) for v in values]
                if all(v and v[0] == "string" for v in strings):
                    try:
                        return ("string", strings[0][1].format(*(v[1] for v in strings[1:])))
                    except (ValueError, KeyError, IndexError):
                        return None
        return None

    def _contexts(self):
        queue, seen = deque(), set()
        for function in self.functions:
            if function["name"] in {"NB_MODULE", "PYBIND11_MODULE"} and function["body"]:
                name = function["names"]
                # Module macros use identifier-like pseudo-parameters, not typed arguments.
                parameters = (
                    function["node"]
                    .child_by_field_name("declarator")
                    .child_by_field_name("parameters")
                )
                tokens = [self.text(function["file"], n) for n in parameters.named_children]
                if len(tokens) >= 2:
                    queue.append(
                        (
                            function,
                            {tokens[1]: ("module", function["file"]["package"] + "." + tokens[0])},
                            {},
                        )
                    )
        while queue:
            function, initial, substitutions = queue.popleft()
            key = (
                function["file"]["path"],
                function["node"].start_byte,
                tuple(sorted(initial.items())),
                tuple(sorted(substitutions.items())),
            )
            if key in seen:
                continue
            seen.add(key)
            env = dict(initial)
            file = function["file"]
            nodes = list(walk(function["body"]))
            # Finite environment: only source string/module values are propagated.
            changed = True
            while changed:
                changed = False
                for node in nodes:
                    if node.type != "init_declarator":
                        continue
                    name = self.text(file, node.child_by_field_name("declarator"))
                    key = self.local_key(node, name)
                    value = node.child_by_field_name("value")
                    if value and value.type == "argument_list" and len(value.named_children) == 1:
                        value = value.named_children[0]
                    resolved = self.value(value, file, env)
                    if resolved and key not in env:
                        env[key] = resolved
                        changed = True
            self.contexts.append((function, env, substitutions))
            for node in nodes:
                if node.type != "call_expression":
                    continue
                func, args = node.child_by_field_name("function"), node.child_by_field_name(
                    "arguments"
                )
                if not func or func.type == "field_expression" or not args:
                    continue
                values = [self.value(arg, file, env) for arg in args.named_children]
                if not any(value and value[0] == "module" for value in values):
                    continue
                candidates, templates = self._callee(self.text(file, func), function)
                for target in candidates:
                    if len(values) > len(target["names"]):
                        continue
                    child_env = {
                        name: value
                        for name, value in zip(target["names"], values)
                        if name and value
                    }
                    child_types = {
                        name: substitutions.get(value, value)
                        for name, value in zip(target["templates"], templates)
                    }
                    queue.append((target, child_env, child_types))

    def _types(self):
        self.class_variables = {}
        for function, env, substitutions in self.contexts:
            file = function["file"]
            for node in walk(function["body"]):
                if node.type == "declaration":
                    typ, dec = node.child_by_field_name("type"), node.child_by_field_name(
                        "declarator"
                    )
                    base, arguments = split_type(self.text(file, typ))
                    if (
                        self.framework(base, file)
                        and base.rsplit("::", 1)[-1] in {"class_", "enum_"}
                        and arguments
                        and dec
                    ):
                        name = self.text(file, dec.child_by_field_name("declarator"))
                        self.class_variables[(file["path"], self.local_key(dec, name))] = arguments[
                            0
                        ]
                        args = dec.child_by_field_name("value")
                        if args and args.type == "argument_list":
                            self._register_type(arguments[0], base, args, file, env, substitutions)
                if node.type == "call_expression":
                    base, arguments = split_type(
                        self.text(file, node.child_by_field_name("function"))
                    )
                    if (
                        self.framework(base, file)
                        and base.rsplit("::", 1)[-1] in {"class_", "enum_"}
                        and arguments
                    ):
                        args = node.child_by_field_name("arguments")
                        if args:
                            self._register_type(arguments[0], base, args, file, env, substitutions)

    def _register_type(self, cpp, base, args, file, env, substitutions):
        values = args.named_children
        if len(values) < 2:
            return
        module = self.value(values[0], file, env)
        name = self.value(values[1], file, env)
        if module and module[0] == "module" and name and name[0] == "string":
            cppbase, cppargs = split_type(cpp)
            choices = [n + "::" + cppbase for n in file["using_namespaces"]] + [cppbase]
            qualified = next((c for c in choices if c in self.declared_types), cppbase)
            record = {
                "python": module[1] + "." + name[1],
                "cpp": cpp,
                "kind": base.rsplit("::", 1)[-1],
                "file": file["path"],
            }
            key = qualified
            if record not in self.registered_types[key]:
                self.registered_types[key].append(record)

    def resolve_type(self, text, overrides, file, substitutions=None, visiting=(), scope=""):
        substitutions = substitutions or {}
        base, arguments = split_type(text)
        if base in substitutions and not arguments:
            return self.resolve_type(substitutions[base], overrides, file, {}, visiting, scope)
        scopes = scope.split("::") if scope else []
        choices = ["::".join(scopes[:i] + [base]) for i in range(len(scopes), 0, -1)]
        choices += [n + "::" + base for n in file["using_namespaces"]] + [base]
        registered = []
        for choice in choices:
            if choice in overrides:
                return {"type": overrides[choice]}
            rows = self.registered_types.get(choice, [])
            local = [r for r in rows if self.files[r["file"]]["package"] == file["package"]]
            if local:
                registered = local
                break
            if rows and "::" in base and choice == base:
                registered = rows
                break
        if registered:
            return {"type": " | ".join(sorted({r["python"] for r in registered}))}
        for choice in choices:
            aliases = [
                (path, value)
                for path, value in self.aliases.get(choice, [])
                if path in self.available[file["path"]]
            ]
            if len({value for _, value in aliases}) == 1 and choice not in visiting:
                return self.resolve_type(
                    aliases[0][1],
                    overrides,
                    file,
                    substitutions,
                    visiting + (choice,),
                    choice.rpartition("::")[0],
                )
        short = base.rsplit("::", 1)[-1]
        if (
            base.startswith("std::")
            and short in {"shared_ptr", "unique_ptr", "reference_wrapper"}
            and arguments
        ):
            return self.resolve_type(arguments[0], overrides, file, substitutions, visiting, scope)
        if base.startswith("std::") and short == "optional" and arguments:
            value = self.resolve_type(arguments[0], overrides, file, substitutions, visiting, scope)
            if value:
                value["type"] += " | builtins.NoneType"
            return value
        if self.framework(base, file) and short in {"ndarray", "array_t"}:
            value = {"type": "numpy.ndarray"}
            for argument in arguments:
                kind, dimensions = split_type(argument)
                if (
                    self.framework(kind, file)
                    and kind.rsplit("::", 1)[-1] == "ndim"
                    and len(dimensions) == 1
                ):
                    rank = integer(dimensions[0], substitutions)
                    if rank is not None and rank >= 0:
                        value["constraints"] = {"ndim": rank}
                elif self.framework(kind, file) and kind.rsplit("::", 1)[-1] == "shape":
                    value["constraints"] = {"ndim": len(dimensions)}
            return value
        if base.startswith("std::") and short in {"array", "vector", "list"} and arguments:
            item = self.resolve_type(arguments[0], overrides, file, substitutions, visiting, scope)
            if item is None:
                return None
            value = {"type": "sequence", "items": item}
            if short == "array" and len(arguments) == 2:
                length = integer(arguments[1], substitutions)
                if length is not None and length >= 0:
                    value["constraints"] = {"length": length}
            return value
        if base.startswith("std::") and short in {"tuple", "pair"}:
            if (short == "pair" and len(arguments) != 2) or ("<" not in text):
                return None
            values = [
                self.resolve_type(a, overrides, file, substitutions, visiting, scope)
                for a in arguments
            ]
            if any(v is None for v in values):
                return None
            result = {"type": "tuple", "constraints": {"length": len(values)}}
            if values:
                result["items"] = values
            return result
        if base.startswith("std::") and short in {"map", "unordered_map"} and len(arguments) >= 2:
            values = [
                self.resolve_type(a, overrides, file, substitutions, visiting, scope)
                for a in arguments[:2]
            ]
            if all(v is not None for v in values):
                return {
                    "type": "builtins.dict",
                    "items": {"type": "tuple", "constraints": {"length": 2}, "items": values},
                }
            return None
        if base.startswith("std::") and short == "variant":
            values = [
                self.resolve_type(a, overrides, file, substitutions, visiting, scope)
                for a in arguments
            ]
            if not values or any(v is None for v in values):
                return None
            return {"type": " | ".join(sorted({v["type"] for v in values}))}
        if base in {"bool", "void"}:
            return {"type": "builtins.bool" if base == "bool" else "builtins.NoneType"}
        if re.fullmatch(
            r"(?:(?:signed|unsigned) )?(?:(?:short|long|long long)(?: int)?|int)", base
        ) or re.fullmatch(r"(?:std::)?(?:u?int(?:8|16|32|64)_t|u?intptr_t|size_t|ptrdiff_t)", base):
            return {"type": "builtins.int"}
        if base in {"float", "double", "long double"}:
            return {"type": "builtins.float"}
        if base in {"char", "wchar_t", "char16_t", "char32_t", "std::string", "std::string_view"}:
            return {"type": "builtins.str"}
        if base in {"signed char", "unsigned char"}:
            return {"type": "builtins.int"}
        if base in {"std::complex"}:
            return {"type": "builtins.complex"}
        if base == "std::filesystem::path":
            return {"type": "builtins.str | os.PathLike"}
        if base == "std::function" or (
            self.framework(base, file) and short in {"function", "callable"}
        ):
            return {"type": "collections.abc.Callable"}
        return None

    def _receiver(self, node, function):
        file = function["file"]
        while node and node.type == "call_expression":
            func = node.child_by_field_name("function")
            if func and func.type == "field_expression":
                node = func.child_by_field_name("argument")
            else:
                base, args = split_type(self.text(file, func))
                return (
                    args[0]
                    if self.framework(base, file)
                    and base.rsplit("::", 1)[-1] in {"class_", "enum_"}
                    and args
                    else None
                )
        name = self.text(file, node)
        parent = node.parent if node else None
        while parent:
            key = (file["path"], (parent.start_byte, name))
            if parent.type == "compound_statement" and key in self.class_variables:
                return self.class_variables[key]
            parent = parent.parent
        return None

    def records(self, overrides):
        records, unresolved, census, covered = [], [], {}, set()
        for function, env, substitutions in self.contexts:
            file = function["file"]
            for node in walk(function["body"]):
                if node.type != "call_expression":
                    continue
                func, args_node = node.child_by_field_name("function"), node.child_by_field_name(
                    "arguments"
                )
                if not func or func.type != "field_expression" or not args_node:
                    continue
                method = self.text(file, func.child_by_field_name("field"))
                if method not in self.METHODS:
                    continue
                args = args_node.named_children
                if not args:
                    continue
                field = func.child_by_field_name("field")
                site = (file["path"], field.start_byte)
                covered.add(site)
                owner_text = self._receiver(func.child_by_field_name("argument"), function)
                owner = split_type(owner_text)[0] if owner_text else None
                owner_value = (
                    self.resolve_type(
                        owner_text,
                        overrides,
                        file,
                        substitutions,
                        scope=self.scope(function["node"]),
                    )
                    if owner_text
                    else None
                )
                receiver = self.value(func.child_by_field_name("argument"), file, env)
                module = receiver[1] if receiver and receiver[0] == "module" else None
                name, callable_node = None, None
                literal_name = self.value(args[0], file, env)
                if literal_name and literal_name[0] == "string":
                    name = literal_name[1]
                    callable_node = args[1] if len(args) > 1 else None
                else:
                    base, _ = split_type(self.text(file, args[0].child_by_field_name("function")))
                    if self.framework(base, file) and base.rsplit("::", 1)[-1] in {
                        "init",
                        "init_implicit",
                        "new_",
                    }:
                        name, callable_node = "__init__", args[0]
                proof = {
                    "file": file["path"],
                    "line": field.start_point.row + 1,
                    "column": field.start_point.column + 1,
                    "binding": name,
                    "owner": owner,
                    "registration_kind": method,
                    "python_module": module,
                    "owner_python": (
                        owner_value["type"]
                        if owner_value and " | " not in owner_value["type"]
                        else None
                    ),
                }
                census[site] = proof
                if owner is None and module is None:
                    unresolved.append({**proof, "reason": "binding_receiver_unresolved"})
                    continue
                if name is None or callable_node is None:
                    unresolved.append({**proof, "reason": "unresolved_registration_name"})
                    continue
                types, returns, type_file, type_scope = self.signature(
                    callable_node,
                    function,
                    owner if method != "def_static" else None,
                    substitutions,
                )
                if types is None:
                    unresolved.append(
                        {
                            **proof,
                            "reason": "declaration_source_unavailable_or_ambiguous",
                            "expression": self.text(file, callable_node),
                        }
                    )
                    continue
                values = [
                    self.resolve_type(t, overrides, type_file, substitutions, scope=type_scope)
                    for t in types
                ]
                if any(v is None for v in values):
                    unresolved.append(
                        {
                            **proof,
                            "reason": "python_type_mapping_unresolved",
                            "types": types,
                            "unresolved_types": [t for t, v in zip(types, values) if v is None],
                        }
                    )
                    continue
                return_value = (
                    self.resolve_type(
                        returns, overrides, type_file, substitutions, scope=type_scope
                    )
                    if returns
                    else None
                )
                records.append(
                    {
                        **proof,
                        "inputs": values,
                        "return_value": return_value,
                        "cpp_parameter_types": types,
                        "cpp_return_type": returns,
                    }
                )
        # Report registrations outside successfully propagated module contexts too.
        structural = []
        for file in self.files.values():
            for node in walk(file["root"]):
                if node.type != "call_expression":
                    continue
                func = node.child_by_field_name("function")
                if not func or func.type != "field_expression":
                    continue
                method = self.text(file, func.child_by_field_name("field"))
                if method not in self.METHODS:
                    continue
                field = func.child_by_field_name("field")
                site = (file["path"], field.start_byte)
                structural.append(
                    {
                        "file": file["path"],
                        "line": field.start_point.row + 1,
                        "column": field.start_point.column + 1,
                        "kind": method,
                    }
                )
                if site not in covered:
                    unresolved.append(
                        {
                            "file": file["path"],
                            "line": field.start_point.row + 1,
                            "column": field.start_point.column + 1,
                            "registration_kind": method,
                            "reason": "module_context_unresolved",
                        }
                    )
        self.report = {
            "registration_sites": len(structural),
            "registration_kinds": dict(Counter(x["kind"] for x in structural)),
            "sites_with_resolved_inputs": len(
                {(r["file"], r["line"], r["column"]) for r in records}
            ),
            "sites_with_module_context": len(covered),
            "module_contexts": len(self.contexts),
            "type_registrations": sum(len(v) for v in self.registered_types.values()),
            "source_type_aliases": sum(len(v) for v in self.aliases.values()),
            "syntax_recovery_files": self.parse_recovery,
            "all_registration_sites": structural,
        }
        return records, unresolved

    def signature(self, node, function, owner, substitutions):
        file = function["file"]
        scope = self.scope(function["node"])
        if node.type == "lambda_expression":
            declarator = node.child_by_field_name("declarator")
            params = declarator.child_by_field_name("parameters") if declarator else None
            if not params or params.has_error:
                return None, None, file, scope
            types = [
                self.text(file, p.child_by_field_name("type"))
                for p in params.named_children
                if p.type in {"parameter_declaration", "optional_parameter_declaration"}
            ]
            if owner and types and split_type(types[0])[0] == owner:
                types = types[1:]
            trailing = next(
                (n for n in declarator.named_children if n.type == "trailing_return_type"), None
            )
            if trailing:
                ret = self.text(file, trailing).removeprefix("->").strip()
            else:
                ret = None
                statements = [
                    n
                    for n in walk(node.child_by_field_name("body"))
                    if n.type == "return_statement"
                ]
                values = []
                for statement in statements:
                    expression = statement.named_children[0] if statement.named_children else None
                    if expression and expression.type == "call_expression":
                        candidate = self.text(file, expression.child_by_field_name("function"))
                    else:
                        candidate = None
                    values.append(candidate)
                if values and values[0] and all(v == values[0] for v in values):
                    ret = values[0]
            return types, ret, file, scope
        if node.type == "call_expression":
            expression = self.text(file, node.child_by_field_name("function"))
            base, args = split_type(expression)
            if self.framework(base, file) and base.rsplit("::", 1)[-1] in {
                "init",
                "init_implicit",
                "overload_cast",
            }:
                return args, None, file, scope
            if self.framework(base, file) and base.rsplit("::", 1)[-1] == "new_":
                arguments = node.child_by_field_name("arguments")
                if arguments and len(arguments.named_children) == 1:
                    return self.signature(
                        arguments.named_children[0], function, None, substitutions
                    )
        expression = self.text(file, node).lstrip("&")
        expression = callable_name(expression)
        if expression in self.fields:
            values = self.fields[expression]
            if len({t for _, t in values}) == 1:
                target, typ = values[0]
                return [], typ, target, expression.rpartition("::")[0]
        candidates, _ = self._callee(expression, function)
        if not candidates:
            # Prototypes count even when no function body is in the snapshot.
            candidates = [
                f
                for f in self.function_names.get(expression.rsplit("::", 1)[-1], [])
                if f["qualified"] == expression
                and f["file"]["path"] in self.available[file["path"]]
            ]
        signatures = {(tuple(f["types"]), f["return_type"]) for f in candidates}
        if len(signatures) == 1:
            types, ret = next(iter(signatures))
            target = candidates[0]
            return list(types), ret, target["file"], target["qualified"].rpartition("::")[0]
        return None, None, file, scope
