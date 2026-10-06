#!/usr/bin/env python3
"""Собирает все варианты ВПР по математике 7 класса с vprklass.ru.

Результат: Временные/vpr_matematika7.json
    [ { "zag": "...", "url": "...", "chasti": [
          { "nazvanie": "Часть 1", "komplekty": [ {"n":1,"ssylki":[[текст,url],...]}, ... ] } ] } ]
"""
import json
import os
import re
import subprocess
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/120 Safari/537.36')
RAZDEL = 'https://vprklass.ru/7-klass/matematika-7-klass/'
FAIL_EXT = re.compile(r'\.(pdf|jpg|jpeg|png|doc|docx|zip|rar|xls|xlsx)$', re.I)


def skachat(url):
    p = subprocess.run(['curl', '-sS', '-m', '60', '-A', UA, url],
                       capture_output=True)
    return p.stdout.decode('utf-8', 'replace')


def posty():
    """Все ссылки на записи внутри раздела (со всех страниц пагинации)."""
    nashli = []
    str_ = 1
    while str_ <= 4:
        url = RAZDEL if str_ == 1 else f'{RAZDEL}page/{str_}'
        h = skachat(url)
        novye = 0
        for m in re.finditer(r'href="(https://vprklass\.ru/7-klass/matematika-7-klass/([a-z0-9\-]+))(#more-\d+)?"', h):
            u = m.group(1)
            if u.endswith(f'/page/{str_}'):
                continue
            if u not in nashli:
                nashli.append(u)
                novye += 1
        if not novye:
            break
        str_ += 1
        time.sleep(0.3)
    return nashli


def zagolovok(h):
    m = re.search(r'<h1[^>]*class="entry-title"[^>]*>(.*?)</h1>', h, re.S)
    if not m:
        m = re.search(r'<h1[^>]*>(.*?)</h1>', h, re.S)
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', m.group(1))).strip() if m else ''


def razobrat_post(url):
    h = skachat(url)
    m = re.search(r'<div class="entry-content">(.*?)<footer', h, re.S)
    seg = m.group(1) if m else h
    # убираем «Связанные страницы»
    i = seg.find('Связанные страницы')
    if i > 0:
        seg = seg[:i]
    chasti = []
    # идём по блокам: ищем заголовки/абзацы-названия и следующие за ними таблицы
    kuski = re.split(r'(<table[^>]*>.*?</table>)', seg, flags=re.S)
    tek_tekst = ''
    for k in kuski:
        if k.startswith('<table'):
            stroki = []
            for tr in re.findall(r'<tr[^>]*>(.*?)</tr>', k, re.S):
                ssyl = []
                for a in re.finditer(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', tr, re.S):
                    u = a.group(1)
                    t = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', a.group(2))).strip()
                    if FAIL_EXT.search(u):
                        ssyl.append([t, u])
                if ssyl:
                    stroki.append(ssyl)
            if stroki:
                # первая строка — шапка? если в ней нет ссылок на файлы, она уже отсеяна
                naz = tek_tekst.strip(' .—-')
                komplekty = [{'n': i + 1, 'ssylki': s} for i, s in enumerate(stroki)]
                chasti.append({'nazvanie': naz or 'Варианты', 'komplekty': komplekty})
            tek_tekst = ''
        else:
            # название части = текст последнего блока (h2/h3/p/strong)
            # перед таблицей, а не весь текст подряд
            bloki = re.findall(r'<(h2|h3|h4|p|strong|div)\b[^>]*>(.*?)</\1>',
                               k, re.S)
            t = ''
            for _, b in bloki:
                tt = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', b)).strip()
                if tt:
                    t = tt
            if not t:
                t = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', k)).strip()
            if t:
                tek_tekst = t[-160:]
    return zagolovok(h), chasti


def main():
    urls = posty()
    print(f'найдено записей: {len(urls)}')
    vse = []
    for u in urls:
        z, ch = razobrat_post(u)
        kol = sum(len(c['komplekty']) for c in ch)
        print(f'  {kol:3} компл.  {z[:70]}')
        if ch:
            vse.append({'zag': z, 'url': u, 'chasti': ch})
        time.sleep(0.3)
    put = os.path.join(ROOT, 'Временные', 'vpr_matematika7.json')
    with open(put, 'w', encoding='utf-8') as f:
        json.dump(vse, f, ensure_ascii=False, indent=1)
    print(f'-> {os.path.relpath(put, ROOT)}  записей: {len(vse)}')


if __name__ == '__main__':
    main()
