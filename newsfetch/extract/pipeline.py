"""Multi-strategy extraction pipeline (evidence → rank → confidence → article)."""

from __future__ import annotations

from typing import Any

from lxml.html import tostring

from newsfetch.config import Config
from newsfetch.detect.language import detect_language
from newsfetch.detect.page_type import detect_page_type
from newsfetch.errors import LowConfidenceExtractionError
from newsfetch.extract.rank import (
    build_confidence,
    candidates_to_evidence,
    fuse_title_evidence,
    rank_field,
)
from newsfetch.models.article import Article, ExtractionTrace
from newsfetch.models.evidence import ExtractionReport
from newsfetch.nlp import extract_keywords, summarize
from newsfetch.normalize.date import date_from_url, parse_date
from newsfetch.normalize.text import normalize_whitespace
from newsfetch.normalize.url import absolutize, canonicalize, domain_from_url
from newsfetch.parser.html import Document
from newsfetch.strategies.heuristic import extract_content_heuristic, strip_boilerplate_nodes
from newsfetch.strategies.jsonld import extract_jsonld
from newsfetch.strategies.meta import extract_meta
from newsfetch.strategies.opengraph import extract_opengraph
from newsfetch.strategies.plugin import ExtractionStrategy
from newsfetch.strategies.semantic import extract_semantic

_WORDS_PER_MINUTE = 200


def _merge_maps(*maps: dict) -> dict:
    merged: dict = {}
    for m in maps:
        for key, values in m.items():
            merged.setdefault(key, []).extend(values)
    return merged


