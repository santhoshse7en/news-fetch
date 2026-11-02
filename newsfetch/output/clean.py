"""Clean an article-body DOM node for HTML / Markdown output."""

from __future__ import annotations

import copy
import html
import re

from lxml.html import HtmlElement, tostring

from newsfetch.normalize.url import absolutize
from newsfetch.strategies.heuristic import _is_unlikely

_DROP_TAGS = (
    "script", "style", "noscript", "template", "svg", "canvas", "iframe", "object", "embed",
    "form", "button", "input", "select", "textarea", "nav", "aside", "footer", "header",
)
_UNWRAP_TAGS = ("span", "font", "center")
_KEEP_ATTRS = {
    "a": ("href", "title"),
    "img": ("src", "alt", "title"),
    "td": ("colspan", "rowspan"),
    "th": ("colspan", "rowspan"),
    "ol": ("start",),
    "time": ("datetime",),
    "pre": ("class",),
    "code": ("class",),
}
_VOID_OR_MEDIA = {"img", "br", "hr"}
_HIDDEN_STYLE_RE = re.compile(r"display\s*:\s*none|visibility\s*:\s*hidden", re.I)


def _image_src(img: HtmlElement) -> str | None:
    src = img.get("src") or img.get("data-src") or img.get("data-original")
    if (not src or src.startswith("data:")) and img.get("srcset"):
        src = img.get("srcset", "").split(",")[0].strip().split(" ")[0]
    if not src or src.startswith("data:"):
        return None
    return src


def clean_body(node: HtmlElement, *, base_url: str | None = None) -> HtmlElement:
    """Return a cleaned *copy* of ``node``: boilerplate removed, attributes allow-listed,
    URLs absolutized. The original document is not modified."""
    root = copy.deepcopy(node)
    root.tail = None

    for el in list(root.iter(*_DROP_TAGS)):
        if el is not root:
            el.drop_tree()  # drop_tree keeps the tail text, unlike parent.remove()
    for el in list(root.iter()):
        if el is root or not isinstance(el.tag, str) or el.getparent() is None:
            continue
        hidden = (
            el.get("hidden") is not None
            or el.get("aria-hidden") == "true"
            or _HIDDEN_STYLE_RE.search(el.get("style", ""))
        )
        if hidden or _is_unlikely(el):
            el.drop_tree()
    for el in list(root.iter()):  # comments / processing instructions
        if not isinstance(el.tag, str) and el.getparent() is not None:
            el.drop_tree()

    for img in list(root.iter("img")):
        src = _image_src(img)
        if src is None:
            img.drop_tree()
            continue
        img.set("src", absolutize(base_url, src) if base_url else src)
    for a in list(root.iter("a")):
        href = (a.get("href") or "").strip()
        if not href or href.lower().startswith(("javascript:", "data:", "vbscript:")):
            a.drop_tag()  # keep the link text
            continue
        a.set("href", absolutize(base_url, href) if base_url else href)

    for el in list(root.iter(*_UNWRAP_TAGS)):
        if el is not root:
            el.drop_tag()

    for el in root.iter():
        if not isinstance(el.tag, str):
            continue
        keep = _KEEP_ATTRS.get(el.tag, ())
        for attr in list(el.attrib):
            if attr not in keep:
                del el.attrib[attr]

    # Drop elements left empty (no text, no media), innermost first
    for el in reversed(list(root.iter())):
        if el is root or not isinstance(el.tag, str) or el.tag in _VOID_OR_MEDIA:
            continue
        if not (el.text_content() or "").strip() and not any(True for _ in el.iter("img")):
            el.drop_tree()
    return root


def to_html(node: HtmlElement) -> str:
    return tostring(node, encoding="unicode", method="html").strip()


def text_to_html(text: str) -> str:
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    return "".join(f"<p>{html.escape(p)}</p>" for p in paras)
