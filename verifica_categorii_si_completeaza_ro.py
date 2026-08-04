#!/usr/bin/env python3
"""Găsește și completează, la cerere, articole lipsă din paginile categorii.

Arată într-o fereastră toate lipsurile și completează toate articolele numai
după apăsarea butonului DA. Nu include ``Python Files`` și nici categoria
``python-scripts-examples.html``.
"""

from __future__ import annotations

import argparse
import html
import re
import sys
import tkinter as tk
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from tkinter import scrolledtext

from verifica_categorii import (
    CATEGORY_FILES,
    CATEGORY_LINK_RE,
    ROOT_DEFAULT,
    canonical_slug,
    invalid_filename_articles,
    read_html,
)


# Acestea sunt pagini speciale, nu articole pentru completarea categoriilor.
EXCLUDED_ARTICLES = {
    "abonament-membership.html", "contact.html", "dezabonare.html", "directory.html",
    "evenimente.html", "feedback.html", "feedback_thankyou.html", "newsletter.html",
    "newsletter_confirm.html", "parteneri.html", "scenarii-de-film.html",
    "termeni-si-conditii.html", "training-si-consultanta.html",
    "cum-arata-imagini-robineti-centrala-termica-ariston.html",
    "imagini-din-muzeul-mitropolitan-iasi.html",
    "index.html",
}
EXCLUDED_CATEGORIES = {"python-scripts-examples.html"}

LIST_LINK_RE = re.compile(
    r'<a\s+href=["\']https?://[^/"\']+/(?P<slug>[^/"\'?#]+\.html)["\']\s+class=["\']linkMare["\']\s*>(?P<title>.*?)</a>',
    re.IGNORECASE | re.DOTALL,
)
TITLE_RE = re.compile(
    r'<h1\b[^>]*class=["\'][^"\']*\bden_articol\b[^"\']*["\'][^>]*>(?P<title>.*?)</h1>',
    re.IGNORECASE | re.DOTALL,
)
METADATA_RE = re.compile(
    r'<td\s+class=["\']text_dreapta["\']>(?P<meta>.*?)</td>',
    re.IGNORECASE | re.DOTALL,
)
SUMMARY_RE = re.compile(
    r'<p\s+class=["\']text_obisnuit2["\']>\s*<em>(?P<summary>.*?)</em>\s*</p>',
    re.IGNORECASE | re.DOTALL,
)
CATEGORY_START = "<!-- ARTICOL CATEGORIE START -->"
CATEGORY_END = "<!-- ARTICOL CATEGORIE FINAL -->"


@dataclass(frozen=True)
class Article:
    path: Path
    categories: set[str]


@dataclass(frozen=True)
class PlannedAction:
    kind: str
    article: Path
    target_category: str
    source_categories: tuple[str, ...] = ()


def clean_text(fragment: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html.unescape(fragment))).strip()


def title_key(fragment: str) -> str:
    """Cheie tolerantă pentru aceeași denumire cu spații/entități HTML diferite."""
    return clean_text(fragment).casefold()


def source_articles(root: Path, category_slugs: set[str]) -> dict[str, set[Path]]:
    """Citește doar HTML-urile din directorul principal, nu Python Files."""
    result = {slug: set() for slug in category_slugs}
    for path in root.glob("*.html"):
        name = path.name.casefold()
        if name in category_slugs or name in EXCLUDED_ARTICLES:
            continue
        # Numele canonical indică articolul real; copia greșită nu trebuie
        # inclusă la completarea categoriilor.
        canonical = canonical_slug(path)
        if canonical and canonical != name and (root / canonical).is_file():
            continue
        text = read_html(path)
        for match in CATEGORY_LINK_RE.finditer(text):
            category = match.group("slug").casefold()
            if category in result:
                result[category].add(path)
    return result


def category_listing(page: str) -> tuple[set[str], set[str], list[str]]:
    entries = list(LIST_LINK_RE.finditer(page))
    slugs = {match.group("slug").casefold() for match in entries}
    titles = {title_key(match.group("title")) for match in entries}
    counts = Counter(match.group("slug").casefold() for match in entries)
    return slugs, titles, sorted(name for name, count in counts.items() if count > 1)


