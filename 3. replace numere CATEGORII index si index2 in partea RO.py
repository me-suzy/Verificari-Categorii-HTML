# -*- coding: utf-8 -*-
"""
Script care inlocuieste sectiunea Categories din index.html si index2.html (Sedinta 18)
cu sectiunea corespunzatoare din Principal 2022/ro/index.html

Partea dintre: <!-- Categories --> si <!-- BOOKS START -->
"""

import os
import sys

# Fix encoding pentru console Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Căi absolute
SOURCE_FILE = r"e:\Carte\BB\17 - Site Leadership\Principal 2022\ro\index.html"
TARGET_FILES = [
    r"e:\Carte\BB\17 - Site Leadership\alte\Ionel Balauta\Aryeht\Task 1 - Traduce tot site-ul\Doar Google Web\Andreea\Meditatii\Sedinta 18\index.html",
    r"e:\Carte\BB\17 - Site Leadership\alte\Ionel Balauta\Aryeht\Task 1 - Traduce tot site-ul\Doar Google Web\Andreea\Meditatii\Sedinta 18\index2.html",
]

CATEGORIES_MARKER = "<!-- Categories -->"
BOOKS_START_MARKER = "<!-- BOOKS START -->"


def extract_section(content, start_marker, end_marker):
    """Extrage conținutul dintre start_marker (inclusiv) și end_marker (exclusiv)."""
    start_idx = content.find(start_marker)
    if start_idx == -1:
        raise ValueError(f"Marcatorul '{start_marker}' nu a fost gasit.")
    
    end_idx = content.find(end_marker, start_idx)
    if end_idx == -1:
        raise ValueError(f"Marcatorul '{end_marker}' nu a fost gasit dupa '{start_marker}'.")
    
    return content[start_idx:end_idx].rstrip()


def replace_section(content, new_section, start_marker, end_marker):
    """Înlocuiește secțiunea dintre marcatori cu noul conținut."""
    start_idx = content.find(start_marker)
    if start_idx == -1:
        raise ValueError(f"Marcatorul '{start_marker}' nu a fost gasit.")
    
    end_idx = content.find(end_marker, start_idx)
    if end_idx == -1:
        raise ValueError(f"Marcatorul '{end_marker}' nu a fost gasit dupa '{start_marker}'.")
    
    return content[:start_idx] + new_section + "\n\n                    " + content[end_idx:]


def main():
    print("=" * 60)
    print("Replace Categories sectiune din Principal 2022 in Sedinta 18")
    print("=" * 60)
    
    # Verifică dacă fișierul sursă există
    if not os.path.exists(SOURCE_FILE):
        print(f"EROARE: Fisierul sursa nu exista: {SOURCE_FILE}")
        return
    
    # Citește și extrage secțiunea din Principal 2022
    print(f"\nCitire fisier sursa: {SOURCE_FILE}")
    with open(SOURCE_FILE, "r", encoding="utf-8") as f:
        source_content = f.read()
    
    try:
        new_section = extract_section(source_content, CATEGORIES_MARKER, BOOKS_START_MARKER)
        print(f"Sectiunea extrasa: {len(new_section)} caractere")
    except ValueError as e:
        print(f"EROARE la extragere: {e}")
        return
    
    # Procesează fiecare fișier țintă
    for target_path in TARGET_FILES:
        print(f"\nProcesare: {os.path.basename(target_path)}")
        
        if not os.path.exists(target_path):
            print(f"  ATENTIE: Fisierul nu exista, sarit.")
            continue
        
        with open(target_path, "r", encoding="utf-8") as f:
            target_content = f.read()
        
        try:
            new_content = replace_section(target_content, new_section, CATEGORIES_MARKER, BOOKS_START_MARKER)
            
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            
            print(f"  OK: Sectiunea Categories a fost inlocuita cu succes.")
        except ValueError as e:
            print(f"  EROARE: {e}")
    
    print("\n" + "=" * 60)
    print("Gata.")
    print("=" * 60)


if __name__ == "__main__":
    main()
