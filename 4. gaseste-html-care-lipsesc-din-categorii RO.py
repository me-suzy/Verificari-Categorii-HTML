# -*- coding: utf-8 -*-
r"""
Script care scaneaza folderul Principal\ro\ si subfolderele DESPRE, Python Files,
si gaseste fisierele HTML care NU sunt referite/linkate in niciun fisier de tip categorii.
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


def normalize_rel_path(path):
    """Normalizeaza o cale relativa pentru comparatii case-insensitive."""
    return path.replace("/", "\\").strip().lower()


SKIP_HTML_FILES = {
    normalize_rel_path(r"cum-arata-imagini-robineti-centrala-termica-ariston.html"): True,
    normalize_rel_path(r"dezabonare.html"): True,
    normalize_rel_path(r"feedback_thankyou.html"): True,
    normalize_rel_path(r"imagini-din-muzeul-mitropolitan-iasi.html"): True,
    normalize_rel_path(r"js-cookie-master\test\amd.html"): True,
    normalize_rel_path(r"js-cookie-master\test\encoding.html"): True,
    normalize_rel_path(r"js-cookie-master\test\malformed_cookie.html"): True,
    normalize_rel_path(r"js-cookie-master\test\missing_semicolon.html"): True,
    normalize_rel_path(r"newsletter_confirm.html"): True,
    normalize_rel_path(r"Python Files\python-how-to-mix-lines-or-how-to-shuffle-sentences-random.html"): True,
    normalize_rel_path(r"Python Files\python-PROBA-EXEMPLU.html"): True,
    normalize_rel_path(r"Python Files\webinar-avantul-spre-excelenta.html"): True,
    normalize_rel_path(r"Python Files\webinar-cercul-care-inchide-toate-sensurile.html"): True,
    normalize_rel_path(r"Python Files\webinar-constructia-subreda-a-leadershipului.html"): True,
    normalize_rel_path(r"Python Files\webinar-convinge-ma-ca-esti-in-viata.html"): True,
    normalize_rel_path(r"Python Files\webinar-culoarea-distincta-a-leadershipului.html"): True,
    normalize_rel_path(r"Python Files\webinar-culoarul-ingust-spre-culmile-desavarsirii.html"): True,
    normalize_rel_path(r"Python Files\webinar-drumul-adevarului.html"): True,
    normalize_rel_path(r"Python Files\webinar-dulcele-izvor-al-perfectiunii.html"): True,
    normalize_rel_path(r"Python Files\webinar-in-gol-se-ascunde-plinul.html"): True,
    normalize_rel_path(r"Python Files\webinar-omul-care-a-facut-26-iunie.html"): True,
    normalize_rel_path(r"Python Files\webinar-progresul-dirijabil-al-leadershipului.html"): True,
    normalize_rel_path(r"Python Files\webinar-scara-prea-ingusta-a-leadershipului.html"): True,
    normalize_rel_path(r"Python Files\webinar-taina-leadershipului.html"): True,
    normalize_rel_path(r"Python Files\webinar-totul-unitar-al-leadershipului.html"): True,
    normalize_rel_path(r"Python Files\webinar-un-patrat-negru-in-albul-orbitor.html"): True,
    normalize_rel_path(r"Python Files\webinar-un-rege-pentru-regatul-meu.html"): True,
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
    print("Gaseste fisiere HTML care NU sunt referite in niciun fisier categorii")
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