def article_title(path: Path) -> str:
    match = TITLE_RE.search(read_html(path))
    if not match:
        return ""
    return title_key(match.group("title"))


def planned_actions(root: Path) -> list[PlannedAction]:
    categories = [name for name in CATEGORY_FILES if name not in EXCLUDED_CATEGORIES]
    category_slugs = {name.casefold() for name in categories}
    sources = source_articles(root, category_slugs)
    listings: dict[str, tuple[set[str], set[str], list[str]]] = {}
    listed_anywhere: dict[str, set[str]] = {}
    titles_listed_anywhere: dict[str, set[str]] = {}
    for category in categories:
        category_path = root / category
        if not category_path.is_file():
            continue
        listed, titles, duplicates = category_listing(read_html(category_path))
        listings[category] = (listed, titles, duplicates)
        for slug in listed:
            listed_anywhere.setdefault(slug, set()).add(category)
        for title in titles:
            titles_listed_anywhere.setdefault(title, set()).add(category)

    actions: list[PlannedAction] = [
        PlannedAction("ȘTERGE FIȘIER", article, canonical)
        for article, canonical in invalid_filename_articles(root, category_slugs)
    ]
    for category in categories:
        category_path = root / category
        if not category_path.is_file():
            print(f"CATEGORIE INEXISTENTĂ: {category}")
            continue
        listed, listed_titles, duplicates = listings[category]
        if duplicates:
            print(f"DUBLATE în {category}: {', '.join(duplicates)}")
        for article in sorted(sources[category.casefold()], key=lambda item: item.name.casefold()):
            # Unele pagini vechi au titlul corect, dar URL-ul rămas dintr-un
            # articol anterior. În acel caz articolul este deja prezent vizual.
            slug = article.name.casefold()
            title = article_title(article)
            if slug in listed or title in listed_titles:
                continue
            # Articolul este deja în altă categorie: nu îl duplicăm automat.
            # Îl afișăm în consolă drept problemă de încadrare, nu drept lipsă.
            other_categories = (listed_anywhere.get(slug, set()) | titles_listed_anywhere.get(title, set())) - {category}
            if other_categories:
                actions.append(PlannedAction("MUTĂ", article, category, tuple(sorted(other_categories, key=str.casefold))))
                continue
            else:
                actions.append(PlannedAction("ADĂUGĂ", article, category))

    # Verificarea inversă: un articol poate fi deja corect în categoria
    # declarată, dar să fi rămas și într-o categorie veche/gresită.
    article_by_slug: dict[str, Path] = {}
    declared_categories: dict[str, set[str]] = {}
    for declared_category, articles in sources.items():
        for article in articles:
            slug = article.name.casefold()
            article_by_slug[slug] = article
            declared_categories.setdefault(slug, set()).add(declared_category)

    already_moving = {action.article.name.casefold() for action in actions if action.kind == "MUTĂ"}
    for listed_category, (listed_slugs, _listed_titles, _duplicates) in listings.items():
        for slug in listed_slugs:
            declared = declared_categories.get(slug, set())
            article = article_by_slug.get(slug)
            title = article_title(article) if article else ""
            # Ștergem numai o copie suplimentară: fișierul articol este
            # autoritatea, iar articolul trebuie să existe deja în categoria
            # declarată de el. Altfel cazul este tratat mai sus ca MUTĂ.
            already_correctly_listed = any(
                slug in listings[declared_category][0] or title in listings[declared_category][1]
                for declared_category in declared
                if declared_category in listings
            )
            if declared and listed_category not in declared and slug not in already_moving and already_correctly_listed:
                actions.append(
                    PlannedAction(
                        "ELIMINĂ", article, listed_category,
                        tuple(sorted(declared, key=str.casefold)),
                    )
                )
    return actions


