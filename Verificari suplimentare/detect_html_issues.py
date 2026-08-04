import re
from collections import Counter

file_path = r'e:\Carte\BB\17 - Site Leadership\Principal 2022\ro\python-scripts-examples.html'

print("=" * 80)
print("DETECTARE PROBLEME HTML ÎN ARTICOLE")
print("=" * 80)

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Găsește secțiunea
start = content.find('<!-- ARTICOL START -->')
end = content.find('<!-- ARTICOL FINAL -->')

if start == -1 or end == -1:
    print("Nu am găsit secțiunea!")
    exit()

section = content[start:end]

# Extrage toate articolele
articles = re.findall(r'<article[^>]*>.*?</article>', section, re.DOTALL)

print(f"\nTotal articole: {len(articles)}\n")

problematic_articles = []

for idx, article in enumerate(articles, 1):
    issues = []
    
    # 1. Verifică tag-uri HTML în interiorul atributelor sau textului
    # Detectează tag-uri HTML în interiorul atributelor (ex: href="...<title>...")
    html_in_attributes = re.findall(r'="[^"]*<[^"]*"', article)
    if html_in_attributes:
        issues.append(f"Tag-uri HTML în atribute ({len(html_in_attributes)})")
    
    # Detectează tag-uri HTML în interiorul textului link-urilor sau paragrafelor
    # (ex: <a>...<title>...</a> sau <p>...<meta>...</p>)
    suspicious_patterns = [
        (r'<a[^>]*>.*?<title>.*?</a>', 'Tag <title> în interiorul link-ului'),
        (r'<a[^>]*>.*?<meta[^>]*>.*?</a>', 'Tag <meta> în interiorul link-ului'),
        (r'<p[^>]*>.*?<title>.*?</p>', 'Tag <title> în interiorul paragrafului'),
        (r'<p[^>]*>.*?<meta[^>]*>.*?</p>', 'Tag <meta> în interiorul paragrafului'),
        (r'<h[1-6][^>]*>.*?<title>.*?</h[1-6]>', 'Tag <title> în interiorul heading-ului'),
        (r'<h[1-6][^>]*>.*?<meta[^>]*>.*?</h[1-6]>', 'Tag <meta> în interiorul heading-ului'),
    ]
    
    for pattern, description in suspicious_patterns:
        if re.search(pattern, article, re.DOTALL):
            issues.append(description)
    
    # 2. Verifică tag-uri neînchise sau malformate
    # Verifică dacă există tag-uri care se suprapun incorect
    tag_stack = []
    tag_pattern = r'<(/?)([a-zA-Z][a-zA-Z0-9]*)[^>]*?(/?)>'
    
    for match in re.finditer(tag_pattern, article):
        is_closing = match.group(1) == '/'
        tag_name = match.group(2).lower()
        is_self_closing = match.group(3) == '/' or tag_name in ['img', 'br', 'hr', 'input', 'meta', 'link']
        
        if not is_closing and not is_self_closing:
            tag_stack.append(tag_name)
        elif is_closing:
            if tag_stack and tag_stack[-1] == tag_name:
                tag_stack.pop()
            elif tag_name in tag_stack:
                issues.append(f"Tag-uri suprapuse incorect: {tag_name}")
    
    if tag_stack:
        issues.append(f"Tag-uri neînchise: {', '.join(tag_stack[:5])}")
    
    # 3. Verifică structură anormală (articole care diferă de structura standard)
    # Structura standard: <article> -> <div class="blog-listing-inner"> -> <div class="news_desc"> -> <h2/h3> -> <a>
    has_standard_structure = (
        'blog-listing-inner' in article and
        'news_desc' in article and
        re.search(r'<h[23][^>]*>', article) and
        re.search(r'<a[^>]*href=', article)
    )
    
    if not has_standard_structure:
        issues.append("Structură non-standard")
    
    # 4. Verifică conținut suspect în link-uri
    # Link-uri care conțin tag-uri HTML în text
    links = re.findall(r'<a[^>]*>(.*?)</a>', article, re.DOTALL)
    for link_text in links:
        # Elimină tag-urile HTML permise (ex: <span>, <i>)
        clean_text = re.sub(r'<(span|i|em|strong|b)[^>]*>.*?</\1>', '', link_text, flags=re.DOTALL)
        # Verifică dacă mai rămân tag-uri HTML
        if re.search(r'<[^>]+>', clean_text):
            issues.append("Tag-uri HTML suspecte în textul link-urilor")
            break
    
    # 5. Verifică dimensiune anormală
    article_size = len(article)
    avg_size = sum(len(a) for a in articles) / len(articles)
    
    if article_size > avg_size * 1.5:  # 50% mai mare decât media
        issues.append(f"Dimensiune anormală: {article_size} bytes (media: {avg_size:.0f})")
    
    # 6. Verifică caractere speciale sau entități HTML suspecte
    # Detectează entități HTML în locuri neobișnuite
    if article.count('&lt;') > 5 or article.count('&gt;') > 5:
        issues.append("Multe entități HTML (&lt; sau &gt;)")
    
    # 7. Verifică dacă există tag-uri HTML ca text (nu ca tag-uri)
    # De ex: <title> sau <meta> care ar trebui să fie entități HTML
    html_tags_as_text = re.findall(r'[^<]<title[^>]*>', article) + re.findall(r'[^<]<meta[^>]*>', article)
    if html_tags_as_text:
        issues.append(f"Tag-uri HTML ca text (nu ca entități): {len(html_tags_as_text)}")
    
    if issues:
        # Extrage titlul
        title_match = re.search(r'<h[23][^>]*>.*?<a[^>]*>(.*?)</a>', article, re.DOTALL)
        title = title_match.group(1).strip()[:80] if title_match else "Fără titlu"
        
        problematic_articles.append({
            'index': idx,
            'title': title,
            'size': article_size,
            'issues': issues,
            'article': article
        })
        
        print(f"⚠ ARTICOL #{idx}: {title[:60]}...")
        for issue in issues:
            print(f"   - {issue}")
        print()

