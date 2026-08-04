#!/usr/bin/env python3
"""Find, add, move, and remove English category summaries after confirmation."""
from __future__ import annotations

import argparse
import re
import sys
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import scrolledtext

from verifica_categorii_en import (
    CATEGORY_LINK_RE, H1_RE, LIST_LINK_RE, ROOT_DEFAULT, article_title,
    category_listing, category_names, collect_sources, invalid_filename_articles, read_html,
)

METADATA_RE = re.compile(r'<td\s+class=["\']text_dreapta["\']>(?P<meta>.*?)</td>', re.I | re.S)
SUMMARY_RE = re.compile(r'<p\s+class=["\']text_obisnuit2["\']>\s*<em>(?P<summary>.*?)</em>\s*</p>', re.I | re.S)
CATEGORY_START = "<!-- ARTICOL CATEGORIE START -->"
CATEGORY_END = "<!-- ARTICOL CATEGORIE FINAL -->"
MONTHS = {name: number for number, name in enumerate(
    "january february march april may june july august september october november december".split(), 1)}
DATE_RE = re.compile(r"\bOn\s+(?P<month>[A-Za-z]+)\s+(?P<day>\d{1,2}),\s+(?P<year>\d{4})", re.I)
RO_FLAG_RE = re.compile(
    r'<a\s+href=["\']https?://[^"\']+/(?P<slug>[^/"\'?#]+\.html)["\'][^>]*>\s*'
    r'<img\b(?=[^>]*\btitle=["\']ro["\'])[^>]*>', re.I | re.S)


@dataclass(frozen=True)
class Action:
    kind: str  # ADD, MOVE, REMOVE, DELETE FILE
    article: Path
    category: str
    declared_categories: tuple[str, ...] = ()
    ro_category: str = ""
    ro_article: str = ""
    ro_verified: bool = False
    direct_link_wrong: bool = False
    wrong_category_count: int = 0


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", value)).strip()


def date_key(value: str) -> tuple[int, int, int]:
    match = DATE_RE.search(clean_text(value))
    if not match:
        return (0, 0, 0)
    return int(match.group("year")), MONTHS.get(match.group("month").casefold(), 0), int(match.group("day"))


def ro_verification(en_root: Path, article: Path, en_category: str) -> tuple[str, str, bool]:
    """Confirms the EN action against the corresponding Romanian category."""
    ro_root = en_root.parent / "ro"
    article_flag = RO_FLAG_RE.search(read_html(article))
    category_flag = RO_FLAG_RE.search(read_html(en_root / en_category)) if (en_root / en_category).is_file() else None
    if not article_flag or not category_flag:
        return "", "", False
    ro_article, ro_category = article_flag.group("slug"), category_flag.group("slug")
    ro_category_path = ro_root / ro_category
    if not ro_category_path.is_file() or not (ro_root / ro_article).is_file():
        return ro_category, ro_article, False
    listed, _titles, _duplicates = category_listing(read_html(ro_category_path))
    return ro_category, ro_article, ro_article.casefold() in listed


def action_with_ro_check(
    en_root: Path, kind: str, article: Path, category: str, declared: tuple[str, ...] = (),
    direct_link_wrong: bool = False, wrong_category_count: int = 0,
) -> Action:
    # REMOVE actions are verified against the correct (declared) category,
    # rather than against the category from which the duplicate is removed.
    verification_category = declared[0] if kind == "REMOVE" and declared else category
    ro_category, ro_article, verified = ro_verification(en_root, article, verification_category)
    return Action(kind, article, category, declared, ro_category, ro_article, verified, direct_link_wrong, wrong_category_count)


def ro_to_en_map(en_root: Path) -> dict[str, str]:
    """Maps each Romanian category slug to its English counterpart via FLAGS_1."""
    result: dict[str, str] = {}
    for category in category_names():
        path = en_root / category
        if path.is_file():
            flag = RO_FLAG_RE.search(read_html(path))
            if flag:
                result[flag.group("slug").casefold()] = category
    return result


