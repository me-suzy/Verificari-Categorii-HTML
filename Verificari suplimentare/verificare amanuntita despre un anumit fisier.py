import re

file_path = r'e:\Carte\BB\17 - Site Leadership\Principal 2022\ro\python-scripts-examples.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

print("Căutare diferite tipuri de conținut:\n")

# Caută tag-uri code
code_tags = len(re.findall(r'<code[^>]*>', content))
print(f"Tag-uri <code>: {code_tags}")

# Caută scripturi
scripts = len(re.findall(r'<script[^>]*>.*?</script>', content, re.DOTALL))
print(f"Tag-uri <script>: {scripts}")

# Caută iframe-uri
iframes = len(re.findall(r'<iframe[^>]*>', content))
print(f"Tag-uri <iframe>: {iframes}")

# Caută link-uri către librării externe
if 'prism' in content.lower():
    print("\n✓ Găsit: Prism.js")
if 'highlight' in content.lower():
    print("✓ Găsit: Highlight.js")
if 'codemirror' in content.lower():
    print("✓ Găsit: CodeMirror")
if 'ace.js' in content.lower():
    print("✓ Găsit: Ace Editor")

# Caută foarte mult JavaScript inline
js_inline = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
total_js_size = sum(len(js) for js in js_inline)
print(f"\nDimensiune JavaScript inline: {total_js_size:,} caractere")

# Verifică dacă sunt multe imagini
images = len(re.findall(r'<img[^>]*>', content))
print(f"Total imagini: {images}")

# Caută text foarte lung în articole (poate cod stocat ca text)
article_sections = re.findall(r'<article[^>]*>(.*?)</article>', content, re.DOTALL)
if article_sections:
    avg_article_size = sum(len(a) for a in article_sections) / len(article_sections)
    print(f"\nArticole găsite: {len(article_sections)}")
    print(f"Dimensiune medie articol: {avg_article_size:,.0f} caractere")