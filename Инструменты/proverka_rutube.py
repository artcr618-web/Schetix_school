#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Терпеливая проверка ссылок на видео Rutube.

Rutube ставит WAF-блок (403 «Access Blocked») на серии частых запросов,
а потом рвёт TLS. Обычный обход ссылок в таких условиях бесполезен:
половина ответов — не про ссылку, а про блок.

Поэтому этот скрипт не «проверяет и падает», а ждёт: идёт по списку
невыясненных ссылок, между запросами держит паузу, и повторяет круги,
пока каждая ссылка не получит настоящий ответ.

    python3 -u Инструменты/proverka_rutube.py

Читает:  Временные/geografia_video.json
Пишет:   Временные/proverka_rutube.log
Возврат: 0 = все ссылки выяснены, 1 = остались непроверенные.

Коды: 200 — жива; 404/410 — удалена; 403/000/прочее — пока не выяснено.
"""
import io
import json
import os
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _пути import DATA_GEO_VIDEO, VREM

LOG = os.path.join(VREM, 'proverka_rutube.log')
KRUGOV = 6
PAUZA = 8

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36')

OK = {'200'}                      # точно жива
MRTVA = {'404', '410'}            # точно удалена


def sprosit(url):
    """Код ответа или '000' при сетевой ошибке. Тело не качаем."""
    req = urllib.request.Request(url, headers={
        'User-Agent': UA,
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'ru-RU,ru;q=0.9',
        'Range': 'bytes=0-0',
    })
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return str(r.status)
    except urllib.error.HTTPError as e:
        return str(e.code)
    except Exception:
        return '000'


def main():
    R = json.load(io.open(DATA_GEO_VIDEO, encoding='utf-8'))
    spis = [{'n': v['n'], 't': v['t'], 'id': v['id']}
            for v in R['курс'] + R.get('доп', [])]
    url = {v['n']: f'https://rutube.ru/video/{v["id"]}/' for v in spis}

    itog = {}
    for krug in range(1, KRUGOV + 1):
        zhdut = [v['n'] for v in spis if v['n'] not in itog]
        if not zhdut:
            break
        print(f'--- круг {krug}/{KRUGOV}, непроверенных: {len(zhdut)} ---', flush=True)
        for n in zhdut:
            k = sprosit(url[n])
            if k in OK or k in MRTVA or (k.startswith('5') and k.isdigit()):
                itog[n] = k
                print(f'  § {n:>2}: {k}', flush=True)
            else:
                print(f'  § {n:>2}: {k} (блок или сеть, попробую ещё)', flush=True)
            time.sleep(PAUZA)
        if len(itog) < len(spis):
            print('  круг кончился, передыхаю 60 с', flush=True)
            time.sleep(60)

    lines = ['# Проверка ссылок Rutube для страницы «География, 5 класс — видео»',
             '# 200 — жива; 404/410 — удалена; прочее — выяснить не удалось',
             '']
    zhiv = mert = neyas = 0
    for v in spis:
        k = itog.get(v['n'], '?')
        if k in OK:
            zhiv += 1
        elif k in MRTVA:
            mert += 1
        else:
            neyas += 1
        lines.append(f'§ {v["n"]:>2}  {k:<4} {v["t"]:<48} {url[v["n"]]}')
    lines += ['', f'Итого: живых {zhiv}, удалённых {mert}, не выяснено {neyas}']
    io.open(LOG, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
    print('\n'.join(lines[-3:]), flush=True)
    print(f'Лог: {LOG}', flush=True)
    return 0 if neyas == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
