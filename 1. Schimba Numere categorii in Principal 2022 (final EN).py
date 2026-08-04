import os
import re
from pathlib import Path

category_files = [
    'leadership-and-attitude.html',
    'leadership-magic.html',
    'successful-leadership.html',
    'hr-human-resources.html',
    'leadership-laws.html',
    'total-leadership.html',
    'leadership-that-lasts.html',
    'leadership-principles.html',
    'leadership-plus.html',
    'qualities-of-a-leader.html',
    'top-leadership.html',
    'leadership-impact.html',
    'personal-development.html',
    'leadership-skills-and-abilities.html',
    'real-leadership.html',
    'basic-leadership.html',
    'leadership-360.html',
    'leadership-pro.html',
    'leadership-expert.html',
    'leadership-know-how.html',
    'leadership-journal.html',
    'alpha-leadership.html',
    'leadership-on-off.html',
    'leadership-deluxe.html',
    'leadership-xxl.html',
    'leadership-50-extra.html',
    'leadership-fusion.html',
    'leadership-v8.html',
    'leadership-x3-silver.html',
    'leadership-q2-sensitive.html',
    'leadership-t7-hybrid.html',
    'leadership-n6-celsius.html',
    'leadership-s4-quartz.html',
    'leadership-gt-accent.html',
    'leadership-fx-intensive.html',
    'leadership-iq-light.html',
    'leadership-7th-edition.html',
    'leadership-xs-analytics.html',
    'leadership-z3-extended.html',
    'leadership-ex-elite.html',
    'leadership-w3-integra.html',
    'leadership-sx-experience.html',
    'leadership-y5-superzoom.html',
    'performance-ex-flash.html',
    'leadership-mindware.html',
    'leadership-r2-premiere.html',
    'leadership-y4-titanium.html',
    'leadership-quantum-xx.html',
    'python-scripts-examples.html',
]

title_to_file = {
    'Leadership and Attitude': 'leadership-and-attitude.html',
    'Leadership Magic': 'leadership-magic.html',
    'Successful Leadership': 'successful-leadership.html',
    'Human Resources': 'hr-human-resources.html',
    'Leadership Laws': 'leadership-laws.html',
    'Total Leadership': 'total-leadership.html',
    'Leadership That Lasts': 'leadership-that-lasts.html',
    'Leadership Principles': 'leadership-principles.html',
    'Leadership Plus': 'leadership-plus.html',
    'Qualities of A Leader': 'qualities-of-a-leader.html',
    'Top Leadership': 'top-leadership.html',
    'Leadership Impact': 'leadership-impact.html',
    'Personal Development': 'personal-development.html',
    'Skills and Abilities': 'leadership-skills-and-abilities.html',
    'Real Leadership': 'real-leadership.html',
    'Basic Leadership': 'basic-leadership.html',
    'Leadership 360&#730;': 'leadership-360.html',
    'Leadership 360°': 'leadership-360.html',
    'Leadership Pro': 'leadership-pro.html',
    'Leadership Expert': 'leadership-expert.html',
    'Leadership Know-How': 'leadership-know-how.html',
    'Leadership Journal': 'leadership-journal.html',
    'Alpha Leadership': 'alpha-leadership.html',
    'Leadership On/Off': 'leadership-on-off.html',
    'Leadership Deluxe': 'leadership-deluxe.html',
    'Leadership XXL-Pack': 'leadership-xxl.html',
    'Leadership &plus;50% Extra': 'leadership-50-extra.html',
    'Leadership +50% Extra': 'leadership-50-extra.html',
    'Leadership Fusion': 'leadership-fusion.html',
    'Leadership V8': 'leadership-v8.html',
    'Leadership X3-Silver': 'leadership-x3-silver.html',
    'Leadership Q2-Sensitive': 'leadership-q2-sensitive.html',
    'Leadership T7-Hybrid': 'leadership-t7-hybrid.html',
    'Leadership N6-Celsius': 'leadership-n6-celsius.html',
    'Leadership S4-Quartz': 'leadership-s4-quartz.html',
    'Leadership GT-Accent': 'leadership-gt-accent.html',
    'Leadership FX-Intensive': 'leadership-fx-intensive.html',
    'Leadership IQ-Light': 'leadership-iq-light.html',
    'Leadership 7th Edition': 'leadership-7th-edition.html',
    'Leadership XS-Analytics': 'leadership-xs-analytics.html',
    'Leadership Z3-Extended': 'leadership-z3-extended.html',
    'Leadership eX-Elite': 'leadership-ex-elite.html',
    'Leadership W3-Integra': 'leadership-w3-integra.html',
    'Leadership sX-Experience': 'leadership-sx-experience.html',
    'Leadership Y5-SuperZoom': 'leadership-y5-superzoom.html',
    'Performance eX-Flash': 'performance-ex-flash.html',
    'Leadership Mindware': 'leadership-mindware.html',
    'Leadership R2-Premiere': 'leadership-r2-premiere.html',
    'Leadership Y4-Titanium': 'leadership-y4-titanium.html',
    'Leadership Quantum-XX': 'leadership-quantum-xx.html',
    'Python Scripts Examples': 'python-scripts-examples.html',
}