if problematic_articles:
    print("=" * 80)
    print(f"REZUMAT: {len(problematic_articles)} articole cu probleme")
    print("=" * 80)
    
    # Găsește articolul cu cele mai multe probleme
    worst = max(problematic_articles, key=lambda x: len(x['issues']))
    
    print(f"\n{'=' * 80}")
    print(f"ARTICOLUL CEL MAI PROBLEMATIC: #{worst['index']}")
    print("=" * 80)
    print(f"Titlu: {worst['title']}")
    print(f"Dimensiune: {worst['size']} bytes")
    print(f"Probleme: {len(worst['issues'])}")
    print("\nToate problemele:")
    for issue in worst['issues']:
        print(f"  - {issue}")
    
    # Afișează porțiunea problematică
    print(f"\n{'=' * 80}")
    print("CONȚINUT ARTICOL (primele 2000 caractere):")
    print("=" * 80)
    print(worst['article'][:2000])
    if len(worst['article']) > 2000:
        print("\n... (trunchiat)")
    
    # Caută specific problemele
    print(f"\n{'=' * 80}")
    print("ANALIZĂ DETALIATĂ:")
    print("=" * 80)
    
    # Caută tag-uri HTML în atribute
    html_in_attrs = re.findall(r'="([^"]*<[^"]*)"', worst['article'])
    if html_in_attrs:
        print(f"\n1. Tag-uri HTML în atribute găsite:")
        for attr in html_in_attrs[:3]:
            print(f"   {attr[:150]}...")
    
    # Caută tag-uri HTML în text
    html_in_text = re.findall(r'<a[^>]*>(.*?<title>.*?)</a>', worst['article'], re.DOTALL)
    if not html_in_text:
        html_in_text = re.findall(r'<a[^>]*>(.*?<meta[^>]*>.*?)</a>', worst['article'], re.DOTALL)
    if html_in_text:
        print(f"\n2. Tag-uri HTML în textul link-urilor:")
        for text in html_in_text[:2]:
            print(f"   {text[:200]}...")
    
    # Caută tag-uri HTML în paragrafe
    html_in_p = re.findall(r'<p[^>]*>(.*?<title>.*?)</p>', worst['article'], re.DOTALL)
    if not html_in_p:
        html_in_p = re.findall(r'<p[^>]*>(.*?<meta[^>]*>.*?)</p>', worst['article'], re.DOTALL)
    if html_in_p:
        print(f"\n3. Tag-uri HTML în paragrafe:")
        for text in html_in_p[:2]:
            print(f"   {text[:200]}...")
    
else:
    print("\n✓ Nu s-au găsit articole cu probleme HTML majore")

print("\n" + "=" * 80)

