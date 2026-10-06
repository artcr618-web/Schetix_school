#!/usr/bin/env python3
"""Разбирает страницы всеконтрольные.рф / контрользнаний.рф с контрольными.

Структура страницы: текст темы («Контрольная К-1. Проверяемые темы: §…»)
и сразу за ним ссылки «К-1. Вариант 1…4». Собираем пары (тема, варианты).

    python3 Инструменты/sbor_kontrolnye.py <url> [<url> ...]
    -> печатает JSON-подобную структуру
"""
import html
import json
import re
import subprocess
import sys

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/120 Safari/537.36')
SSYL = re.compile(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', re.S)
TEG = re.compile(r'<[^>]+>')
VAR = re.compile(r'(вариант|вар\.)\s*(\d)', re.I)


def skachat(url):
    p = subprocess.run(['curl', '-sS', '-m', '60', '-A', UA, '-L', url],
                       capture_output=True)
    return p.stdout.decode('utf-8', 'replace')


def chist(s):
    return re.sub(r'\s+', ' ', html.unescape(TEG.sub('', s))).strip()


def razobrat(url):
    h = skachat(url)
    i = h.find('entry-content')
    if i < 0:
        i = h.find('<h1')
    j = h.find('Навигация по записям')
    k = h.find('комментари', i)
    kon = min([x for x in (j, k) if x > 0] or [len(h)])
    seg = h[i:kon]
    # режем на куски: ссылки и текст между ними
    kuski = []
    pos = 0
    for m in SSYL.finditer(seg):
        kuski.append(('txt', seg[pos:m.start()]))
        kuski.append(('a', m))
        pos = m.end()
    kuski.append(('txt', seg[pos:]))
    gruppy = []
    tek_tekst = ''
    tek_ssyl = []
    for tip, k in kuski:
        if tip == 'a':
            t = chist(k.group(2))
            u = k.group(1)
            if not VAR.search(t):
                continue
            if u.startswith('/'):
                # относительная ссылка -> абсолютная
                dom = re.match(r'(https?://[^/]+)', url).group(1)
                u = dom + u
            tek_ssyl.append([t, u])
        else:
            t = chist(k)
            if len(t) < 4:
                continue
            if tek_ssyl:
                gruppy.append({'tema': tek_tekst, 'ssylki': tek_ssyl})
                tek_ssyl = []
            tek_tekst = t
    if tek_ssyl:
        gruppy.append({'tema': tek_tekst, 'ssylki': tek_ssyl})
    # подчищаем темы: обрезаем до 200 знаков, убираем «&nbsp;»
    for g in gruppy:
        g['tema'] = g['tema'].replace('\xa0', ' ').strip(' |')[:220]
    return gruppy


def main():
    dan = {}
    for url in sys.argv[1:]:
        g = razobrat(url)
        dan[url] = g
        print(f'=== {url}  ({len(g)} работ)')
        for x in g:
            print(f"  {x['tema'][:90]}")
            for t, u in x['ssylki']:
                print(f"      {t[:24]:26} {u}")
    print(json.dumps(dan, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