def source_to_summary_block(article_path: Path, target_category: str) -> str:
    """Extrage titlul, metadatele și sumarul primului articol din fișierul sursă."""
    text = read_html(article_path)
    title = TITLE_RE.search(text)
    metadata = METADATA_RE.search(text)
    summary = SUMMARY_RE.search(text)
    absent = []
    if not title:
        absent.append("titlul h1.den_articol")
    if not metadata:
        absent.append("metadatele text_dreapta")
    if not summary:
        absent.append("sumarul p.text_obisnuit2 > em")
    if absent:
        raise ValueError(f"{article_path.name}: nu găsesc " + ", ".join(absent))

    title_html = title.group("title").strip()
    metadata_html = metadata.group("meta").strip()
    # Unele surse au href-ul categoriei corect, dar atributul title rămas de
    # la o categorie veche. Îl refacem din denumirea afișată a categoriei.
    category_url = re.escape(f"https://neculaifantanaru.com/{target_category}")
    category_anchor = re.search(
        rf'(<a\s+href=["\']{category_url}["\']\s+title=["\'])[^"\']*(["\'][^>]*>)(?P<label>.*?)</a>',
        metadata_html, re.IGNORECASE | re.DOTALL,
    )
    if category_anchor:
        label = clean_text(category_anchor.group("label"))
        replacement = (
            category_anchor.group(1)
            + f"Vezi toate articolele din {label}"
            + category_anchor.group(2)
            + category_anchor.group("label")
            + "</a>"
        )
        metadata_html = metadata_html[:category_anchor.start()] + replacement + metadata_html[category_anchor.end():]
    summary_html = summary.group("summary").strip()
    url = f"https://neculaifantanaru.com/{article_path.name}"
    return f'''    <table width="552" border="0">
          <tr>
            <td><span class="den_articol"><a href="{url}" class="linkMare">{title_html}</a></span></td>
          </tr>
          <tr>
            <td class="text_dreapta">{metadata_html}</td>
          </tr>
        </table>
        <p class="text_obisnuit2"><em>{summary_html}</em></p>
        <table width="552" border="0">
          <tr>
            <td width="552"><div align="right" id="external2"><a href="{url}">citește mai departe </a><a href="https://neculaifantanaru.com/" title=""><img src="Arrow3_black_5x7.gif" alt="" width="5" height="7" class="arrow" /></a></div></td>
          </tr>
        </table>
		<p class="text_obisnuit"></p>
'''


MONTHS = {
    "ianuarie": 1, "februarie": 2, "martie": 3, "aprilie": 4, "mai": 5, "iunie": 6,
    "iulie": 7, "august": 8, "septembrie": 9, "octombrie": 10, "noiembrie": 11, "decembrie": 12,
}
DATE_RE = re.compile(r"\bOn\s+(?P<month>[A-Za-zĂÂÎȘȚăâîșț]+)\s+(?P<day>\d{1,2}),\s+(?P<year>\d{4})", re.IGNORECASE)


def date_key(metadata: str) -> tuple[int, int, int]:
    match = DATE_RE.search(clean_text(metadata))
    if not match:
        return (0, 0, 0)
    return (int(match.group("year")), MONTHS.get(match.group("month").casefold(), 0), int(match.group("day")))


