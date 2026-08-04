# -*- coding: utf-8 -*-
r"""
Script care scaneaza folderul Principal\en\ si subfolderele ABOUT, FISIERE PYTHON HTML,
si gaseste fisierele HTML care NU sunt referite/linkate in niciun fisier de tip categorii.
"""

import os
import re

# Foldere de scanat - versiunea EN
ROOT_FOLDER = r"e:\Carte\BB\17 - Site Leadership\Principal\en"
SCAN_FOLDERS = [
    ROOT_FOLDER,
    os.path.join(ROOT_FOLDER, "ABOUT"),
    os.path.join(ROOT_FOLDER, "FISIERE PYTHON HTML"),
]

# Lista fisierelor de tip categorii (din folderul en)
CATEGORY_FILES = [
    "index.html",
    "leadership-and-attitude.html",
    "leadership-magic.html",
    "successful-leadership.html",
    "hr-human-resources.html",
    "leadership-laws.html",
    "total-leadership.html",
    "leadership-that-lasts.html",
    "leadership-principles.html",
    "leadership-plus.html",
    "qualities-of-a-leader.html",
    "top-leadership.html",
    "leadership-impact.html",
    "personal-development.html",
    "leadership-skills-and-abilities.html",
    "real-leadership.html",
    "basic-leadership.html",
    "leadership-360.html",
    "leadership-pro.html",
    "leadership-expert.html",
    "leadership-know-how.html",
    "leadership-journal.html",
    "alpha-leadership.html",
    "leadership-on-off.html",
    "leadership-deluxe.html",
    "leadership-xxl.html",
    "leadership-50-extra.html",
    "leadership-fusion.html",
    "leadership-v8.html",
    "leadership-x3-silver.html",
    "leadership-q2-sensitive.html",
    "leadership-t7-hybrid.html",
    "leadership-n6-celsius.html",
    "leadership-s4-quartz.html",
    "leadership-gt-accent.html",
    "leadership-fx-intensive.html",
    "leadership-iq-light.html",
    "leadership-7th-edition.html",
    "leadership-xs-analytics.html",
    "leadership-z3-extended.html",
    "leadership-ex-elite.html",
    "leadership-w3-integra.html",
    "leadership-sx-experience.html",
    "leadership-y5-superzoom.html",
    "performance-ex-flash.html",
    "leadership-mindware.html",
    "leadership-r2-premiere.html",
    "leadership-y4-titanium.html",
    "leadership-quantum-xx.html",
    "python-scripts-examples.html",
]


def normalize_rel_path(path):
    """Normalizeaza o cale relativa pentru comparatii case-insensitive."""
    return path.replace("/", "\\").strip().lower()


SKIP_HTML_FILES = {
    normalize_rel_path(r"feedback_thankyou.html"): True,
    normalize_rel_path(r"FISIERE PYTHON HTML\Python - EXEMPLU EXAMPLE.html"): True,
    normalize_rel_path(r"FISIERE PYTHON HTML\python-how-to-mix-lines-or-how-to-shuffle-sentences-random.html"): True,
    normalize_rel_path(r"FISIERE PYTHON HTML\updates.html"): True,
    normalize_rel_path(r"FISIERE PYTHON HTML\webinar-a-black-square-into-the-dazzling-white.html"): True,
    normalize_rel_path(r"FISIERE PYTHON HTML\webinar-a-king-for-my-kingdom.html"): True,
    normalize_rel_path(r"FISIERE PYTHON HTML\webinar-convince-me-that-you-are-alive.html"): True,
    normalize_rel_path(r"FISIERE PYTHON HTML\webinar-in-emptiness-is-hidden-the-fullness.html"): True,
    normalize_rel_path(r"FISIERE PYTHON HTML\webinar-the-circle-that-closes-all-senses.html"): True,
    normalize_rel_path(r"FISIERE PYTHON HTML\webinar-the-dirigible-progress-of-leadership.html"): True,
    normalize_rel_path(r"FISIERE PYTHON HTML\webinar-the-distinctive-color-of-leadership.html"): True,
    normalize_rel_path(r"FISIERE PYTHON HTML\webinar-the-impetus-towards-excellence.html"): True,
    normalize_rel_path(r"FISIERE PYTHON HTML\webinar-the-man-who-made-the-june-26.html"): True,
    normalize_rel_path(r"FISIERE PYTHON HTML\webinar-the-mystery-of-leadership.html"): True,
    normalize_rel_path(r"FISIERE PYTHON HTML\webinar-the-narrow-corridor-towards-the-heights-of-perfection.html"): True,
    normalize_rel_path(r"FISIERE PYTHON HTML\webinar-the-road-of-truth.html"): True,
    normalize_rel_path(r"FISIERE PYTHON HTML\webinar-the-sweet-source-of-perfection.html"): True,
    normalize_rel_path(r"FISIERE PYTHON HTML\webinar-the-too-narrow-ladder-of-leadership.html"): True,
    normalize_rel_path(r"FISIERE PYTHON HTML\webinar-the-unitary-whole-of-leadership.html"): True,
    normalize_rel_path(r"FISIERE PYTHON HTML\webinar-the-weak-construction-of-leadership.html"): True,
    normalize_rel_path(r"newsletter_confirm.html"): True,
    normalize_rel_path(r"romania-images-from-the-metropolitan-museum-iasi-underground-galleries.html"): True,
    normalize_rel_path(r"search.html"): True,
    normalize_rel_path(r"unsubscribe.html"): True,
    normalize_rel_path(r"y_key_e479323ce281e459.html"): True,
}

