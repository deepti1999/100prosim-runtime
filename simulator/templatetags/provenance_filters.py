import re

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()

# Remove workbook-style numeric citations, including variants like:
#   [9.224]
#   [9.85, S. 21]
#   [9.182 Seite 9]
#   [122]
_BRACKET_CITATION_RE = re.compile(r"\s*\[[^\]]*\d[^\]]*\]")
_SPACE_BEFORE_PUNCT_RE = re.compile(r"\s+([,.;:])")
_GEMAESS_REF_RE = re.compile(r"gemäß\s*\[[^\]]+\]", re.IGNORECASE)
_VGL_REF_RE = re.compile(r"vgl\.\s*\[[^\]]+\]", re.IGNORECASE)
_INLINE_CITATION_RE = re.compile(r"\[[^\]]*\d[^\]]*\]")
_DUPLICATE_GEMAESS_LABEL_RE = re.compile(
    r"(gemäß\s+)([^,]+),\s*\2([,.;:])",
    re.IGNORECASE,
)


def _title_from_description(description):
    if not description:
        return None
    m = re.search(r'"([^"]+)"', str(description))
    if m:
        return m.group(1)
    return str(description).strip()


def _label_from_url(url):
    if not url:
        return None
    cleaned = str(url).rstrip("/").split("/")[-1]
    return cleaned or None


def _display_name(ref):
    return (
        ref.get("label")
        or _title_from_description(ref.get("description"))
        or _label_from_url(ref.get("url"))
        or "Quelle unten"
    )


def _pick_ref_name(line, refs):
    if not refs:
        return "Quelle unten"
    lower = line.lower()
    for ref in refs:
        label = ref.get("label") or ""
        if "solartherm" in lower and "solartherm" in label.lower():
            return _display_name(ref)
        if ("photovoltaik" in lower or "pv" in lower) and "pv" in label.lower():
            return _display_name(ref)
    return _display_name(refs[0])


def _pick_ref_name_for_context(context, refs, fallback_index):
    if not refs:
        return "Quelle unten", fallback_index

    lower = context.lower()
    if "studie" in lower or "agora" in lower:
        for ref in refs:
            haystack = f"{(ref.get('label') or '').lower()} {(ref.get('description') or '').lower()}"
            if "agora" in haystack:
                return _display_name(ref), fallback_index
    if (
        "datenteil" in lower
        or "datenanhang" in lower
        or "modulflächen" in lower
        or "datei" in lower
    ):
        for ref in refs:
            if str(ref.get("url") or "").lower().endswith(".xlsx"):
                return _display_name(ref), fallback_index

    for idx, ref in enumerate(refs):
        label = (ref.get("label") or "").lower()
        description = (ref.get("description") or "").lower()
        haystack = f"{label} {description}"
        if "solartherm" in lower and "solartherm" in haystack:
            return _display_name(ref), fallback_index
        if ("photovoltaik" in lower or "pv" in lower) and "pv" in haystack:
            return _display_name(ref), fallback_index
        if "dach" in lower and "dach" in haystack:
            return _display_name(ref), fallback_index
        if "kollektor" in lower and "kollektor" in haystack:
            return _display_name(ref), fallback_index
        if "potenzial" in lower and "agora" in haystack:
            return _display_name(ref), fallback_index

    idx = min(fallback_index, len(refs) - 1)
    next_index = min(fallback_index + 1, len(refs) - 1)
    return _display_name(refs[idx]), next_index


def _replace_scoped_refs(text, pattern, refs):
    if not refs:
        return text

    next_index = 0

    def repl(match):
        nonlocal next_index
        start = max(0, match.start() - 80)
        end = min(len(text), match.end() + 80)
        context = text[start:end]
        name, next_index = _pick_ref_name_for_context(context, refs, next_index)
        keyword = "vgl." if match.group(0).lower().startswith("vgl.") else "gemäß"
        return f"{keyword} {name}"

    return pattern.sub(repl, text)


def _replace_inline_citations(text, refs):
    if not refs:
        return clean_provenance_note(text)

    next_index = 0

    def repl(match):
        nonlocal next_index
        start = max(0, match.start() - 80)
        end = min(len(text), match.end() + 80)
        context = text[start:end]
        name, next_index = _pick_ref_name_for_context(context, refs, next_index)
        return name

    return _INLINE_CITATION_RE.sub(repl, text)


def _dedupe_adjacent_labels(text):
    return _DUPLICATE_GEMAESS_LABEL_RE.sub(r"\1\2\3", text)


@register.filter
def clean_provenance_note(value):
    """Remove workbook-style bracket citations from user-facing note text.

    Example:
      'Gemäß GENESIS [9.224], Tabelle ...' -> 'Gemäß GENESIS, Tabelle ...'
    """
    if not value:
        return value

    text = str(value)
    text = _BRACKET_CITATION_RE.sub("", text)
    text = _SPACE_BEFORE_PUNCT_RE.sub(r"\1", text)
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


@register.filter
def render_provenance_note(value, source_refs):
    """Render note text into cleaner user-facing prose.

    Uses section-specific source labels to avoid broken phrases like
    `gemäß .` after workbook citation markers are removed.
    """
    if not value:
        return value

    refs = list(source_refs or [])
    refs_by_section = {"status": [], "ziel": []}
    for ref in refs:
        section = ref.get("section")
        if section in refs_by_section:
            refs_by_section[section].append(ref)

    current_section = None
    rendered_parts = []
    for raw_part in str(value).split("\n\n"):
        part = raw_part.strip()
        if not part:
            continue
        lower = part.lower()
        if lower.startswith("- status-ansatz:"):
            current_section = "status"
        elif lower.startswith("- ziel-ansatz:"):
            current_section = "ziel"

        section_refs = refs_by_section.get(current_section or "", [])
        part = _replace_scoped_refs(part, _GEMAESS_REF_RE, section_refs)
        part = _replace_scoped_refs(part, _VGL_REF_RE, section_refs)
        part = _replace_inline_citations(part, section_refs)
        part = _dedupe_adjacent_labels(part)
        part = clean_provenance_note(part)
        rendered_parts.append(escape(part))

    return mark_safe("<br><br>".join(rendered_parts))
