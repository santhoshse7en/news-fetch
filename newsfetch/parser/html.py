"""HTML document wrapper around lxml."""

from __future__ import annotations

from lxml import html as lhtml
from lxml.html import HtmlElement

from newsfetch.errors import ParseError

_UPPERCASE = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
_LOWERCASE = "abcdefghijklmnopqrstuvwxyz"


class Document:
    """Parsed HTML document with helper accessors."""

    def __init__(self, root: HtmlElement, *, base_url: str | None = None) -> None:
        self.root = root
        self.base_url = base_url

    @classmethod
    def from_html(cls, content: str | bytes, *, base_url: str | None = None) -> Document:
        try:
            if isinstance(content, bytes):
                # Prefer UTF-8; fall back to lxml's encoding sniff for legacy pages
                try:
                    text = content.decode("utf-8")
                except UnicodeDecodeError:
                    root = lhtml.fromstring(content)
                else:
                    root = lhtml.fromstring(text)
            else:
                root = lhtml.fromstring(content)
        except Exception as exc:  # lxml raises varied parse errors
            raise ParseError(f"Failed to parse HTML: {exc}") from exc

        if root is None:
            raise ParseError("Failed to parse HTML: empty document")

        if not isinstance(root, HtmlElement):
            raise ParseError("Failed to parse HTML: unexpected root type")

        return cls(root, base_url=base_url)

    def css(self, selector: str) -> list[HtmlElement]:
        try:
            return list(self.root.cssselect(selector))
        except ImportError:
            raise  # missing cssselect must not look like "no matches"
        except Exception:
            return []

    def xpath(self, expr: str) -> list:
        try:
            return list(self.root.xpath(expr))
        except Exception:
            return []

    def meta_content(self, *, property: str | None = None, name: str | None = None) -> str | None:
        if property:
            nodes = self.css(f'meta[property="{property}"]')
            if not nodes:
                prop = property.lower()
                nodes = self.xpath(
                    f'//meta[translate(@property,"{_UPPERCASE}","{_LOWERCASE}")="{prop}"]'
                )
        elif name:
            nodes = self.css(f'meta[name="{name}"]')
            if not nodes:
                key = name.lower()
                nodes = self.xpath(
                    f'//meta[translate(@name,"{_UPPERCASE}","{_LOWERCASE}")="{key}"]'
                )
        else:
            return None

        for node in nodes:
            content = node.get("content")
            if content and content.strip():
                return content.strip()
        return None

    def text_content(self, node: HtmlElement | None = None) -> str:
        target = node if node is not None else self.root
        return " ".join(t.strip() for t in target.itertext() if t and t.strip())
