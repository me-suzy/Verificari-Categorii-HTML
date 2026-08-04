# -*- coding: utf-8 -*-
r"""
Compara fisierele HTML din Principal\ro\ cu Principal 2022\ro\
si afiseaza cele care se gasesc intr-un folder dar nu si in celalalt.
"""

import os

FOLDER_A = r"e:\Carte\BB\17 - Site Leadership\Principal\ro"
FOLDER_B = r"e:\Carte\BB\17 - Site Leadership\Principal 2022\ro"

LABEL_A = r"Principal\ro"
LABEL_B = r"Principal 2022\ro"


def get_html_filenames(folder):
    """Returneaza un set cu toate numele de fisiere .html din folder (doar radacina, fara subfoldere)."""
    filenames = set()
    if not os.path.exists(folder):
        print(f"  ATENTIE: Folderul nu exista: {folder}")
        return filenames
    for f in os.listdir(folder):
        if f.lower().endswith(".html"):
            filenames.add(f.lower())
    return filenames


def main():
    print("=" * 70)
    print("Comparare fisiere HTML intre doua foldere")
    print("=" * 70)
    print(f"  Folder A: {FOLDER_A}")
    print(f"  Folder B: {FOLDER_B}")

    print("\n1. Scanare fisiere HTML...")
    files_a = get_html_filenames(FOLDER_A)
    files_b = get_html_filenames(FOLDER_B)
    print(f"   {LABEL_A}: {len(files_a)} fisiere .html")
    print(f"   {LABEL_B}: {len(files_b)} fisiere .html")

    only_in_a = sorted(files_a - files_b)
    only_in_b = sorted(files_b - files_a)
    common = files_a & files_b

    print(f"\n   Comune in ambele: {len(common)}")
    print(f"   Doar in {LABEL_A}: {len(only_in_a)}")
    print(f"   Doar in {LABEL_B}: {len(only_in_b)}")

    print(f"\n{'=' * 70}")
    print(f"  Fisiere DOAR in {LABEL_A} ({len(only_in_a)}):")
    print(f"{'=' * 70}")
    if only_in_a:
        for f in only_in_a:
            print(f"  {f}")
    else:
        print("  (niciunul)")

    print(f"\n{'=' * 70}")
    print(f"  Fisiere DOAR in {LABEL_B} ({len(only_in_b)}):")
    print(f"{'=' * 70}")
    if only_in_b:
        for f in only_in_b:
            print(f"  {f}")
    else:
        print("  (niciunul)")

    print(f"\n{'=' * 70}")
    print("Gata.")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
