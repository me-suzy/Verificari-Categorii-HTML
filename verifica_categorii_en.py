#!/usr/bin/env python3
"""Audit category pages for the English Leadership website. Read-only."""
from __future__ import annotations

import argparse
import html
import re
import sys
from collections import Counter
from pathlib import Path

ROOT_DEFAULT = Path(r"E:\Carte\BB\17 - Site Leadership\Principal\en")
CATEGORY_FILES = """
leadership-and-attitude.html leadership-magic.html successful-leadership.html
hr-human-resources.html leadership-laws.html total-leadership.html leadership-that-lasts.html
leadership-principles.html leadership-plus.html qualities-of-a-leader.html top-leadership.html
leadership-impact.html personal-development.html leadership-skills-and-abilities.html
real-leadership.html basic-leadership.html leadership-360.html leadership-pro.html
leadership-expert.html leadership-know-how.html leadership-journal.html alpha-leadership.html
leadership-on-off.html leadership-deluxe.html leadership-xxl.html leadership-50-extra.html
leadership-fusion.html leadership-v8.html leadership-x3-silver.html leadership-q2-sensitive.html
leadership-t7-hybrid.html leadership-n6-celsius.html leadership-s4-quartz.html
leadership-gt-accent.html leadership-fx-intensive.html leadership-iq-light.html
leadership-7th-edition.html leadership-xs-analytics.html leadership-z3-extended.html
leadership-ex-elite.html leadership-w3-integra.html leadership-sx-experience.html
leadership-y5-superzoom.html performance-ex-flash.html leadership-mindware.html
leadership-r2-premiere.html leadership-y4-titanium.html leadership-quantum-xx.html
python-scripts-examples.html
""".split()

EXCLUDED_CATEGORIES = {"python-scripts-examples.html"}
NON_ARTICLE_FILES = {
    "index.html", "subscription-membership.html", "contact.html", "unsubscribe.html",
    "directory.html", "events.html", "feedback.html", "feedback_thankyou.html",
    "newsletter.html", "newsletter_confirm.html", "partners.html", "film-scenarios.html",
    "terms-and-conditions.html", "training-and-coaching.html",
    "romania-images-from-the-metropolitan-museum-iasi-underground-galleries.html",
    "search.html", "privacy-policy.html",
}

CATEGORY_LINK_RE = re.compile(
    r"<a\b(?=[^>]*\bhref\s*=\s*[\"'][^\"']*/(?P<slug>[^/\"'?#]+\.html)[^\"']*[\"'])"
    r"(?=[^>]*\brel\s*=\s*[\"']category\s+tag[\"'])[^>]*>", re.I | re.S)
LIST_LINK_RE = re.compile(
    r'<a\s+href=["\']https?://[^"\']+/(?P<slug>[^/"\'?#]+\.html)["\']\s+class=["\']linkMare["\']\s*>(?P<title>.*?)</a>', re.I | re.S)
H1_RE = re.compile(r'<h1\b[^>]*class=["\'][^"\']*\bden_articol\b[^"\']*["\'][^>]*>(?P<title>.*?)</h1>', re.I | re.S)
CANONICAL_RE = re.compile(
    r'<link\b(?=[^>]*\brel\s*=\s*["\']canonical["\'])'
    r'(?=[^>]*\bhref\s*=\s*["\']https?://[^"\']+/(?P<slug>[^/"\'?#]+\.html)[^"\']*["\'])[^>]*>',
    re.I | re.S,
)
RO_FLAG_RE = re.compile(
    r'<a\s+href=["\']https?://[^"\']+/(?P<slug>[^/"\'?#]+\.html)["\'][^>]*>\s*'
    r'<img\b(?=[^>]*\btitle=["\']ro["\'])[^>]*>', re.I | re.S)


def read_html(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def text_key(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html.unescape(value))).strip().casefold()


def article_title(path: Path) -> str:
    match = H1_RE.search(read_html(path))
    return text_key(match.group("title")) if match else ""


