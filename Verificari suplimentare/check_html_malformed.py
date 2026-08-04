"""
Script pentru detectarea problemelor HTML care pot cauza încărcare lentă:
- Tag-uri HTML în text (trebuie să fie entități: &lt;title&gt;)
- Tag-uri neînchise
- Structură HTML malformată
"""

import re
import os
import sys

def check_html_in_text(content, section_start_marker='<!-- ARTICOL START -->', section_end_marker='<!-- ARTICOL FINAL -->'):
    """
    Verifică dacă există tag-uri HTML în text (care ar trebui să fie entități)
    """
    # Găsește secțiunea
    start = content.find(section_start_marker)
    end = content.find(section_end_marker)
    
    if start == -1 or end == -1:
        return []
    
    section = content[start:end]
    
    # Tag-uri HTML care NU ar trebui să fie în text
    forbidden_tags = ['title', 'meta', 'script', 'style', 'head', 'body', 'html', 'doctype']
    
    issues = []
    
    for tag in forbidden_tags:
        # Caută <tag> sau <tag ...> care NU este &lt;tag&gt;
        pattern = rf'(?<!&lt;)<{tag}(?:\s[^>]*)?>'
        matches = list(re.finditer(pattern, section, re.IGNORECASE))
        
        for match in matches:
            pos = match.start() + start  # Poziție în întregul fișier
            tag_content = match.group(0)
            
            # Verifică contextul
            section_pos = match.start()
            last_a = section.rfind('<a', 0, section_pos)
            last_p = section.rfind('<p', 0, section_pos)
            last_h = section.rfind('<h', 0, section_pos)
            
            context = None
            if last_a != -1 and (last_p == -1 or last_a > last_p) and (last_h == -1 or last_a > last_h):
                next_close_a = section.find('</a>', section_pos)
                if next_close_a == -1 or next_close_a > section_pos:
                    context = 'link'
            elif last_p != -1:
                next_close_p = section.find('</p>', section_pos)
                if next_close_p == -1 or next_close_p > section_pos:
                    context = 'paragraph'
            elif last_h != -1:
                context = 'heading'
            
            if context:
                # Extrage contextul pentru afișare
                context_start = max(0, section_pos - 50)
                context_end = min(len(section), section_pos + 100)
                context_text = section[context_start:context_end]
                
                issues.append({
                    'tag': tag,
                    'position': pos,
                    'context_type': context,
                    'content': tag_content,
                    'context': context_text
                })
    
    return issues

def check_unclosed_tags(content, section_start_marker='<!-- ARTICOL START -->', section_end_marker='<!-- ARTICOL FINAL -->'):
    """
    Verifică tag-uri neînchise în secțiunea de articole
    """
    start = content.find(section_start_marker)
    end = content.find(section_end_marker)
    
    if start == -1 or end == -1:
        return []
    
    section = content[start:end]
    
    issues = []
    
    # Verifică tag-uri <a>
    opens_a = section.count('<a')
    closes_a = section.count('</a>')
    if opens_a != closes_a:
        issues.append({
            'tag': 'a',
            'opens': opens_a,
            'closes': closes_a,
            'difference': opens_a - closes_a
        })
    
    # Verifică tag-uri <p>
    opens_p = section.count('<p')
    closes_p = section.count('</p>')
    if opens_p != closes_p:
        issues.append({
            'tag': 'p',
            'opens': opens_p,
            'closes': closes_p,
            'difference': opens_p - closes_p
        })
    
    return issues

def analyze_file(file_path):
    """
    Analizează un fișier HTML pentru probleme
    """
    print(f"\n{'=' * 80}")
    print(f"Analiză: {os.path.basename(file_path)}")
    print("=" * 80)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"✗ Eroare la citire: {e}")
        return
    
    # 1. Verifică tag-uri HTML în text
    html_in_text = check_html_in_text(content)
    
    if html_in_text:
        print(f"\n⚠ GĂSITE {len(html_in_text)} TAG-URI HTML ÎN TEXT:")
        for i, issue in enumerate(html_in_text, 1):
            print(f"\n{i}. Tag <{issue['tag']}> în {issue['context_type']}")
            print(f"   Poziție: {issue['position']}")
            print(f"   Conținut: {issue['content'][:80]}...")
            print(f"   Context: ...{issue['context']}...")
    else:
        print("\n✓ Nu s-au găsit tag-uri HTML în text")
    
    # 2. Verifică tag-uri neînchise
    unclosed = check_unclosed_tags(content)
    
    if unclosed:
        print(f"\n⚠ TAG-URI NEÎNCHISE:")
        for issue in unclosed:
            print(f"   - <{issue['tag']}>: {issue['opens']} deschise, {issue['closes']} închise (diferență: {issue['difference']})")
    else:
        print("\n✓ Toate tag-urile sunt închise corect")
    
    return len(html_in_text) > 0 or len(unclosed) > 0

if __name__ == '__main__':
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = r'e:\Carte\BB\17 - Site Leadership\Principal 2022\ro\python-scripts-examples.html'
    
    has_issues = analyze_file(file_path)
    
    print("\n" + "=" * 80)
    if has_issues:
        print("⚠ Fișierul are probleme HTML care pot cauza încărcare lentă!")
    else:
        print("✓ Fișierul este OK")
    print("=" * 80)

