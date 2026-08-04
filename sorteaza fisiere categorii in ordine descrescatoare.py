#!/usr/bin/env python3
"""Sortează descrescător, după dată, blocurile de articole din categorii.

Sunt procesate toate fișierele ``.html`` din INPUT_FOLDER care conțin
delimitatorii ``<!-- ARTICOL START -->`` și ``<!-- ARTICOL FINAL -->``.
Prin urmare este inclus și ``index.html`` dacă are aceeași structură.
"""
from __future__ import annotations

import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path


# Schimbă ulterior numai această linie cu folderul principal dorit.
INPUT_FOLDER = Path(r"D:\3\Input")

# Nu se creează copii .bak; scriptul modifică direct fișierele din INPUT_FOLDER.
CREATE_BACKUPS = False

START_MARKER = "<!-- ARTICOL START -->"
END_MARKER = "<!-- ARTICOL FINAL -->"
ARTICLE_RE = re.compile(r"<article\b[^>]*>.*?</article>", re.IGNORECASE | re.DOTALL)
TIME_RE = re.compile(
    r"<time\b(?P<attrs>[^>]*)>(?P<text>.*?)</time>", re.IGNORECASE | re.DOTALL
)
DATETIME_RE = re.compile(r"\bdatetime\s*=\s*['\"](?P<value>[^'\"]+)['\"]", re.IGNORECASE)
DATE_RE = re.compile(
    r"(?:on\s+)?(?P<month>[a-zăâîșşţț]+)\s+(?P<day>\d{1,2}),\s*(?P<year>\d{4})",
    re.IGNORECASE,
)
MONTHS = {
    "ianuarie": 1, "ianuarue": 1, "februarie": 2, "martie": 3, "aprilie": 4, "mai": 5,
    "iunie": 6, "iulie": 7, "august": 8, "septembrie": 9, "octombrie": 10,
    "noiembrie": 11, "decembrie": 12,
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5,
    "june": 6, "july": 7, "august": 8, "september": 9, "october": 10,
    "november": 11, "december": 12,
}


@dataclass(frozen=True)
class ArticleBlock:
    html: str
    date: tuple[int, int, int]


def read_html(path: Path) -> tuple[str, str]:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "cp1250", "cp1252", "latin-1"):
        try:
            return raw.decode(encoding), encoding
        except UnicodeDecodeError:
            pass
    return raw.decode("utf-8", errors="replace"), "utf-8"


def normalize(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value)
    value = unicodedata.normalize("NFD", value.casefold())
    return "".join(char for char in value if unicodedata.category(char) != "Mn")


def date_from_block(block: str) -> tuple[int, int, int]:
    """Extrage data afișată în articol; ea este autoritatea pentru sortare."""
    for time_tag in TIME_RE.finditer(block):
        visible = normalize(time_tag.group("text"))
        text_date = DATE_RE.search(visible)
        # Data vizibilă este cea pe care o vede cititorul. Unele fișiere au
        # atributul datetime rămas greșit după copiere, deci nu îl lăsăm să
        # schimbe ordinea când contrazice textul afișat.
        if text_date:
            return (
                int(text_date.group("year")),
                MONTHS.get(text_date.group("month"), 0),
                int(text_date.group("day")),
            )
        datetime_value = DATETIME_RE.search(time_tag.group("attrs"))
        if datetime_value:
            value = datetime_value.group("value")
            iso = re.match(r"(?P<year>\d{4})(?:-(?P<month>\d{1,2})(?:-(?P<day>\d{1,2}))?)?", value)
            if iso:
                year = int(iso.group("year"))
                return year, int(iso.group("month") or 0), int(iso.group("day") or 0)
    return (0, 0, 0)  # Bloc fără dată: rămâne ultimul, în ordinea originală.


def sort_section(section: str) -> tuple[str, int, int]:
    matches = list(ARTICLE_RE.finditer(section))
    if len(matches) < 2:
        return section, len(matches), 0
    original = [ArticleBlock(match.group(0), date_from_block(match.group(0))) for match in matches]
    ordered = sorted(original, key=lambda item: item.date, reverse=True)
    if original == ordered:
        return section, len(matches), 0

    # Înlocuim doar conținutul fiecărui <article>; spațiile, comentariile și
    # restul structurii dintre blocuri rămân exact cum erau în fișier.
    pieces: list[str] = []
    cursor = 0
    for match, article in zip(matches, ordered):
        pieces.append(section[cursor:match.start()])
        pieces.append(article.html)
        cursor = match.end()
    pieces.append(section[cursor:])
    return "".join(pieces), len(matches), 1


def sort_file(path: Path) -> tuple[bool, int, str]:
    page, encoding = read_html(path)
    start = page.find(START_MARKER)
    end = page.find(END_MARKER, start + len(START_MARKER)) if start >= 0 else -1
    if start < 0 or end < 0:
        return False, 0, "fără delimitatori de articole"
    section_start = start + len(START_MARKER)
    sorted_section, count, changed = sort_section(page[section_start:end])
    if not changed:
        return False, count, "deja în ordine"
    if CREATE_BACKUPS:
        backup = path.with_suffix(path.suffix + ".bak")
        if not backup.exists():
            backup.write_bytes(path.read_bytes())
    path.write_bytes((page[:section_start] + sorted_section + page[end:]).encode(encoding))
    return True, count, "sortat descrescător"


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if not INPUT_FOLDER.is_dir():
        print(f"Folder inexistent: {INPUT_FOLDER}")
        return 2
    total = changed = 0
    for path in sorted(INPUT_FOLDER.glob("*.html"), key=lambda item: item.name.casefold()):
        did_change, count, status = sort_file(path)
        if count:
            total += 1
            changed += int(did_change)
            print(f"{path.name}: {status} ({count} blocuri)")
    print(f"\nPagini de categorie/index găsite: {total}. Modificate: {changed}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