def insert_in_date_order(category_path: Path, article_path: Path) -> None:
    """Inserează un singur sumar înaintea primului articol mai vechi."""
    raw = category_path.read_bytes()
    # Păstrăm codarea și terminatoarele de linii ale paginii categoriei.
    encoding = "utf-8-sig" if raw.startswith(b"\xef\xbb\xbf") else "utf-8"
    try:
        page = raw.decode(encoding)
    except UnicodeDecodeError:
        encoding = "cp1252"
        page = raw.decode(encoding)
    block = source_to_summary_block(article_path, category_path.name)
    source_meta = METADATA_RE.search(read_html(article_path))
    new_date = date_key(source_meta.group("meta"))

    # Analizăm numai lista de articole a categoriei. Data fiecărui articol
    # este chiar textul din <td class="text_dreapta">On ...</td>.
    section_start = page.find(CATEGORY_START)
    if section_start < 0:
        raise ValueError(f"{category_path.name}: nu găsesc începutul listei de categorie")
    section_start += len(CATEGORY_START)
    section_end = page.find(CATEGORY_END, section_start)
    if section_end < 0:
        section_end = len(page)

    entries: list[tuple[int, int, int]] = []
    for metadata in METADATA_RE.finditer(page, section_start, section_end):
        if not clean_text(metadata.group("meta")).casefold().startswith("on "):
            continue
        table_start = page.rfind("<table", section_start, metadata.start())
        if table_start >= section_start:
            entries.append((table_start, metadata.end(), date_key(metadata.group("meta"))))

    insertion_at = next(
        (table_start for table_start, _meta_end, existing_date in entries if existing_date < new_date),
        -1,
    )
    if insertion_at < 0 and entries:
        # Cel mai vechi: după paragraful gol ce încheie ultimul bloc de articol.
        last_metadata_end = entries[-1][1]
        tail = re.search(
            r'<p\s+class=["\']text_obisnuit["\']>\s*</p>',
            page[last_metadata_end:section_end], re.IGNORECASE | re.DOTALL,
        )
        insertion_at = last_metadata_end + tail.end() if tail else last_metadata_end
    if insertion_at < 0:
        insertion_at = section_start

    newline = "\r\n" if "\r\n" in page else "\n"
    # Blocul se termină deja cu o singură linie nouă; următorul tabel începe
    # imediat pe rândul următor, fără rând gol intermediar.
    page = page[:insertion_at] + block.replace("\n", newline) + page[insertion_at:]
    category_path.write_text(page, encoding=encoding, newline="")


def remove_summary_from_category(category_path: Path, article_name: str) -> None:
    """Elimină blocul complet al articolului din categoria greșită."""
    raw = category_path.read_bytes()
    encoding = "utf-8-sig" if raw.startswith(b"\xef\xbb\xbf") else "utf-8"
    try:
        page = raw.decode(encoding)
    except UnicodeDecodeError:
        encoding = "cp1252"
        page = raw.decode(encoding)
    url = re.escape(f"https://neculaifantanaru.com/{article_name}")
    anchor = re.search(rf'<a\s+href=["\']{url}["\']\s+class=["\']linkMare["\']', page, re.IGNORECASE)
    if not anchor:
        raise ValueError(f"{article_name}: nu găsesc linkul în {category_path.name}")
    start = page.rfind("<table", 0, anchor.start())
    tail = re.search(r'<p\s+class=["\']text_obisnuit["\']>\s*</p>', page[anchor.end():], re.IGNORECASE | re.DOTALL)
    if start < 0 or not tail:
        raise ValueError(f"{article_name}: nu pot delimita blocul din {category_path.name}")
    end = anchor.end() + tail.end()
    category_path.write_text(page[:start] + page[end:], encoding=encoding, newline="")