def category_names() -> list[str]:
    return [name for name in CATEGORY_FILES if name not in EXCLUDED_CATEGORIES]


def canonical_slug(path: Path) -> str:
    match = CANONICAL_RE.search(read_html(path))
    return match.group("slug").casefold() if match else ""


def article_paths(root: Path, category_slugs: set[str]) -> list[Path]:
    return [
        path for path in root.glob("*.html")
        if path.name.casefold() not in category_slugs
        and path.name.casefold() not in NON_ARTICLE_FILES
    ]


def invalid_filename_articles(root: Path, category_slugs: set[str]) -> list[tuple[Path, str]]:
    """Find unreferenced typo copies whose own canonical URL names another file.

    ``index.html`` is deliberately ignored: current articles may be previewed
    there, and that must never keep an accidental duplicate alive.
    """
    pages = article_paths(root, category_slugs)
    category_pages = [root / name for name in category_names() if (root / name).is_file()]
    invalid: list[tuple[Path, str]] = []
    for path in pages:
        canonical = canonical_slug(path)
        if not canonical or canonical == path.name.casefold() or not (root / canonical).is_file():
            continue
        wrong_name = path.name.casefold()
        listed = any(wrong_name in category_listing(read_html(category))[0] for category in category_pages)
        href_re = re.compile(rf'https?://[^"\']*/{re.escape(wrong_name)}(?=["\'?#])', re.I)
        referenced_elsewhere = any(
            other.name.casefold() != "index.html" and other != path and href_re.search(read_html(other))
            for other in root.glob("*.html")
        )
        if not listed and not referenced_elsewhere:
            invalid.append((path, canonical))
    return sorted(invalid, key=lambda item: item[0].name.casefold())


def collect_sources(root: Path, category_slugs: set[str]) -> dict[str, set[Path]]:
    result = {slug: set() for slug in category_slugs}
    # Deliberately scans only the main EN folder, never FISIERE PYTHON HTML.
    for path in article_paths(root, category_slugs):
        # A duplicate file with a misspelled filename must not be treated as a
        # second article.  Its canonical URL identifies the real article.
        canonical = canonical_slug(path)
        if canonical and canonical != path.name.casefold() and (root / canonical).is_file():
            continue
        for match in CATEGORY_LINK_RE.finditer(read_html(path)):
            slug = match.group("slug").casefold()
            if slug in result:
                result[slug].add(path)
    return result


def category_listing(page: str) -> tuple[set[str], set[str], list[str]]:
    entries = list(LIST_LINK_RE.finditer(page))
    slugs = {item.group("slug").casefold() for item in entries}
    titles = {text_key(item.group("title")) for item in entries}
    counts = Counter(item.group("slug").casefold() for item in entries)
    return slugs, titles, sorted(name for name, count in counts.items() if count > 1)


def ro_check(en_root: Path, article_name: str, en_category: str) -> str:
    """Uses the Romanian article's own category tag as the canonical RO check."""
    article_path = en_root / article_name
    if not article_path.is_file():
        return "RO check unavailable"
    article_flag = RO_FLAG_RE.search(read_html(article_path))
    if not article_flag:
        return "RO counterpart missing"
    ro_article = article_flag.group("slug")
    ro_article_path = en_root.parent / "ro" / ro_article
    if not ro_article_path.is_file():
        return "RO article missing"
    ro_tag = CATEGORY_LINK_RE.search(read_html(ro_article_path))
    if not ro_tag:
        return "RO article category tag missing"
    ro_category = ro_tag.group("slug")
    ro_path = en_root.parent / "ro" / ro_category
    confirmed = ro_path.is_file() and ro_article.casefold() in category_listing(read_html(ro_path))[0]
    return f"RO category: {ro_category} ({'confirmed' if confirmed else 'not confirmed'})"