def ro_canonical_en_category(en_root: Path, article: Path, mapping: dict[str, str]) -> str:
    """Uses the Romanian article tag plus its Romanian category listing as authority."""
    flag = RO_FLAG_RE.search(read_html(article))
    if not flag:
        return ""
    ro_article = flag.group("slug")
    ro_article_path = en_root.parent / "ro" / ro_article
    if not ro_article_path.is_file():
        return ""
    tag = CATEGORY_LINK_RE.search(read_html(ro_article_path))
    if not tag:
        return ""
    ro_category = tag.group("slug").casefold()
    ro_category_path = en_root.parent / "ro" / ro_category
    if not ro_category_path.is_file():
        return ""
    listed, _titles, _duplicates = category_listing(read_html(ro_category_path))
    if ro_article.casefold() not in listed:
        return ""
    return mapping.get(ro_category, "")


def plan(root: Path) -> list[Action]:
    categories = category_names()
    category_slugs = {name.casefold() for name in categories}
    sources = collect_sources(root, category_slugs)
    listings = {name: category_listing(read_html(root / name)) for name in categories if (root / name).is_file()}
    listed_anywhere: dict[str, set[str]] = {}
    article_by_slug: dict[str, Path] = {}
    declared: dict[str, set[str]] = {}
    for category, (slugs, _titles, _duplicates) in listings.items():
        for slug in slugs:
            listed_anywhere.setdefault(slug, set()).add(category)
    for category, articles in sources.items():
        for article in articles:
            slug = article.name.casefold()
            article_by_slug[slug] = article
            declared.setdefault(slug, set()).add(category)

    ro_mapping = ro_to_en_map(root)
    actions: list[Action] = []
    # A typo copy has a canonical URL for a different, existing file and is
    # neither a category entry nor linked by another article.  It is safe to
    # remove after the explicit YES confirmation.
    for article, canonical in invalid_filename_articles(root, category_slugs):
        actions.append(Action("DELETE FILE", article, canonical))
    for slug, article in article_by_slug.items():
        tags = declared[slug]
        listed = listed_anywhere.get(slug, set())
        # The Romanian source and Romanian category listing are the strongest
        # confirmation. If unavailable, fall back to the existing EN evidence.
        chosen = ro_canonical_en_category(root, article, ro_mapping)
        if not chosen:
            chosen = next(iter(tags)) if any(tag in listed for tag in tags) else (sorted(listed)[0] if listed else next(iter(tags)))

        if tags != {chosen}:
            actions.append(action_with_ro_check(
                root, "UPDATE TAG", article, chosen, tuple(sorted(tags)),
                direct_link_wrong=True, wrong_category_count=len(listed - {chosen}),
            ))
        if chosen not in listed:
            if listed:
                actions.append(action_with_ro_check(
                    root, "MOVE", article, chosen, tuple(sorted(listed)),
                    direct_link_wrong=tags != {chosen}, wrong_category_count=len(listed),
                ))
            else:
                actions.append(action_with_ro_check(root, "ADD", article, chosen, direct_link_wrong=tags != {chosen}))
        else:
            # Păstrăm categoria corectă și eliminăm numai copiile suplimentare.
            for wrong_category in sorted(listed - {chosen}):
                actions.append(action_with_ro_check(
                    root, "REMOVE", article, wrong_category, (chosen,),
                    direct_link_wrong=tags != {chosen}, wrong_category_count=len(listed - {chosen}),
                ))
    return sorted(set(actions), key=lambda item: (item.kind, item.category, item.article.name.casefold()))


def build_block(article: Path, category: str) -> tuple[str, tuple[int, int, int]]:
    text = read_html(article)
    title, metadata, summary = H1_RE.search(text), METADATA_RE.search(text), SUMMARY_RE.search(text)
    if not (title and metadata and summary):
        raise ValueError(f"Cannot extract title, metadata, or summary from {article.name}")
    url = f"https://neculaifantanaru.com/en/{article.name}"
    return f'''    <table width="552" border="0">
          <tr>
            <td><span class="den_articol"><a href="{url}" class="linkMare">{title.group('title').strip()}</a></span></td>
          </tr>
          <tr>
            <td class="text_dreapta">{metadata.group('meta').strip()}</td>
          </tr>
        </table>
        <p class="text_obisnuit2"><em>{summary.group('summary').strip()}</em></p>
        <table width="552" border="0">
          <tr>
            <td width="552"><div align="right" id="external2"><a href="{url}">read more </a><a href="https://neculaifantanaru.com/en/" title=""><img src="Arrow3_black_5x7.gif" alt="" width="5" height="7" class="arrow" /></a></div></td>
          </tr>
        </table>
		<p class="text_obisnuit"></p>
''', date_key(metadata.group("meta"))