def confirmation_window(actions: list[PlannedAction]) -> bool:
    """Afișează lista înainte de orice modificare și întoarce alegerea DA/NU."""
    root = tk.Tk()
    root.title("Verificare categorii — articole lipsă")
    root.geometry("820x560")
    root.minsize(620, 380)
    root.configure(padx=16, pady=14)
    root.grid_columnconfigure(0, weight=1)
    root.grid_rowconfigure(2, weight=1)
    decision = {"value": False}

    tk.Label(
        root,
        text=f"S-au găsit {len(actions)} acțiuni necesare pentru paginile categoriilor.",
        font=("Segoe UI", 12, "bold"), anchor="w",
    ).grid(row=0, column=0, sticky="ew")
    tk.Label(
        root,
        text="DA adaugă lipsurile și mută articolele aflate într-o categorie greșită, în ordinea datei.",
        font=("Segoe UI", 10), anchor="w", justify="left", wraplength=760,
    ).grid(row=1, column=0, sticky="ew", pady=(7, 10))

    listing = scrolledtext.ScrolledText(root, font=("Consolas", 11), wrap="word", padx=10, pady=9, height=16)
    listing.grid(row=2, column=0, sticky="nsew")
    listing.tag_configure("danger", foreground="#b00020", font=("Consolas", 11, "bold"))
    for action in actions:
        if action.kind == "ȘTERGE FIȘIER":
            listing.insert("end", f"ȘTERGE FIȘIER: {action.article.name}\n    URL canonical: {action.target_category}\n    motiv: numele diferă de canonical și nu este folosit în categorii/articole.\n\n", "danger")
        elif action.kind == "MUTĂ":
            listing.insert("end", f"MUTĂ: {action.article.name}\n    din: {', '.join(action.source_categories)}\n    în:  {action.target_category}\n\n")
        elif action.kind == "ELIMINĂ":
            listing.insert("end", f"ELIMINĂ DIN CATEGORIA GREȘITĂ: {action.article.name}\n    din: {action.target_category}\n    tag declarat în: {', '.join(action.source_categories)}\n\n")
        else:
            listing.insert("end", f"ADĂUGĂ: {action.article.name}\n    în:  {action.target_category}\n\n")
    listing.configure(state="disabled")

    buttons = tk.Frame(root)
    buttons.grid(row=3, column=0, pady=(12, 0))

    def yes() -> None:
        decision["value"] = True
        root.destroy()

    def no() -> None:
        root.destroy()

    tk.Button(
        buttons, text="DA — COMPLETEAZĂ TOATE", command=yes, bg="#8fcb7b",
        activebackground="#72b65e", font=("Segoe UI", 10, "bold"), padx=16, pady=7,
    ).pack(side="left", padx=6)
    tk.Button(
        buttons, text="NU — ANULEAZĂ", command=no, bg="#f0b5b5",
        activebackground="#df9292", font=("Segoe UI", 10, "bold"), padx=16, pady=7,
    ).pack(side="left", padx=6)
    root.protocol("WM_DELETE_WINDOW", no)
    root.mainloop()
    return decision["value"]


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT_DEFAULT)
    args = parser.parse_args()
    root = args.root.resolve()
    if not root.is_dir():
        print(f"Director inexistent: {root}", file=sys.stderr)
        return 2

    actions = planned_actions(root)
    if not actions:
        print("Nu există articole lipsă sau încadrate greșit în categoriile incluse.")
        return 0
    print("\nACȚIUNI NECESARE:")
    for action in actions:
        if action.kind == "ȘTERGE FIȘIER":
            print(f"ȘTERGE FIȘIER: {action.article.name} (canonical: {action.target_category})")
        elif action.kind == "MUTĂ":
            print(f"MUTĂ: {action.article.name} — {', '.join(action.source_categories)} -> {action.target_category}")
        elif action.kind == "ELIMINĂ":
            print(f"ELIMINĂ: {action.article.name} din {action.target_category} (tag: {', '.join(action.source_categories)})")
        else:
            print(f"ADĂUGĂ: {action.article.name} -> {action.target_category}")

    if not confirmation_window(actions):
        print("Nu am modificat niciun fișier.")
        return 0
    for action in actions:
        if action.kind == "ȘTERGE FIȘIER":
            action.article.unlink()
            print(f"ȘTERS: {action.article.name} (canonical: {action.target_category})")
        elif action.kind == "MUTĂ":
            for source_category in action.source_categories:
                remove_summary_from_category(root / source_category, action.article.name)
            insert_in_date_order(root / action.target_category, action.article)
            print(f"MUTAT: {action.article.name} -> {action.target_category}")
        elif action.kind == "ELIMINĂ":
            remove_summary_from_category(root / action.target_category, action.article.name)
            print(f"ELIMINAT: {action.article.name} din {action.target_category}")
        else:
            insert_in_date_order(root / action.target_category, action.article)
            print(f"ADĂUGAT: {action.article.name} -> {action.target_category}")
    print("Gata. Rulează din nou scriptul pentru verificare.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
