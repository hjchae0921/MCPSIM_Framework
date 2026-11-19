"""Recreate the searchable Markdown chunks from the bundled official HTML."""

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup, NavigableString
from markdownify import markdownify

HERE = Path(__file__).resolve().parent
KINDS = {"function", "class", "method", "property", "attribute", "data", "exception"}


def code_language(element):
    for parent in [element, *element.parents]:
        for value in parent.get("class", []):
            if value.startswith("highlight-"):
                language = value.removeprefix("highlight-")
                return "" if language in {"default", "none"} else language
    return ""


def to_markdown(element, page_url):
    html = (
        "".join(str(child) for child in element.contents) if element.name == "dd" else str(element)
    )
    node = BeautifulSoup(html, "html.parser")
    for extra in node.select(".headerlink, .viewcode-link, script, style, nav, aside"):
        extra.decompose()
    for link in node.find_all("a", href=True):
        link["href"] = urljoin(page_url, link["href"])
    for image in node.find_all("img", src=True):
        image["src"] = urljoin(page_url, image["src"])
    for fields in node.select("dl.field-list"):
        for term in fields.find_all("dt", recursive=False):
            term.name = "p"
            label = node.new_tag("strong")
            for child in list(term.contents):
                label.append(child.extract())
            term.append(label)
        for description in fields.find_all("dd", recursive=False):
            description.name = "div"
        fields.name = "div"
    equations = {}
    for number, math in enumerate(node.select(".math")):
        for extra in math.select(".eqno"):
            extra.decompose()
        value = math.get_text().strip()
        display = math.name == "div" or value.startswith(r"\[")
        if value.startswith(r"\[") and value.endswith(r"\]"):
            value = value[2:-2].strip()
        elif value.startswith(r"\(") and value.endswith(r"\)"):
            value = value[2:-2].strip()
        marker = f"RAGMATHPLACEHOLDER{number}END"
        equations[marker] = "\n\n$$\n" + value + "\n$$\n\n" if display else "$" + value + "$"
        math.replace_with(NavigableString(marker))
    text = markdownify(
        str(node), heading_style="ATX", bullets="-", code_language_callback=code_language
    )
    for marker, equation in equations.items():
        text = text.replace(marker, equation)
    return re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"


def split_page(html, page_url):
    """Yield the official Python API definitions in page order."""
    soup = BeautifulSoup(html, "html.parser")
    body = soup.find("main") or soup.find("div", role="main")
    if body is None:
        raise ValueError("Official document has no main content region.")
    seen = set()
    blocks = body.select("dl.py")
    for block in blocks:
        kind = next((k for k in block.get("class", []) if k in KINDS), None)
        terms = block.find_all("dt", recursive=False)
        identifiers = [t["id"] for t in terms if t.get("id")]
        if kind is None or not identifiers:
            raise ValueError("Unrecognized API definition in official document.")
        identifier = identifiers[0]
        if identifier in seen:
            raise ValueError("Duplicate API anchor: " + identifier)
        seen.add(identifier)
        signatures = []
        for term in terms:
            term = deepcopy(term)
            for extra in term.select(".headerlink, .viewcode-link"):
                extra.decompose()
            signatures.append(re.sub(r"\s+", " ", term.get_text()).strip())
        description = block.find("dd", recursive=False)
        if description is None:
            raise ValueError("API definition has no description container: " + identifier)
        description = deepcopy(description)
        # Each class member gets its own document, avoiding repeated class bodies.
        for nested in description.select("dl.py"):
            nested.decompose()
        text = (
            "# "
            + identifier
            + "\n\n```python\n"
            + "\n".join(signatures)
            + "\n```\n\n"
            + to_markdown(description, page_url)
        )
        yield identifier, text


def rebuild(output):
    sources = json.loads((HERE / "sources.json").read_text())
    index = json.loads((HERE / "api_index.json").read_text())
    chunks = {}
    for page in sources["pages"]:
        html = (HERE / page["file"]).read_bytes()
        if hashlib.sha256(html).hexdigest() != page["sha256"]:
            raise ValueError(f"Official HTML checksum mismatch: {page['file']}")
        for name, text in split_page(html, page["source"]):
            if name not in index:
                continue
            record = index[name]
            data = text.encode("utf-8")
            if name in chunks or hashlib.sha256(data).hexdigest() != record["sha256"]:
                raise ValueError(f"Chunk differs from the indexed official API: {name}")
            chunks[name] = data
    if chunks.keys() != index.keys():
        raise ValueError(
            f"Missing official API definitions: {sorted(index.keys() - chunks.keys())}"
        )
    for name, data in chunks.items():
        dest = output / Path(index[name]["chunk"]).relative_to("chunks")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
    return len(chunks)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=HERE / "chunks")
    print(f"Wrote {rebuild(parser.parse_args().output)} API chunks.")