def decode_page(path: Path) -> tuple[str, str]:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "cp1252"):
        try:
            return raw.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace"), "utf-8"


def insert_sorted(category_path: Path, article: Path) -> None:
    page, encoding = decode_page(category_path)
    block, new_date = build_block(article, category_path.name)
    begin = page.find(CATEGORY_START)
    if begin < 0:
        raise ValueError(f"Category start marker missing in {category_path.name}")
    begin += len(CATEGORY_START)
    finish = page.find(CATEGORY_END, begin)
    if finish < 0:
        finish = len(page)
    entries: list[tuple[int, int, tuple[int, int, int]]] = []
    for metadata in METADATA_RE.finditer(page, begin, finish):
        if not clean_text(metadata.group("meta")).casefold().startswith("on "):
            continue
        start = page.rfind("<table", begin, metadata.start())
        if start >= begin:
            entries.append((start, metadata.end(), date_key(metadata.group("meta"))))
    insertion = next((start for start, _end, value in entries if value < new_date), -1)
    if insertion < 0 and entries:
        tail = re.search(r'<p\s+class=["\']text_obisnuit["\']>\s*</p>', page[entries[-1][1]:finish], re.I | re.S)
        insertion = entries[-1][1] + tail.end() if tail else entries[-1][1]
    if insertion < 0:
        insertion = begin
    newline = "\r\n" if "\r\n" in page else "\n"
    category_path.write_text(page[:insertion] + block.replace("\n", newline) + page[insertion:], encoding=encoding, newline="")


def remove_block(category_path: Path, article: Path) -> bool:
    page, encoding = decode_page(category_path)
    url = re.escape(article.name)
    anchor = re.search(rf'<a\s+href=["\']https?://[^"\']*/{url}["\']\s+class=["\']linkMare["\']', page, re.I)
    if not anchor:
        # The item may already have been removed by an earlier interrupted run.
        return False
    start = page.rfind("<table", 0, anchor.start())
    # Most summaries finish with an empty ``text_obisnuit`` paragraph.  A few
    # legacy category pages are malformed at the last item: they contain the
    # opening paragraph tag but not its closing ``</p>`` before the enclosing
    # category ``</div>``.  In that case remove the opening tag as part of the
    # article, but leave the enclosing div untouched.
    tail = re.search(r'<p\s+class=["\']text_obisnuit["\'][^>]*>', page[anchor.end():], re.I | re.S)
    if start < 0 or not tail:
        raise ValueError(f"Article block cannot be delimited: {article.name} in {category_path.name}")
    tail_start = anchor.end() + tail.start()
    closing_p = re.search(r'</p\s*>', page[tail_start:], re.I)
    end = tail_start + closing_p.end() if closing_p else tail_start
    category_path.write_text(page[:start] + page[end:], encoding=encoding, newline="")
    return True


def update_article_tag(root: Path, article: Path, target_category: str) -> None:
    """Copies the canonical category anchor from its category page into the article."""
    category_page = read_html(root / target_category)
    target_url = re.escape(f"https://neculaifantanaru.com/en/{target_category}")
    anchor_re = re.compile(
        rf'<a\b(?=[^>]*\bhref\s*=\s*["\']{target_url}["\'])'
        r'(?=[^>]*\brel\s*=\s*["\']category\s+tag["\'])[^>]*>.*?</a>', re.I | re.S)
    canonical = anchor_re.search(category_page)
    if not canonical:
        raise ValueError(f"Canonical category tag not found in {target_category}")
    page, encoding = decode_page(article)
    source_anchor = re.compile(
        r'<a\b(?=[^>]*\brel\s*=\s*["\']category\s+tag["\'])[^>]*>.*?</a>', re.I | re.S).search(page)
    if not source_anchor:
        raise ValueError(f"Category tag not found in {article.name}")
    article.write_text(page[:source_anchor.start()] + canonical.group(0) + page[source_anchor.end():], encoding=encoding, newline="")


