"""Render a cleaned article-body node as Markdown (CommonMark + GFM tables). No dependencies."""

from __future__ import annotations

import re

from lxml.html import HtmlElement

_HEADINGS = {"h1": 1, "h2": 2, "h3": 3, "h4": 4, "h5": 5, "h6": 6}
_CONTAINERS = {"div", "section", "article", "main", "body", "html", "dl", "dd", "dt", "details", "summary"}
_BLOCKS = set(_HEADINGS) | _CONTAINERS | {
    "p", "ul", "ol", "blockquote", "pre", "hr", "table", "figure", "figcaption",
}
_WS_RE = re.compile(r"\s+")
_ESCAPE_RE = re.compile(r"([\\`*_\[\]])")
_BLOCK_START_RE = re.compile(r"^(#|>|[-+] )")
_ORDERED_START_RE = re.compile(r"^(\d+)([.)] )")
_LIST_ITEM_RE = re.compile(r"^(?:[-+] |\d+[.)] )")
# Hard line break placeholder survives whitespace collapsing
_BR = "\x00"


def _esc(text: str) -> str:
    return _ESCAPE_RE.sub(r"\\\1", text)


def _finish_inline(text: str) -> str:
    text = _WS_RE.sub(" ", text).strip()
    text = text.replace(f" {_BR} ", _BR).replace(f"{_BR} ", _BR).replace(f" {_BR}", _BR)
    text = text.strip(_BR).replace(_BR, "  \n")
    if _BLOCK_START_RE.match(text):
        text = "\\" + text
    else:
        # Backslash can't escape a digit in CommonMark; escape the delimiter instead ("1\.")
        text = _ORDERED_START_RE.sub(r"\1\\\2", text, count=1)
    return text


def _tag(el) -> str | None:
    return el.tag if isinstance(el.tag, str) else None


def _inline_children(el: HtmlElement) -> str:
    parts = [_esc(el.text or "")]
    for child in el:
        if _tag(child):
            parts.append(_inline(child))
        parts.append(_esc(child.tail or ""))
    return "".join(parts)


def _inline(el: HtmlElement) -> str:
    tag = _tag(el)
    if tag == "br":
        return _BR
    if tag == "img":
        alt = _WS_RE.sub(" ", el.get("alt", "")).strip()
        return f"![{_esc(alt)}]({el.get('src', '')})"
    inner = _inline_children(el)
    if tag == "a":
        text = _WS_RE.sub(" ", inner).strip()
        href = el.get("href", "")
        return f"[{text or href}]({href})" if href else inner
    if tag in {"strong", "b"} and inner.strip():
        return f"**{inner.strip()}**"
    if tag in {"em", "i", "cite"} and inner.strip():
        return f"*{inner.strip()}*"
    if tag == "code":
        code = el.text_content()
        return f"`{code}`" if "`" not in code else f"`` {code} ``"
    if tag in {"del", "s", "strike"} and inner.strip():
        return f"~~{inner.strip()}~~"
    return inner


def _render_blocks(el: HtmlElement, out: list[str]) -> None:
    buf: list[str] = []

    def flush() -> None:
        text = _finish_inline("".join(buf))
        buf.clear()
        if text:
            out.append(text)

    buf.append(_esc(el.text or ""))
    for child in el:
        tag = _tag(child)
        if tag is None:
            pass
        elif tag in _BLOCKS:
            flush()
            _render_block(child, out)
        else:
            buf.append(_inline(child))
        buf.append(_esc(child.tail or ""))
    flush()


def _render_list(el: HtmlElement, out: list[str], ordered: bool) -> None:
    start = int(el.get("start", "1")) if (el.get("start") or "").isdigit() else 1
    items: list[str] = []
    for n, li in enumerate((c for c in el if _tag(c) == "li"), start=start):
        marker = f"{n}. " if ordered else "- "
        parts: list[str] = []
        _render_blocks(li, parts)
        # Nested lists stay tight under their item; other blocks are separated by a blank line
        body = parts[0] if parts else ""
        for part in parts[1:]:
            body += ("\n" if _LIST_ITEM_RE.match(part) else "\n\n") + part
        if not body:
            continue
        indent = " " * len(marker)
        lines = body.split("\n")
        items.append(marker + lines[0] + "".join(f"\n{indent}{line}" if line else "\n" for line in lines[1:]))
    if items:
        out.append("\n".join(items))


def _render_table(el: HtmlElement, out: list[str]) -> None:
    rows = []
    for tr in el.iter("tr"):
        cells = [_finish_inline(_inline_children(c)).replace("|", "\\|").replace("\n", " ")
                 for c in tr if _tag(c) in {"td", "th"}]
        if cells:
            rows.append(cells)
    if not rows:
        return
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    lines = ["| " + " | ".join(rows[0]) + " |", "|" + "---|" * width]
    lines += ["| " + " | ".join(r) + " |" for r in rows[1:]]
    out.append("\n".join(lines))


def _render_block(el: HtmlElement, out: list[str]) -> None:
    tag = _tag(el)
    if tag in _HEADINGS:
        text = _finish_inline(_inline_children(el))
        if text:
            out.append("#" * _HEADINGS[tag] + " " + text)
    elif tag == "p" or tag == "figcaption":
        text = _finish_inline(_inline_children(el))
        if text:
            out.append(f"*{text}*" if tag == "figcaption" else text)
    elif tag in {"ul", "ol"}:
        _render_list(el, out, ordered=tag == "ol")
    elif tag == "blockquote":
        inner: list[str] = []
        _render_blocks(el, inner)
        if inner:
            out.append("\n".join(f"> {line}" if line else ">" for line in "\n\n".join(inner).split("\n")))
    elif tag == "pre":
        code = el.text_content().strip("\n")
        lang = ""
        for node in (el, *el.iter("code")):
            match = re.search(r"(?:language|lang)-([\w+-]+)", node.get("class", ""))
            if match:
                lang = match.group(1)
                break
        fence = "````" if "```" in code else "```"
        out.append(f"{fence}{lang}\n{code}\n{fence}")
    elif tag == "hr":
        out.append("---")
    elif tag == "table":
        _render_table(el, out)
    else:  # containers, figure
        _render_blocks(el, out)


def to_markdown(node: HtmlElement) -> str:
    """Markdown for a (cleaned) body node; blocks separated by blank lines."""
    out: list[str] = []
    _render_block(node, out)
    return "\n\n".join(block for block in out if block.strip()).strip()


def text_to_markdown(text: str) -> str:
    """Markdown for plain paragraph text (``\\n\\n``-separated), e.g. JSON-LD ``articleBody``."""
    paras = (_finish_inline(_esc(p)) for p in text.split("\n\n"))
    return "\n\n".join(p for p in paras if p)