class Extractor:
    """Collect evidence from strategies, rank candidates, emit Article + confidence."""

    def __init__(
        self,
        config: Config | None = None,
        *,
        strategies: list[ExtractionStrategy] | None = None,
    ) -> None:
        self.config = config or Config()
        self._extra_strategies: list[ExtractionStrategy] = list(strategies or [])

    def register_strategy(self, strategy: ExtractionStrategy) -> None:
        """Register a custom extraction strategy (plugin)."""
        self._extra_strategies.append(strategy)

    def extract(self, html: str | bytes, url: str) -> Article:
        doc = Document.from_html(html, base_url=url)
        trace = ExtractionTrace() if self.config.debug else None

        jsonld = extract_jsonld(doc)
        og = extract_opengraph(doc)
        meta = extract_meta(doc)
        semantic = extract_semantic(doc)

        body_html = tostring(doc.root, encoding="unicode", method="html")
        body_doc = Document.from_html(body_html, base_url=url)
        strip_boilerplate_nodes(body_doc.root)
        heuristic_text = extract_content_heuristic(body_doc)

        plugin_maps = [s.extract(doc) for s in self._extra_strategies]
        merged = _merge_maps(jsonld, og, meta, semantic, *plugin_maps)
        merged.setdefault("text", []).extend(heuristic_text)

        if trace is not None:
            tried = ["json-ld", "opengraph", "meta", "semantic", "dom"]
            tried.extend(s.name for s in self._extra_strategies)
            trace.strategies_tried = tried
            for field_name, cands in merged.items():
                for c in cands:
                    trace.add(field_name, c.value, c.source, c.score)

        # Evidence → rank per field
        title_ev = fuse_title_evidence(candidates_to_evidence("title", merged.get("title", [])))
        title_f = rank_field("title", title_ev)

        desc_f = rank_field("description", candidates_to_evidence("description", merged.get("description", [])))
        authors_f = rank_field("authors", candidates_to_evidence("authors", merged.get("authors", [])))
        date_f = rank_field(
            "published_at",
            candidates_to_evidence("published_at", merged.get("published_at", [])),
            parse_dates=True,
        )
        mod_f = rank_field(
            "modified_at",
            candidates_to_evidence("modified_at", merged.get("modified_at", [])),
            parse_dates=True,
        )
        publisher_f = rank_field("publisher", candidates_to_evidence("publisher", merged.get("publisher", [])))
        section_f = rank_field("section", candidates_to_evidence("section", merged.get("section", [])))
        lang_f = rank_field("language", candidates_to_evidence("language", merged.get("language", [])))
        canon_f = rank_field(
            "canonical_url",
            candidates_to_evidence("canonical_url", merged.get("canonical_url", [])),
        )
        image_f = rank_field("image", candidates_to_evidence("image", merged.get("image", [])))
        content_f = rank_field("content", candidates_to_evidence("text", merged.get("text", [])))

        sources: dict[str, str] = {}

        title = title_f.value if isinstance(title_f.value, str) else None
        if title_f.source:
            sources["title"] = title_f.source

        description = desc_f.value if isinstance(desc_f.value, str) else None
        if desc_f.source:
            sources["description"] = desc_f.source

        authors = list(authors_f.value) if isinstance(authors_f.value, list) else []
        if authors_f.source:
            sources["authors"] = authors_f.source

        published_at = parse_date(date_f.value) if isinstance(date_f.value, str) else None
        if date_f.source:
            sources["published_at"] = date_f.source
        if published_at is None:
            published_at = date_from_url(url)
            if published_at:
                sources["published_at"] = "url.date"
                date_f.strategy = "url"
                date_f.source = "url.date"
                date_f.score = 0.55
                date_f.confidence = 0.55
                date_f.value = published_at.isoformat()
                date_f.candidates = max(date_f.candidates, 1)

        modified_at = parse_date(mod_f.value) if isinstance(mod_f.value, str) else None
        if mod_f.source:
            sources["modified_at"] = mod_f.source

        publisher = publisher_f.value if isinstance(publisher_f.value, str) else None
        if publisher_f.source:
            sources["publisher"] = publisher_f.source
        if not publisher:
            publisher = domain_from_url(url)
            if publisher:
                sources["publisher"] = "url.domain"
                publisher_f.strategy = "url"
                publisher_f.source = "url.domain"
                publisher_f.score = 0.4
                publisher_f.confidence = 0.4
                publisher_f.value = publisher
                publisher_f.candidates = max(publisher_f.candidates, 1)

        section = section_f.value if isinstance(section_f.value, str) else None
        if section_f.source:
            sources["section"] = section_f.source

        language = lang_f.value if isinstance(lang_f.value, str) else detect_language(doc, self.config.language)
        if lang_f.source:
            sources["language"] = lang_f.source

        canonical = absolutize(url, canon_f.value) if isinstance(canon_f.value, str) else url
        canonical = canonicalize(canonical or url, strip_tracking=self.config.strip_tracking_params)
        if canon_f.source:
            sources["canonical_url"] = canon_f.source

        image = absolutize(url, image_f.value) if isinstance(image_f.value, str) else None
        if image_f.source:
            sources["image"] = image_f.source

        text = normalize_whitespace(content_f.value) if isinstance(content_f.value, str) else None
        if content_f.source:
            sources["text"] = content_f.source
        if text:
            content_f.value = text
            content_f.signals.setdefault("word_count", len(text.split()))
            content_f.signals.setdefault("paragraph_count", text.count("\n\n") + 1)

        if text and len(text) < self.config.min_text_length and trace is not None:
            trace.notes.append(f"text shorter than min_text_length={self.config.min_text_length}")

        keywords_c = merged.get("keywords", [])
        if keywords_c:
            keywords = list(keywords_c[0].value) if isinstance(keywords_c[0].value, list) else []
            sources["keywords"] = keywords_c[0].source
        else:
            keywords = extract_keywords(text) if text else []
            if keywords:
                sources["keywords"] = "nlp.frequency"

        summary = summarize(text) if text else None
        if summary:
            sources["summary"] = "nlp.lead-sentences"

        word_count = len(text.split()) if text else 0
        reading_time = max(1, round(word_count / _WORDS_PER_MINUTE)) if word_count else 0

        page = detect_page_type(doc, url, has_article_body=bool(text and word_count >= 40))
        if trace is not None:
            trace.page_type_reasons = list(page.reasons)

        report = ExtractionReport(
            title=title_f,
            description=desc_f,
            content=content_f,
            authors=authors_f,
            date=date_f,
            image=image_f,
            publisher=publisher_f,
            canonical_url=canon_f,
        )
        confidence = build_confidence(report, page_type_confidence=page.confidence)

        if trace is not None:
            for field_name, fe in (
                ("title", title_f),
                ("description", desc_f),
                ("text", content_f),
                ("authors", authors_f),
                ("published_at", date_f),
                ("image", image_f),
                ("publisher", publisher_f),
            ):
                if not fe.source:
                    continue
                for cand in trace.candidates:
                    if cand.field == field_name and cand.source == fe.source:
                        cand.selected = True
                        cand.confidence = fe.confidence

        article = Article(
            url=url,
            canonical_url=canonical,
            title=title,
            description=description,
            text=text,
            authors=authors,
            published_at=published_at,
            modified_at=modified_at,
            publisher=publisher,
            language=language,
            image=image,
            images=[image] if image else [],
            keywords=keywords,
            section=section,
            summary=summary,
            word_count=word_count,
            reading_time_minutes=reading_time,
            page_type=page.page_type,
            is_article=page.is_article,
            sources=sources,
            confidence=confidence,
            extraction=report,
            metadata={"final_url": url, "page_type_reasons": list(page.reasons)},
            trace=trace,
        )

        self._enforce_strict(article)
        return article

    def _enforce_strict(self, article: Article) -> None:
        cfg = self.config
        wants_gate = (
            cfg.strict
            or cfg.min_confidence > 0
            or cfg.require_article_page
            or cfg.min_content_confidence is not None
            or cfg.min_title_confidence is not None
        )
        if not wants_gate:
            return

        failed: list[str] = []
        # strict=True with no explicit threshold → require modest title/content confidence
        threshold = cfg.min_confidence if cfg.min_confidence > 0 else (0.6 if cfg.strict else 0.0)

        if threshold > 0:
            failed.extend(article.confidence.below(threshold, fields=["title", "content"]))

        if cfg.min_content_confidence is not None and article.confidence.content < cfg.min_content_confidence:
            failed.append("content")
        if cfg.min_title_confidence is not None and article.confidence.title < cfg.min_title_confidence:
            failed.append("title")
        if cfg.require_article_page and not article.is_article:
            failed.append("page_type")

        seen: set[str] = set()
        uniq = [f for f in failed if not (f in seen or seen.add(f))]  # type: ignore[func-returns-value]
        uniq = []
        seen = set()
        for name in failed:
            if name not in seen:
                seen.add(name)
                uniq.append(name)

        if uniq:
            raise LowConfidenceExtractionError(
                f"Extraction confidence below threshold for: {', '.join(uniq)}",
                url=article.url,
                confidence=article.confidence,
                failed_fields=uniq,
                article=article,
            )

    def extract_from_nodes(self, *args: Any, **kwargs: Any) -> Article:
        return self.extract(*args, **kwargs)