def confirm(actions: list[Action]) -> bool:
    root = tk.Tk(); root.title("English categories — required changes")
    root.geometry("850x560"); root.minsize(620, 380); root.configure(padx=16, pady=14)
    root.grid_columnconfigure(0, weight=1); root.grid_rowconfigure(1, weight=1)
    tk.Label(root, text=f"{len(actions)} change(s) found.", font=("Segoe UI", 12, "bold"), anchor="w").grid(row=0, column=0, sticky="ew", pady=(0, 8))
    box = scrolledtext.ScrolledText(root, font=("Consolas", 11), wrap="word", padx=10, pady=9)
    box.grid(row=1, column=0, sticky="nsew")
    box.tag_configure("danger", foreground="#b00020", font=("Consolas", 11, "bold"))
    for action in actions:
        if action.kind == "DELETE FILE":
            box.insert("end", f"DELETE FILE: {action.article.name}\n    canonical URL: {action.category}\n    motiv: numele fișierului nu coincide cu canonical și nu este folosit în categorii/articole.\n\n", "danger")
            continue
        extra = f"\n    current tag: {', '.join(action.declared_categories)}" if action.declared_categories else ""
        if action.ro_category:
            ro_status = "CONFIRMED" if action.ro_verified else "NOT CONFIRMED — WILL NOT APPLY"
            extra += f"\n    RO category: {action.ro_category}\n    RO article: {action.ro_article}\n    RO verification: {ro_status}"
        else:
            extra += "\n    RO verification: NO RO COUNTERPART FOUND — WILL NOT APPLY"
        if action.direct_link_wrong:
            extra += "\n    ATENȚIE: link-ul din articol indică altă categorie"
        if action.wrong_category_count:
            extra += f"\n    ATENȚIE: link-ul se află în {action.wrong_category_count} HTML categorii greșite"
        box.insert("end", f"{action.kind}: {action.article.name}\n    category: {action.category}{extra}\n\n")
    box.configure(state="disabled")
    decision = {"yes": False}
    controls = tk.Frame(root); controls.grid(row=2, column=0, pady=(12, 0))
    def yes(): decision["yes"] = True; root.destroy()
    def no(): root.destroy()
    tk.Button(controls, text="YES — APPLY ALL", command=yes, bg="#8fcb7b", font=("Segoe UI", 10, "bold"), padx=18, pady=7).pack(side="left", padx=6)
    tk.Button(controls, text="NO — CANCEL", command=no, bg="#f0b5b5", font=("Segoe UI", 10, "bold"), padx=18, pady=7).pack(side="left", padx=6)
    root.protocol("WM_DELETE_WINDOW", no); root.mainloop(); return decision["yes"]


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(); parser.add_argument("--root", type=Path, default=ROOT_DEFAULT)
    root = parser.parse_args().root.resolve(); actions = plan(root)
    if not actions: print("No changes needed."); return 0
    if not confirm(actions): print("No files changed."); return 0
    safe_actions = [action for action in actions if action.ro_verified or action.kind == "DELETE FILE"]
    skipped_actions = [action for action in actions if not action.ro_verified and action.kind != "DELETE FILE"]
    for action in skipped_actions:
        print(f"SKIPPED (RO verification missing): {action.kind} {action.article.name}")
    # Update source tags first, so a subsequently added/moved summary copies
    # the corrected canonical metadata.
    for action in safe_actions:
        if action.kind == "DELETE FILE":
            action.article.unlink()
            print(f"{action.kind}: {action.article.name} (canonical: {action.category})")
        elif action.kind == "UPDATE TAG":
            try:
                update_article_tag(root, action.article, action.category)
                print(f"{action.kind}: {action.article.name} -> {action.category}")
            except ValueError as error:
                print(f"SKIPPED: {action.kind} {action.article.name} — {error}")
    for action in safe_actions:
        if action.kind in {"UPDATE TAG", "DELETE FILE"}:
            continue
        try:
            if action.kind == "ADD":
                insert_sorted(root / action.category, action.article)
            elif action.kind == "MOVE":
                for old_category in action.declared_categories:
                    remove_block(root / old_category, action.article)
                insert_sorted(root / action.category, action.article)
            else:
                removed = remove_block(root / action.category, action.article)
                if not removed:
                    print(f"ALREADY REMOVED: {action.article.name} -> {action.category}")
                    continue
            print(f"{action.kind}: {action.article.name} -> {action.category}")
        except ValueError as error:
            print(f"SKIPPED: {action.kind} {action.article.name} — {error}")
    return 0


if __name__ == "__main__": raise SystemExit(main())