base_path = r'e:\Carte\BB\17 - Site Leadership\Principal 2022\en'
python_path = r'e:\Carte\BB\17 - Site Leadership\Principal 2022\en\Python'

print("=" * 80)
print("PASUL 1: Numărare articole (după 'by Neculai Fantanaru')")
print("=" * 80)

category_counts = {}
for category_file in category_files:
    file_path = os.path.join(base_path, category_file)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            count = content.count('by Neculai Fantanaru')
            category_counts[category_file] = count
            print(f"  {category_file}: {count}")
    except FileNotFoundError:
        category_counts[category_file] = 0
        print(f"  {category_file}: NU GĂSIT")

print("\n" + "=" * 80)
print("PASUL 2: Corectare link-uri + Actualizare numere")
print("=" * 80)

total_fixed = 0

for folder_path in [base_path, python_path]:
    if not os.path.exists(folder_path):
        continue

    print(f"\nProcesare folder: {folder_path}")
    all_files = [f for f in os.listdir(folder_path) if f.endswith('.html')]

    for index, html_file in enumerate(all_files, 1):
        file_path = os.path.join(folder_path, html_file)

        if index % 100 == 0:
            print(f"  Procesat {index}/{len(all_files)} fișiere...")

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        categories_match = re.search(r'(<!-- Categories -->.*?)(<!-- BOOKS START -->|$)', content, re.DOTALL)

        if not categories_match:
            continue

        before_categories = content[:categories_match.start(1)]
        categories_section = categories_match.group(1)
        after_categories = content[categories_match.end(1):]

        original_categories = categories_section

        # Corectare link-uri (înlocuiește .ro cu .com și corectează path-ul)
        for title, correct_file in title_to_file.items():
            # Pattern care acceptă atât .com cât și .ro
            pattern = r'href="https://neculaifantanaru\.(?:com|ro)/en/[^"]+" title="' + re.escape(title) + r'"'
            correct_href = f'href="https://neculaifantanaru.com/en/{correct_file}" title="{title}"'
            categories_section = re.sub(pattern, correct_href, categories_section)

        # Actualizare numere - MODIFICAT să accepte atât .com cât și .ro
        for category_file, count in category_counts.items():
            # 1) Corectare erori de tipul <span>39</p> (fără </span>)
            broken_pattern = (
                r'(<a\s+href="https://neculaifantanaru\.(?:com|ro)/en/'
                + re.escape(category_file) +
                r'"[^>]*>.*?<span>)(\d+)(</p>)'
            )

            def fix_broken_span(match):
                old = match.group(2)
                new = str(count)
                print(f"  ⚠ Corectat span lipsă în {html_file} - {category_file}: {old} -> {new}")
                # reintroducem </span> înainte de </p> și punem numărul corect
                return match.group(1) + new + '</span>' + match.group(3)

            categories_section, broken_replacements = re.subn(
                broken_pattern,
                fix_broken_span,
                categories_section,
                flags=re.DOTALL
            )

            # 2) Actualizare normală pentru cazurile corecte <span>39</span>
            pattern = (
                r'(<a\s+href="https://neculaifantanaru\.(?:com|ro)/en/'
                + re.escape(category_file) +
                r'"[^>]*>.*?<span>)\d+(</span>)'
            )

            def replace_number(match):
                return match.group(1) + str(count) + match.group(2)

            categories_section = re.sub(pattern, replace_number, categories_section, flags=re.DOTALL)

        if categories_section != original_categories:
            new_content = before_categories + categories_section + after_categories
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            total_fixed += 1
            print(f"  ✅ Actualizat fișierul: {html_file}")

print(f"\nTotal fișiere actualizate: {total_fixed}\n")

print("=" * 80)
print("VERIFICARE FINALĂ (EN)")
print("=" * 80)

errors = 0
checked_files = 0
checked_links = 0

for folder_path in [base_path, python_path]:
    if not os.path.exists(folder_path):
        continue

    html_files = [f for f in os.listdir(folder_path) if f.endswith('.html')]
    print(f"\n📁 Folder: {folder_path} — {len(html_files)} fișiere HTML găsite")

    for html_file in html_files:
        file_path = os.path.join(folder_path, html_file)
        checked_files += 1

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        categories_match = re.search(r'<!-- Categories -->.*?(<!-- BOOKS START -->|$)', content, re.DOTALL)

        if not categories_match:
            continue

        categories_section = categories_match.group(0)
        file_errors = 0

        for category_file, expected_count in category_counts.items():
            # Verificare care acceptă atât .com cât și .ro
            pattern = r'<a\s+href="https://neculaifantanaru\.(?:com|ro)/en/' + re.escape(category_file) + r'"[^>]*>.*?<span>(\d+)</span>'
            matches = re.findall(pattern, categories_section, flags=re.DOTALL)

            for found in matches:
                checked_links += 1
                if found != str(expected_count):
                    print(f"  ❌ EROARE: {html_file} - {category_file}: {found} != {expected_count}")
                    errors += 1
                    file_errors += 1

if errors == 0:
    print("\n✓✓✓ PERFECT! Toate link-urile și numerele sunt corecte!")
else:
    print(f"\n✗ Total erori: {errors} din {checked_links} link-uri verificate ({checked_files} fișiere analizate)")

print("=" * 80)