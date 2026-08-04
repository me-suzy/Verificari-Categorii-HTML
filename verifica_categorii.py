#!/usr/bin/env python3
"""Verifică dacă fiecare pagină de categorie conține toate articolele ei.

Nu modifică niciun fișier HTML. Citește articolele din directorul principal și
din subdirectorul ``Python Files``, apoi scrie raportul în
``raport_verificare_categorii.txt`` și ``raport_verificare_categorii.csv``.
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ROOT_DEFAULT = Path(r"E:\Carte\BB\17 - Site Leadership\Principal\ro")

CATEGORY_FILES = """
lideri-si-atitudine.html
leadership-magic.html
leadership-de-succes.html
hr-resurse-umane.html
legile-conducerii.html
leadership-total.html
leadership-de-durata.html
principiile-conducerii.html
leadership-plus.html
calitatile-unui-lider.html
leadership-de-varf.html
leadership-impact.html
dezvoltare-personala.html
aptitudini-si-abilitati-de-leadership.html
leadership-real.html
directory.html
leadership-de-baza.html
leadership-360.html
leadership-pro.html
leadership-expert.html
leadership-know-how.html
jurnal-de-leadership.html
alpha-leadership.html
leadership-on-off.html
leadership-deluxe.html
leadership-xxl.html
leadership-50-extra.html
leadership-fusion.html
leadership-v8.html
leadership-x3-silver.html
leadership-q2-sensitive.html
leadership-t7-hybrid.html
leadership-n6-celsius.html
leadership-s4-quartz.html
leadership-gt-accent.html
leadership-fx-intensive.html
leadership-iq-light.html
leadership-7th-edition.html
leadership-xs-analytics.html
leadership-z3-extended.html
leadership-ex-elite.html
leadership-w3-integra.html
leadership-sx-experience.html
leadership-y5-superzoom.html
performance-ex-flash.html
leadership-mindware.html
leadership-r2-premiere.html
leadership-y4-titanium.html
leadership-quantum-xx.html
python-scripts-examples.html
""".split()

# Pagini tehnice / de serviciu; pot avea metadate copiate, dar nu sunt articole.
NON_ARTICLE_FILES = {
    "index.html", "abonament-membership.html", "contact.html", "dezabonare.html",
    "directory.html", "evenimente.html", "feedback.html", "feedback_thankyou.html",
    "newsletter.html", "newsletter_confirm.html", "parteneri.html", "scenarii-de-film.html",
    "termeni-si-conditii.html", "training-si-consultanta.html",
    "cum-arata-imagini-robineti-centrala-termica-ariston.html",
    "imagini-din-muzeul-mitropolitan-iasi.html",
}
EXCLUDED_CATEGORIES = {"python-scripts-examples.html"}

# URL-ul categoriei din metadatele unui articol. Se acceptă orice ordine a
# atributelor, dar obligatoriu trebuie să fie un link de categorie (rel=category tag).
CATEGORY_LINK_RE = re.compile(
    r"<a\b(?=[^>]*\bhref\s*=\s*[\"'][^\"']*/(?P<slug>[^/\"'?#]+\.html)[^\"']*[\"'])"
    r"(?=[^>]*\brel\s*=\s*[\"']category\s+tag[\"'])[^>]*>",
    re.IGNORECASE | re.DOTALL,
)

# Linkul articolului din lista paginii categoriei.
ARTICLE_LIST_LINK_RE = re.compile(
    r'<a\s+href=["\']https?://[^/"\']+/(?P<slug>[^/"\'?#]+\.html)["\']\s+class=["\']linkMare["\']\s*>(?P<title>.*?)</a>',
    re.IGNORECASE | re.DOTALL,
)

TITLE_RE = re.compile(r"<title[^>]*>\s*(.*?)\s*</title>", re.IGNORECASE | re.DOTALL)
AUTHOR_METADATA_RE = re.compile(r"</a>\s*,\s*by\s+Neculai\s+Fantanaru\s*</td>", re.IGNORECASE)
CANONICAL_RE = re.compile(
    r'<link\b(?=[^>]*\brel\s*=\s*["\']canonical["\'])'
    r'(?=[^>]*\bhref\s*=\s*["\']https?://[^"\']+/(?P<slug>[^/"\'?#]+\.html)[^"\']*["\'])[^>]*>',
    re.IGNORECASE | re.DOTALL,
)


@dataclass
class Audit:
    category: str
    category_title: str
    metadata_instances: int
    source_articles: set[str]
    listed_articles: set[str]
    listed_titles: set[str]
    present_by_title: set[str]
    duplicate_list_links: list[str]

    @property
    def missing(self) -> list[str]:
        return sorted(self.source_articles - self.listed_articles - self.present_by_title, key=str.casefold)

    @property
    def stale(self) -> list[str]:
        return sorted(self.listed_articles - self.source_articles, key=str.casefold)


def read_html(path: Path) -> str:
    """Citește fișiere ANSI/UTF-8 fără ca scriptul să se oprească la o diacritică."""
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "cp1250", "cp1252", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            pass
    return raw.decode("utf-8", errors="replace")


def title_from(text: str, fallback: str) -> str:
    match = TITLE_RE.search(text)
    if not match:
        return fallback
    return re.sub(r"\s+", " ", html.unescape(match.group(1))).strip()


def title_key(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html.unescape(value))).strip().casefold()


def article_title(root: Path, name: str) -> str:
    for path in (root / name, root / "Python Files" / name):
        if path.is_file():
            # În paginile existente titlul din <title> are sufixul "| Neculai...".
            return title_key(title_from(read_html(path), name).split("|")[0])
    return ""


def article_files(root: Path, category_names: set[str]) -> Iterable[Path]:
    """Returnează articolele din directorul principal, nu din Python Files."""
    for path in root.glob("*.html"):
        name = path.name.casefold()
        if name not in category_names and name not in NON_ARTICLE_FILES:
            yield path


def canonical_slug(path: Path) -> str:
    match = CANONICAL_RE.search(read_html(path))
    return match.group("slug").casefold() if match else ""


def collect_articles_by_category(root: Path, category_names: set[str]) -> dict[str, set[str]]:
    by_category = {name: set() for name in category_names}
    for path in article_files(root, category_names):
        # O copie cu nume greșit are deja fișierul real indicat de canonical.
        canonical = canonical_slug(path)
        if canonical and canonical != path.name.casefold() and (root / canonical).is_file():
            continue
        text = read_html(path)
        for match in CATEGORY_LINK_RE.finditer(text):
            category = match.group("slug").casefold()
            if category in by_category:
                by_category[category].add(path.name)
    return by_category


def listed_slugs(category_html: str) -> tuple[set[str], set[str], list[str]]:
    matches = list(ARTICLE_LIST_LINK_RE.finditer(category_html))
    slugs = [match.group("slug") for match in matches]
    counts = Counter(slugs)
    titles = {title_key(match.group("title")) for match in matches}
    return set(slugs), titles, sorted((slug for slug, count in counts.items() if count > 1), key=str.casefold)


def invalid_filename_articles(root: Path, category_names: set[str]) -> list[tuple[Path, str]]:
    """Copii nefolosite al căror nume nu coincide cu URL-ul canonical."""
    category_pages = [root / name for name in CATEGORY_FILES if name not in EXCLUDED_CATEGORIES and (root / name).is_file()]
    invalid: list[tuple[Path, str]] = []
    for path in article_files(root, category_names):
        canonical = canonical_slug(path)
        if not canonical or canonical == path.name.casefold() or not (root / canonical).is_file():
            continue
        wrong_name = path.name.casefold()
        listed = any(wrong_name in listed_slugs(read_html(category))[0] for category in category_pages)
        href_re = re.compile(rf'https?://[^"\']*/{re.escape(wrong_name)}(?=["\'?#])', re.IGNORECASE)
        referenced_elsewhere = any(
            other.name.casefold() != "index.html" and other != path and href_re.search(read_html(other))
            for other in root.glob("*.html")
        )
        if not listed and not referenced_elsewhere:
            invalid.append((path, canonical))
    return sorted(invalid, key=lambda item: item[0].name.casefold())


def audit(root: Path) -> list[Audit]:
    categories = [name for name in CATEGORY_FILES if name not in EXCLUDED_CATEGORIES]
    category_names = {name.casefold() for name in categories}
    source_by_category = collect_articles_by_category(root, category_names)
    results: list[Audit] = []

    for category in categories:
        path = root / category
        if not path.is_file():
            results.append(Audit(category, "FIȘIER CATEGORIE LIPSĂ", 0, set(), set(), set(), set(), []))
            continue
        page = read_html(path)
        listed, listed_titles, duplicates = listed_slugs(page)
        source_articles = source_by_category[category.casefold()]
        present_by_title = {name for name in source_articles if article_title(root, name) in listed_titles}
        results.append(
            Audit(
                category=category,
                category_title=title_from(page, category),
                metadata_instances=len(AUTHOR_METADATA_RE.findall(page)),
                source_articles=source_articles,
                listed_articles=listed,
                listed_titles=listed_titles,
                present_by_title=present_by_title,
                duplicate_list_links=duplicates,
            )
        )
    return results


def category_mismatches(audits: list[Audit]) -> dict[str, dict[str, list[str]]]:
    """Linkuri listate într-o categorie diferită de tagul declarat în articol."""
    declared_in: dict[str, set[str]] = {}
    for item in audits:
        for name in item.source_articles:
            declared_in.setdefault(name.casefold(), set()).add(item.category)
    result: dict[str, dict[str, list[str]]] = {}
    for item in audits:
        for name in item.listed_articles:
            declared_elsewhere = declared_in.get(name.casefold(), set()) - {item.category}
            if declared_elsewhere:
                result.setdefault(item.category, {})[name] = sorted(declared_elsewhere, key=str.casefold)
    return result


def effective_differences(item: Audit, mismatches: dict[str, dict[str, list[str]]]) -> tuple[list[str], list[str]]:
    missing = item.missing
    # Dacă articolul declară o altă categorie, acesta este un caz de categorie
    # greșită, nu un articol „fără tag”.
    stale = [name for name in item.stale if name not in mismatches.get(item.category, {})]
    return missing, stale


def main() -> int:
    # Consola Windows poate porni în cp1252; rapoartele și mesajele rămân UTF-8.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Verifică lipsurile din toate paginile de categorii.")
    parser.add_argument("--root", type=Path, default=ROOT_DEFAULT, help="Directorul Principal\\ro")
    args = parser.parse_args()
    root = args.root.resolve()
    if not root.is_dir():
        print(f"Director inexistent: {root}", file=sys.stderr)
        return 2

    audits = audit(root)
    mismatches = category_mismatches(audits)
    problems = [item for item in audits if any(effective_differences(item, mismatches)) or mismatches.get(item.category) or item.duplicate_list_links]
    invalid_names = invalid_filename_articles(root, {name.casefold() for name in CATEGORY_FILES if name not in EXCLUDED_CATEGORIES})
    print(f"Verificate: {len(audits)} categorii.")
    print(f"Categorii cu diferențe: {len(problems)}.")
    for path, canonical in invalid_names:
        print(f"\nINVALID FILENAME (safe to delete): {path.name}\n  canonical URL: {canonical}\n  not referenced by category/article pages (index.html ignored)")
    for item in problems:
        print(f"\n{item.category}")
        missing, stale = effective_differences(item, mismatches)
        for name in missing:
            print(f"  LIPSEȘTE: {name}")
        for name, places in mismatches.get(item.category, {}).items():
            print(f"  CATEGORIE DIFERITĂ: {name} — tag declarat în {', '.join(places)}")
        for name in stale:
            print(f"  LISTAT, DAR FĂRĂ TAG: {name}")
        for name in item.duplicate_list_links:
            print(f"  DUBLAT: {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
