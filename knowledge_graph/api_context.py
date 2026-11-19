"""Render only retrieved API contracts and source dataflow, without aliases."""

from collections import Counter, defaultdict
from copy import deepcopy
import json
import re

API_KINDS = {"function", "class", "method", "property"}


def dump(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


js = dump


def binding_value(value):
    text = value["type"]
    attrs = [f"{k}={v}" for k, v in value.get("constraints", {}).items()]
    if "items" in value:
        items = value["items"]
        item = (
            "(" + ",".join(binding_value(v) for v in items) + ")"
            if isinstance(items, list)
            else binding_value(items)
        )
        attrs.append("items=" + item)
    return text + ("[" + ";".join(attrs) + "]" if attrs else "")


def case_lines(record, name):
    if not record.get("cases"):
        return []
    lines = ["  " + name + " cases:"]
    for case in record["cases"]:
        guard = "; ".join(k + ":" + binding_value(v) for k, v in case.get("when", {}).items())
        lines.append("    " + ("when " + guard + " => " if guard else "") + binding_value(case))
    return lines


def build_records(graph, names, selected):
    """Reorganize retrieved call facts; no unselected API contract is hydrated."""
    nodes = {n["id"]: n for n in graph["nodes"]}
    edges = graph["edges"]
    selected = set(selected)
    outgoing, incoming = defaultdict(list), defaultdict(list)
    for edge in edges:
        outgoing[edge["src"]].append(edge)
        incoming[edge["dst"]].append(edge)

    def label(identity):
        node = nodes[identity]
        if node["kind"] in API_KINDS or node["kind"] == "field":
            return names.get(identity, node.get("name", identity))
        if node["kind"] == "return":
            owners = [edge for edge in incoming[identity] if edge["kind"] == "HAS_RETURN"]
            if owners:
                return " | ".join(
                    label(edge["src"])
                    + ".return"
                    + (str(edge["source_path"]) if "source_path" in edge else "")
                    for edge in owners
                )
        if node["kind"] == "argument":
            owners = [edge for edge in incoming[identity] if edge["kind"] == "HAS_ARGUMENT"]
            if owners:
                return " | ".join(
                    label(edge["src"]) + "(input=" + node["name"] + ")" for edge in owners
                )
        return node.get("annotation") or node.get("name") or "undocumented return value"

    def edge_attributes(edge, omit=()):
        return {k: deepcopy(v) for k, v in edge.items() if k not in {"kind", "src", "dst", *omit}}

    def destination(edge):
        target = {"api": label(edge["dst"])}
        if edge.get("role") == "receiver":
            target["role"] = "receiver"
        elif "argument" in edge:
            target["input"] = edge["argument"]
        else:
            target["role"] = edge.get("role", "unspecified")
        target.update(edge_attributes(edge, ("argument", "role")))
        return target

    def flows(identity):
        return [
            destination(e)
            for e in outgoing[identity]
            if e["kind"] == "FEEDS" and e["dst"] in selected
        ]

    def value_record(identity, binding=None):
        n = nodes[identity]
        record = {}
        if n.get("annotation"):
            record["type"] = n["annotation"]
        elif n["kind"] not in ("field", "property", "return"):
            record["type"] = label(identity)
        if binding:
            record.update(edge_attributes(binding))
        typed = [
            {"type": label(e["dst"]), **edge_attributes(e)}
            for e in outgoing[identity]
            if e["kind"] == "HAS_TYPE"
        ]
        if typed:
            record["type_relations"] = typed
        direct = flows(identity) if n["kind"] not in API_KINDS else []
        if direct:
            record["feeds_to"] = direct
        return record

    records, by_id = [], {}
    expected_inputs, expected_returns = [], []
    represented_values = set()
    for identity in sorted(selected, key=label):
        n = nodes[identity]
        record = {"api": label(identity), "kind": n["kind"]}
        if n.get("description"):
            record["description"] = n["description"]
        if "constructor" in n:
            record["constructor"] = n["constructor"]
        inputs = []
        for edge in sorted(
            (e for e in outgoing[identity] if e["kind"] == "HAS_ARGUMENT"),
            key=lambda e: (e.get("signature", 0), e.get("position", 0)),
        ):
            arg = nodes[edge["dst"]]
            item = {"name": arg["name"]}
            if "annotation" in arg:
                item["type"] = arg["annotation"]
            item.update(edge_attributes(edge))
            if "default" in item:
                item["default_expression"] = item.pop("default")
            inputs.append(item)
            expected_inputs.append((identity, deepcopy(item)))
        if inputs:
            record["inputs"] = inputs
        returns = []
        for edge in outgoing[identity]:
            if edge["kind"] == "HAS_RETURN":
                item = value_record(edge["dst"], edge)
                returns.append(item)
                expected_returns.append((identity, deepcopy(item)))
                represented_values.add(edge["dst"])
        if returns:
            record["returns"] = returns
        elif n["kind"] == "property":
            record["returns"] = [value_record(identity)]
            represented_values.add(identity)
        members = []
        for edge in outgoing[identity]:
            if edge["kind"] not in ("HAS_FIELD", "HAS_METHOD", "HAS_PROPERTY"):
                continue
            member = nodes[edge["dst"]]
            if edge["kind"] == "HAS_FIELD":
                item = {
                    "name": member["name"],
                    **value_record(edge["dst"]),
                    **edge_attributes(edge),
                }
                represented_values.add(edge["dst"])
            else:
                # Ownership is explicit; member doc/call details remain in its
                # own API record only when it belongs to the selected API set.
                item = {"api": label(edge["dst"]), "kind": member["kind"]}
            members.append(item)
        if members:
            record["members"] = members
        bases = [label(e["dst"]) for e in outgoing[identity] if e["kind"] == "IS_SUBCLASS_OF"]
        if bases:
            record["bases"] = bases
        records.append(record)
        by_id[identity] = record
    # Attribute/input flows into selected consumers remain explicit even when
    # their declaring class/function is absent from the selected document set.
    external_values = []
    for identity, node in nodes.items():
        direct = flows(identity)
        if not direct:
            continue
        if identity in selected and node["kind"] in ("function", "method"):
            # API-origin FEEDS relates to its returned value. Keep the exact
            # tuple paths on each link; do not guess a
            # concrete result type or conflate it with the receiver object.
            by_id[identity]["return_connections"] = {"feeds_to": direct}
        elif identity in selected and node["kind"] == "class":
            by_id[identity]["instance_feeds_to"] = direct
        elif identity in selected and node["kind"] == "property":
            by_id[identity]["returns"][0]["feeds_to"] = direct
        elif identity not in represented_values or node["kind"] in API_KINDS:
            if node["kind"] in ("function", "method"):
                value = {"value": label(identity) + ".return", "kind": "return", "feeds_to": direct}
            elif node["kind"] == "class":
                value = {
                    "value": label(identity) + " instance",
                    "kind": "instance",
                    "feeds_to": direct,
                }
            else:
                value = {
                    "value": label(identity),
                    "kind": node["kind"],
                    **value_record(identity),
                    "feeds_to": direct,
                }
            owners = [
                e
                for e in incoming[identity]
                if e["kind"] == "HAS_ARGUMENT" and e["src"] in selected
            ]
            if node["kind"] == "argument":
                value["declared_inputs"] = [
                    {
                        "api": label(e["src"]),
                        "input": node["name"],
                        **edge_attributes(e, ("description", "default")),
                    }
                    for e in owners
                ]
            external_values.append(value)
    payload = {"apis": records}
    if external_values:
        payload["external_values"] = external_values
    for identity, item in expected_inputs:
        assert item in by_id[identity]["inputs"]
    for identity, item in expected_returns:
        assert item in by_id[identity]["returns"]
    expected_flows = Counter(
        dump(destination(e)) for e in edges if e["kind"] == "FEEDS" and e["dst"] in selected
    )
    actual_flows = all_feed_targets(payload)
    assert not expected_flows - actual_flows, "A retrieved flow target was omitted."
    return payload


def all_feed_targets(payload):
    """Count link mentions to audit that no retrieved transfer was dropped."""
    if isinstance(payload, list):
        result = Counter()
        for item in payload:
            result.update(all_feed_targets(item))
        return result
    if isinstance(payload, dict):
        result = Counter(dump(target) for target in payload.get("feeds_to", []))
        result.update(dump(target) for target in payload.get("instance_feeds_to", []))
        for key, value in payload.items():
            if key not in ("feeds_to", "instance_feeds_to"):
                result.update(all_feed_targets(value))
        return result
    return Counter()


def facts_only(value):
    """Remove generated status fields and synthetic empty values, not graph facts."""
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            if key.endswith("_status") or key in {"signature", "producer_signature"}:
                continue
            cleaned = facts_only(item)
            if cleaned == [] or cleaned == {}:
                # Component paths may explicitly be empty in a graph edge.
                if key not in ("source_path", "target_path"):
                    continue
            out[key] = cleaned
        return out
    if isinstance(value, list):
        out = [facts_only(item) for item in value]
        return [item for item in out if item != {}]
    return value


def imports_header(graph):
    """Render retrieved public exports with canonical module names, without aliases."""
    nodes = {node["id"]: node for node in graph["nodes"]}
    exports = defaultdict(set)
    for edge in graph["edges"]:
        if edge["kind"] != "EXPORTS":
            continue
        module, symbol = nodes[edge["src"]], nodes[edge["dst"]]
        if module["kind"] == "module" and symbol["kind"] in {"function", "class"}:
            exports[module["name"]].add(symbol["name"])

    lines = ["IMPORTS (canonical modules from retrieved EXPORTS; import only what you use):"]
    for module, symbols in sorted(exports.items()):
        lines.append("  import " + module + "  # EXPORTS: " + ", ".join(sorted(symbols)))
    lines += [
        "args are ordered as shown; explicit indices are zero-based. Missing args/returns are not empty contracts.",
        "FEEDS is source/demo dataflow; Sets on both sides expand to every pair. self means receiver.",
    ]
    return lines


def compressed(payload, *, graph):
    """Keep all API records and documented call fields; factor identical links."""
    lines = imports_header(graph)
    if any("cases" in e for e in graph["edges"]):
        lines.append(
            "cases: when sibling inputs match => value constraint; alternatives are partial; missing guards are unspecified."
        )
    facts = set()
    detailed = {api["api"] for api in payload["apis"]}

    def docs(record, prefix):
        text = record.get("description")
        if text:
            return [prefix + text]
        return []

    def attrs(record, skip=()):
        values = []
        for key, value in record.items():
            if key in skip:
                continue
            if key == "conditional" and value == "matching runtime union alternative":
                values.append("union-alternative")
            else:
                values.append(key + "=" + (str(value) if isinstance(value, str) else js(value)))
        return " [" + ";".join(values) + "]" if values else ""

    def path(value):
        return "".join("[" + str(item) + "]" for item in value)

    def links(record, source):
        for field, kind in (("feeds_to", "FEEDS"),):
            for target in record.get(field, []):
                src = source + path(target.get("source_path", []))
                dst = (
                    target["api"]
                    + "."
                    + (
                        target["input"]
                        if "input" in target
                        else "self" if target.get("role") == "receiver" else "value"
                    )
                )
                dst += path(target.get("target_path", []))
                other = attrs(target, ("api", "input", "role", "source_path", "target_path"))
                facts.add((kind, str(src), str(dst), other))

    def value(record, source):
        links(record, source)
        text = str(record.get("type", ""))
        text += attrs(
            record,
            (
                "type",
                "description",
                "feeds_to",
                "type_relations",
                "name",
                "api",
                "kind",
                "value",
                "cases",
            ),
        )
        for relation in record.get("type_relations", []):
            if relation == {"type": record.get("type")}:
                continue
            text += " as " + str(relation["type"]) + attrs(relation, ("type",))
        return text.strip()

    for api in payload["apis"]:
        owner = api["api"]
        lines += ["", "API: " + str(owner) + " [" + api["kind"] + "]"]
        lines += docs(api, "  description: ")
        if "constructor" in api:
            lines.append("  constructor: " + api["constructor"])
        inputs = api.get("inputs", [])
        if inputs:
            contiguous = [item["position"] for item in inputs] == list(range(len(inputs)))
            args = []
            for item in inputs:
                argument = ("" if contiguous else str(item["position"]) + ":") + item["name"]
                if "type" in item:
                    argument += ":" + str(item["type"])
                if "default_expression" in item:
                    argument += "=" + str(item["default_expression"])
                kind = item.get("parameter_kind")
                if kind not in (None, "positional_or_keyword"):
                    argument += " [" + kind + "]"
                if item.get("required", "default_expression" not in item) != (
                    "default_expression" not in item
                ):
                    argument += " [required]" if item["required"] else " [optional]"
                args.append(argument)
            lines.append("  args: " + ", ".join(args))
            for item in inputs:
                lines += docs(item, "  " + item["name"] + ": ")
                lines += case_lines(item, item["name"])
        returns = []
        for item in api.get("returns", []):
            text = value(item, owner + ".return" + path(item.get("source_path", [])))
            if text:
                returns.append(text)
        if returns:
            lines.append("  returns: " + "; ".join(returns))
        for item in api.get("returns", []):
            lines += docs(item, "  return: ")
            lines += case_lines(item, "return" + path(item.get("source_path", [])))
        links(api.get("return_connections", {}), owner + ".return")
        links({"feeds_to": api.get("instance_feeds_to", [])}, owner + ".instance")
        for member in api.get("members", []):
            if "api" in member:
                if member["api"] not in detailed:
                    lines.append("  member: " + str(member["api"]) + " [" + member["kind"] + "]")
                continue
            text = value(member, owner + "." + member["name"])
            lines.append("  field: " + member["name"] + (":" + text if text else ""))
            lines += docs(member, "  " + member["name"] + ": ")
        if api.get("bases"):
            lines.append("  bases: " + ",".join(str(item) for item in api["bases"]))
    for item in payload.get("external_values", []):
        text = value(item, item["value"])
        lines.append(
            "VALUE: "
            + str(item["value"])
            + " ["
            + item["kind"]
            + "]"
            + (":" + text if text else "")
        )

    # Group only identical target sets. Expansion must reproduce exactly the
    # same graph facts, without creating new producer-consumer connections.
    relation_lines = []
    expanded = set()
    for kind in ("FEEDS",):
        by_source = defaultdict(set)
        for rel, src, dst, note in facts:
            if rel == kind:
                by_source[src].add((dst, note))
        groups = defaultdict(list)
        for src, targets in by_source.items():
            groups[tuple(sorted(targets))].append(src)
        relation_lines.append(kind + ":")
        for targets, sources in sorted(groups.items(), key=lambda pair: sorted(pair[1])):
            sources = sorted(sources)
            left = sources[0] if len(sources) == 1 else "{" + ",".join(sources) + "}"
            right = ",".join(dst + note for dst, note in targets)
            relation_lines.append(
                "  " + left + " -> " + ("{" + right + "}" if len(targets) > 1 else right)
            )
            for src in sources:
                expanded.update((kind, src, dst, note) for dst, note in targets)
    assert expanded == facts
    lines += ["", "RELATIONS:", *relation_lines]
    return "\n".join(lines)
