# -*- coding: utf-8 -*-
"""Проверяет javascript в страницах пакета: node --check на каждый блок."""
import os, re, io, subprocess, tempfile
P = 'Проект'
bad = n = 0
for root, _, fs in os.walk(P):
    for f in sorted(fs):
        if not f.endswith('.html'):
            continue
        s = io.open(os.path.join(root, f), encoding='utf-8').read()
        js = re.findall(r'<script>(.*?)</script>', s, re.S)
        if not js:
            continue
        n += 1
        t = tempfile.NamedTemporaryFile('w', suffix='.js', delete=False,
                                        encoding='utf-8')
        t.write('\n'.join(js)); t.close()
        r = subprocess.run(['node', '--check', t.name], capture_output=True,
                           text=True)
        os.unlink(t.name)
        if r.returncode:
            bad += 1
            print('ОШИБКА JS', os.path.relpath(os.path.join(root, f), P))
            print(r.stderr[:400])
print(f'проверено страниц со скриптом: {n}, ошибок: {bad}')