def ro_canonical_category(en_root: Path, article_name: str) -> str:
    """Romanian category declared by the corresponding Romanian article."""
    article_path = en_root / article_name
    flag = RO_FLAG_RE.search(read_html(article_path)) if article_path.is_file() else None
    if not flag:
        return ""
    ro_article_path = en_root.parent / "ro" / flag.group("slug")
    tag = CATEGORY_LINK_RE.search(read_html(ro_article_path)) if ro_article_path.is_file() else None
    return tag.group("slug").casefold() if tag else ""


def ro_category_for_en_category(en_root: Path, category: str) -> str:
    path = en_root / category
    flag = RO_FLAG_RE.search(read_html(path)) if path.is_file() else None
    return flag.group("slug").casefold() if flag else ""


def audit(root: Path) -> tuple[list[tuple[str, str]], list[tuple[str, str, tuple[str, ...]]], list[tuple[str, str]]]:
    categories = category_names()
    slugs = {name.casefold() for name in categories}
    sources = collect_sources(root, slugs)
    listings = {category: category_listing(read_html(root / category)) for category in categories if (root / category).is_file()}
    listed_anywhere: dict[str, set[str]] = {}
    declared: dict[str, set[str]] = {}
    for category, (listed, _titles, _dupes) in listings.items():
        for slug in listed:
            listed_anywhere.setdefault(slug, set()).add(category)
    for category, paths in sources.items():
        for path in paths:
            declared.setdefault(path.name.casefold(), set()).add(category)

    missing: list[tuple[str, str]] = []
    wrong_category: list[tuple[str, str, tuple[str, ...]]] = []
    extra: list[tuple[str, str]] = []
    for category in categories:
        if category not in listings:
            print(f"MISSING CATEGORY FILE: {category}")
            continue
        listed, titles, _dupes = listings[category]
        for path in sources[category.casefold()]:
            slug, title = path.name.casefold(), article_title(path)
            if slug not in listed and title not in titles:
                elsewhere = listed_anywhere.get(slug, set()) - {category}
                if elsewhere:
                    wrong_category.append((category, path.name, tuple(sorted(elsewhere))))
                else:
                    missing.append((category, path.name))
        for slug in listed:
            tags = declared.get(slug, set()) - {category}
            if tags:
                wrong_category.append((category, slug, tuple(sorted(tags))))
            elif slug not in declared:
                extra.append((category, slug))
    return sorted(set(missing)), sorted(set(wrong_category)), sorted(set(extra))


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT_DEFAULT)
    root = parser.parse_args().root.resolve()
    missing, wrong, extra = audit(root)
    print(f"Checked: {len(category_names())} categories.")
    invalid_names = invalid_filename_articles(root, {name.casefold() for name in category_names()})
    for path, canonical in invalid_names:
        print(f"\nINVALID FILENAME (safe to delete): {path.name}\n  canonical URL: {canonical}\n  not referenced by category/article pages (index.html ignored)")
    # Count all category pages that disagree with the same RO-canonical category.
    wrong_count: Counter[str] = Counter()
    for category, article, _tags in wrong:
        canonical = ro_canonical_category(root, article)
        if canonical and ro_category_for_en_category(root, category) != canonical:
            wrong_count[article] += 1
    for category, article in missing:
        print(f"\n{category}\n  MISSING: {article}\n  {ro_check(root, article, category)}")
    for category, article, tags in wrong:
        correct_category = tags[0] if tags else category
        canonical = ro_canonical_category(root, article)
        listed_ro = ro_category_for_en_category(root, category)
        messages: list[str] = []
        if canonical and listed_ro == canonical and tags:
            messages.append("ARTICOLUL ARE LINK-URL ÎN ALTĂ CATEGORIE")
        if wrong_count[article]:
            messages.append(f"LINK-UL SE AFLĂ ÎN {wrong_count[article]} HTML CATEGORII GREȘITE")
        suffix = "\n  " + "\n  ".join(messages) if messages else ""
        print(f"\n{category}\n  WRONG CATEGORY: {article} — tag declared in {', '.join(tags)}\n  {ro_check(root, article, correct_category)}{suffix}")
    for category, article in extra:
        print(f"\n{category}\n  LISTED, BUT NO CATEGORY TAG: {article}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
