import os
import re

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

base_path = r'e:\Carte\BB\17 - Site Leadership\Principal 2022\en'
python_path = r'e:\Carte\BB\17 - Site Leadership\Principal 2022\en\Python'

print("=" * 80)
print("PASUL 1: Numărare articole corecte (după 'by Neculai Fantanaru')")
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

print("\n" + "=" * 80)
print("PASUL 2: Căutare fișiere cu numere incorecte")
print("=" * 80)

files_with_errors = []
total_checked = 0

for folder_path in [base_path, python_path]:
    if not os.path.exists(folder_path):
        continue

    all_files = [f for f in os.listdir(folder_path) if f.endswith('.html')]

    for html_file in all_files:
        file_path = os.path.join(folder_path, html_file)
        total_checked += 1

        print(f"  Verificare: {html_file}", end="", flush=True)

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        categories_match = re.search(r'<!-- Categories -->.*?(<!-- BOOKS START -->|$)', content, re.DOTALL)

        if not categories_match:
            print(" - fără secțiune Categories")
            continue

        categories_section = categories_match.group(0)

        file_errors = []

        for category_file, expected_count in category_counts.items():
            url = f"https://neculaifantanaru.com/en/{category_file}"
            pattern = r'<a\s+href="' + re.escape(url) + r'"[^>]*>.*?<span>(\d+)</span>'
            matches = re.findall(pattern, categories_section, flags=re.DOTALL)

            for found in matches:
                if found != str(expected_count):
                    file_errors.append({
                        'category': category_file,
                        'found': found,
                        'expected': expected_count
                    })

        if file_errors:
            files_with_errors.append({
                'file': html_file,
                'folder': folder_path,
                'errors': file_errors
            })
            print(f" - ERORI: {len(file_errors)}")
        else:
            print(" - OK")

print(f"\n{'=' * 80}")
print(f"REZULTAT")
print(f"{'=' * 80}")
print(f"Total fișiere verificate: {total_checked}")
print(f"Fișiere cu numere incorecte: {len(files_with_errors)}")

if files_with_errors:
    print(f"\n{'=' * 80}")
    print(f"FIȘIERE CU PROBLEME:")
    print(f"{'=' * 80}")

    for i, error_info in enumerate(files_with_errors[:20], 1):
        print(f"\n{i}. {error_info['file']}")
        print(f"   Locație: {error_info['folder']}")
        for err in error_info['errors'][:3]:
            print(f"   La partea -> {err['category']}: acum găsit={err['found']}, dar corect trebuia sa fie = {err['expected']}")
        if len(error_info['errors']) > 3:
            print(f"   ... și încă {len(error_info['errors']) - 3} erori")

    if len(files_with_errors) > 20:
        print(f"\n... și încă {len(files_with_errors) - 20} fișiere cu erori")
else:
    print("\n✓✓✓ PERFECT! Toate fișierele au numerele corecte!")

print(f"\n{'=' * 80}")