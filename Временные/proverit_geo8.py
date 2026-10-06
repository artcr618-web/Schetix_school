# -*- coding: utf-8 -*-
"""Проверяет все внешние ссылки на четырёх страницах геометрии 8 класса.

    python3 Временные/proverit_geo8.py
"""
import concurrent.futures as futures
import io
import os
import re
import subprocess

PAPKA = os.path.join('8 класс', 'Геометрия')
FAYLY = ['geometriya-8-klass-video.html',
         'geometriya-8-klass-trenazhery.html',
         'geometriya-8-klass-kontrolnye.html',
         'geometriya-8-klass-itogovye-i-sborniki.html']

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/126.0 Safari/537.36')


def kod(url):
    r = subprocess.run(
        ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}',
         '-L', '--max-time', '30', '-A', UA, url],
        capture_output=True, text=True)
    return r.stdout.strip() or '000'


def main():
    ssylki = {}
    for f in FAYLY:
        s = io.open(os.path.join(PAPKA, f), encoding='utf-8').read()
        for m in re.finditer(r'href="(https?://[^"]+)"', s):
            ssylki.setdefault(m.group(1), []).append(f)
    vse = sorted(ssylki)
    print(f'ссылок всего: {len(vse)} (уникальных)')

    with futures.ThreadPoolExecutor(max_workers=8) as ex:
        kody = dict(zip(vse, ex.map(kod, vse)))

    ploho = {u: k for u, k in kody.items() if k != '200'}
    print(f'из них 200: {len(vse) - len(ploho)}')
    if ploho:
        print('\nНЕ 200:')
        for u, k in sorted(ploho.items()):
            print(f'  {k}  {u}')
            print(f'        страницы: {", ".join(sorted(set(ssylki[u])))}')
    else:
        print('битых нет')


if __name__ == '__main__':
    main()
