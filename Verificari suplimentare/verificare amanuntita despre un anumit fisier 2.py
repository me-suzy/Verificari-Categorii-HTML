import re

file_path = r'e:\Carte\BB\17 - Site Leadership\Principal 2022\ro\python-scripts-examples.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

print("=" * 80)
print("ANALIZĂ IFRAME-URI")
print("=" * 80)

# Găsește toate iframe-urile
iframes = re.findall(r'<iframe[^>]*>.*?</iframe>', content, re.DOTALL | re.IGNORECASE)

if not iframes:
    # Încearcă doar tag-ul de deschidere
    iframes = re.findall(r'<iframe[^>]*/?>', content, re.IGNORECASE)

print(f"\nGăsite {len(iframes)} iframe-uri:\n")

for i, iframe in enumerate(iframes, 1):
    print(f"IFRAME {i}:")
    print("-" * 60)

    # Extrage atribute importante
    src_match = re.search(r'src=["\']([^"\']+)["\']', iframe)
    width_match = re.search(r'width=["\']([^"\']+)["\']', iframe)
    height_match = re.search(r'height=["\']([^"\']+)["\']', iframe)
    loading_match = re.search(r'loading=["\']([^"\']+)["\']', iframe)

    if src_match:
        print(f"  src: {src_match.group(1)}")
    if width_match:
        print(f"  width: {width_match.group(1)}")
    if height_match:
        print(f"  height: {height_match.group(1)}")
    if loading_match:
        print(f"  loading: {loading_match.group(1)}")
    else:
        print(f"  loading: ⚠ NU ARE (încarcă imediat, poate bloca pagina!)")

    print()

print("=" * 80)
print("SOLUȚIE:")
print("Adaugă loading='lazy' la iframe-uri pentru a nu bloca pagina!")
print("=" * 80)