# Regex pentru href cu .html (local sau URL)
HREF_HTML_PATTERN = re.compile(r'href\s*=\s*["\']([^"\']*\.html[^"\']*)["\']', re.IGNORECASE)


def extract_html_refs_from_content(content):
    """Extrage toate referintele .html din continut (href)."""
    refs = set()
    for match in HREF_HTML_PATTERN.finditer(content):
        url = match.group(1).strip()
        # Extrage doar numele fisierului (partea din dreapta dupa /)
        if "/" in url:
            filename = url.split("/")[-1]
        else:
            filename = url
        # Elimina #anchor
        if "#" in filename:
            filename = filename.split("#")[0]
        if filename.lower().endswith(".html"):
            refs.add(filename.lower())
    return refs


def get_all_html_refs_from_category_files():
    """Citeste toate fisierele categorii si colecteaza toate referintele .html."""
    all_refs = set()
    category_paths = [os.path.join(ROOT_FOLDER, f) for f in CATEGORY_FILES]

    for path in category_paths:
        if not os.path.exists(path):
            continue
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            refs = extract_html_refs_from_content(content)
            all_refs.update(refs)
        except Exception as e:
            print(f"  EROARE citire {path}: {e}")

    return all_refs


def get_all_html_files_in_scan_folders():
    """Returneaza lista tuturor fisierelor .html din folderele scanate."""
    seen = set()
    html_files = []
    for folder in SCAN_FOLDERS:
        if not os.path.exists(folder):
            continue
        for root, dirs, files in os.walk(folder):
            for f in files:
                if f.lower().endswith(".html"):
                    full_path = os.path.join(root, f)
                    if full_path in seen:
                        continue
                    seen.add(full_path)
                    rel_path = os.path.relpath(full_path, ROOT_FOLDER)
                    html_files.append((full_path, rel_path, f))
    return html_files


def main():
    print("=" * 70)
    print("Gaseste fisiere HTML care NU sunt referite in niciun fisier categorii (EN)")
    print("=" * 70)

    print("\n1. Colectare referinte din fisierele categorii...")
    refs_in_categories = get_all_html_refs_from_category_files()
    print(f"   Total referinte .html gasite in categorii: {len(refs_in_categories)}")

    print("\n2. Scanare fisiere HTML din foldere...")
    html_files = get_all_html_files_in_scan_folders()
    print(f"   Total fisiere .html gasite: {len(html_files)}")

    print("\n3. Identificare fisiere NEREFERITE in categorii...")
    not_referenced = []
    skipped = []
    for full_path, rel_path, filename in html_files:
        if normalize_rel_path(rel_path) in SKIP_HTML_FILES:
            skipped.append((full_path, rel_path, filename))
            continue
        if filename.lower() not in refs_in_categories:
            not_referenced.append((full_path, rel_path, filename))

    # Sortare dupa cale relativa
    not_referenced.sort(key=lambda x: x[1].lower())

    print(f"   Fisiere HTML ignorate prin SKIP_HTML_FILES: {len(skipped)}")
    print(f"\n   Rezultat: {len(not_referenced)} fisiere HTML nu sunt referite in niciun fisier categorii.")
    print("\n" + "-" * 70)
    if not_referenced:
        for full_path, rel_path, filename in not_referenced:
            print(f"  {rel_path}")
    else:
        print("  (niciunul)")

    print("\n" + "=" * 70)
    print("Gata.")
    print("=" * 70)


if __name__ == "__main__":
    main()
