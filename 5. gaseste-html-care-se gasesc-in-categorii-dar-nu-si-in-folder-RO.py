# -*- coding: utf-8 -*-
r"""
Script INVERS: gaseste link-urile .html care sunt referite in fisierele de tip categorii,
dar NU exista ca fisiere in folderul Principal\ro\ (si subfolderele DESPRE, Python Files).
"""

import os
import re

# Foldere de scanat
ROOT_FOLDER = r"e:\Carte\BB\17 - Site Leadership\Principal\ro"
SCAN_FOLDERS = [
    ROOT_FOLDER,
    os.path.join(ROOT_FOLDER, "DESPRE"),
    os.path.join(ROOT_FOLDER, "Python Files"),
]

# Lista fisierelor de tip categorii (din folderul ro)
CATEGORY_FILES = [
    "index.html",
    "lideri-si-atitudine.html",
    "leadership-magic.html",
    "leadership-de-succes.html",
    "hr-resurse-umane.html",
    "legile-conducerii.html",
    "leadership-total.html",
    "leadership-de-durata.html",
    "principiile-conducerii.html",
    "leadership-plus.html",
    "calitatile-unui-lider.html",
    "leadership-de-varf.html",
    "leadership-impact.html",
    "dezvoltare-personala.html",
    "aptitudini-si-abilitati-de-leadership.html",
    "leadership-real.html",
    "leadership-de-baza.html",
    "leadership-360.html",
    "leadership-pro.html",
    "leadership-expert.html",
    "leadership-know-how.html",
    "jurnal-de-leadership.html",
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

# Regex pentru href cu .html (local sau URL)
HREF_HTML_PATTERN = re.compile(r'href\s*=\s*["\']([^"\']*\.html[^"\']*)["\']', re.IGNORECASE)


# Prefixe URL pentru alte limbi (le excludem din cautare)
OTHER_LANG_PATHS = ["/fr/", "/en/", "/es/", "/pt/", "/ar/", "/zh/", "/hi/", "/de/", "/ru/"]


def extract_html_refs_from_content(content, source_file=""):
    """Extrage referintele .html din continut (href), IGNORAND link-urile catre alte limbi."""
    refs = {}
    for match in HREF_HTML_PATTERN.finditer(content):
        url = match.group(1).strip()

        # Ignora link-urile catre alte limbi (ex: /fr/, /en/, /es/ etc.)
        if any(lang in url for lang in OTHER_LANG_PATHS):
            continue

        # Extrage doar numele fisierului (partea din dreapta dupa /)
        if "/" in url:
            filename = url.split("/")[-1]
        else:
            filename = url
        # Elimina #anchor
        if "#" in filename:
            filename = filename.split("#")[0]
        if filename.lower().endswith(".html"):
            fn_lower = filename.lower()
            if fn_lower not in refs:
                refs[fn_lower] = []
            if source_file and source_file not in refs[fn_lower]:
                refs[fn_lower].append(source_file)
    return refs


def get_all_html_refs_from_category_files():
    """Citeste toate fisierele categorii si colecteaza toate referintele .html cu sursa."""
    all_refs = {}  # {filename: [lista de fisiere categorii care il refera]}
    category_paths = [os.path.join(ROOT_FOLDER, f) for f in CATEGORY_FILES]

    for cat_file, path in zip(CATEGORY_FILES, category_paths):
        if not os.path.exists(path):
            continue
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            refs = extract_html_refs_from_content(content, cat_file)
            for fn, sources in refs.items():
                if fn not in all_refs:
                    all_refs[fn] = []
                all_refs[fn].extend(sources)
        except Exception as e:
            print(f"  EROARE citire {path}: {e}")

    return all_refs


def get_all_html_filenames_in_scan_folders():
    """Returneaza un set cu toate numelor de fisiere .html (lowercase) din folderele scanate."""
    seen_paths = set()
    filenames = set()
    for folder in SCAN_FOLDERS:
        if not os.path.exists(folder):
            continue
        for root, dirs, files in os.walk(folder):
            for f in files:
                if f.lower().endswith(".html"):
                    full_path = os.path.join(root, f)
                    if full_path in seen_paths:
                        continue
                    seen_paths.add(full_path)
                    filenames.add(f.lower())
    return filenames


def main():
    print("=" * 70)
    print("Gaseste link-uri din categorii care NU exista ca fisiere in folder (RO)")
    print("=" * 70)

    print("\n1. Colectare referinte din fisierele categorii...")
    refs_in_categories = get_all_html_refs_from_category_files()
    print(f"   Total link-uri .html unice gasite in categorii: {len(refs_in_categories)}")

    print("\n2. Scanare fisiere HTML din foldere...")
    existing_files = get_all_html_filenames_in_scan_folders()
    print(f"   Total fisiere .html existente: {len(existing_files)}")

    print("\n3. Identificare link-uri care NU au fisier corespondent...")
    missing = []
    for ref_filename, sources in refs_in_categories.items():
        if ref_filename not in existing_files:
            missing.append((ref_filename, sources))

    # Sortare alfabetica
    missing.sort(key=lambda x: x[0])

    print(f"\n   Rezultat: {len(missing)} link-uri din categorii nu au fisier in folder.")
    print("\n" + "-" * 70)
    if missing:
        for filename, sources in missing:
            # Afiseaza max 3 surse
            src_display = ", ".join(sources[:3])
            if len(sources) > 3:
                src_display += f" ... (+{len(sources) - 3} altele)"
            print(f"  {filename}")
            print(f"      referit in: {src_display}")
    else:
        print("  (niciunul - toate link-urile au fisiere corespunzatoare)")

    print("\n" + "=" * 70)
    print("Gata.")
    print("=" * 70)


if __name__ == "__main__":
    main()
