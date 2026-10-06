import re, html, os
pat = re.compile(r'[^.]{0,200}(?:учебник[а-яё]*|УМК|Просвещени|Дрофа|Вентана|Полярная звезда|Русское слово|Титул|Spotlight|автор)[^.]{0,200}\.', re.I)
for root, dirs, files in os.walk('Архив'):
    for imya in sorted(files):
        if not imya.endswith('.html'):
            continue
        p = os.path.join(root, imya)
        t = open(p, encoding='utf-8').read()
        t = re.sub(r'<script.*?</script>|<style.*?</style>', ' ', t, flags=re.S)
        t = html.unescape(re.sub(r'<[^>]+>', ' ', t))
        t = re.sub(r'\s+', ' ', t)
        print('=' * 8, p)
        seen = set()
        for m in pat.finditer(t):
            s = m.group(0).strip()
            k = s.lower()
            if k in seen:
                continue
            seen.add(k)
            print('  -', s[:300])
