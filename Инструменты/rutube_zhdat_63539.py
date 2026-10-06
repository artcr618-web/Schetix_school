#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ждём, пока Rutube снимет WAF-блок (403 Access Blocked), и вытаскиваем
плейлист «География 5-6 классы, Полярная звезда» (канал «Учебник вслух»).

Блок IP-базированный: ставится на ~15-60 минут после серии массовых запросов.
Поэтому скрипт не падает, а терпеливо стучится раз в 45 секунд.

Запуск (в фоне, блок может провисеть полчаса):
    python3 Инструменты/rutube_zhdat_63539.py

Результат: Временные/geografia_63539.json
    {title, videos_count, items:[{id, title, duration}], ...}

Код возврата: 0 = добыл, 1 = так и не дождался.
"""
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

try:
    import _пути as P
    VREM = Path(P.VREM)
except Exception:
    VREM = Path('/home/user/Временные')

OUT = VREM / 'geografia_63539.json'
PL = 63539
POPYTKI = 40
PAUZA = 45

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36')


def get(url, tries=3):
    """Вернуть JSON. HTTPError(403) пробрасываем наверх — это признак блока."""
    for k in range(tries):
        req = urllib.request.Request(url, headers={
            'User-Agent': UA,
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'ru-RU,ru;q=0.9',
            'Referer': 'https://rutube.ru/plst/%d/' % PL,
        })
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                if r.status == 200:
                    return json.loads(r.read().decode('utf-8'))
                raise urllib.error.HTTPError(url, r.status, 'HTTP', r.headers, None)
        except urllib.error.HTTPError:
            if k == tries - 1:
                raise
        except Exception:
            if k == tries - 1:
                raise
        time.sleep(3)
    return None


def main():
    for n in range(1, POPYTKI + 1):
        try:
            meta = get('https://rutube.ru/api/playlist/custom/%d/' % PL)
        except urllib.error.HTTPError as e:
            if e.code == 403:
                print('попытка %d/%d: 403 — блок ещё висит, жду %d с' % (n, POPYTKI, PAUZA),
                      flush=True)
                time.sleep(PAUZA)
                continue
            print('попытка %d: неожиданный HTTP %s — сдаюсь' % (n, e.code), flush=True)
            return 1
        except Exception as e:
            print('попытка %d/%d: сеть %r — жду %d с' % (n, POPYTKI, e, PAUZA), flush=True)
            time.sleep(PAUZA)
            continue

        print('попытка %d: блок снят (%r), тащу видео' % (n, meta.get('title')), flush=True)
        items, page = [], 1
        while page <= 12:
            # Блок может вернуться в любой момент, в том числе между страницами.
            # Тогда ждём и спрашиваем эту страницу заново, а не падаем.
            pop = 0
            while True:
                try:
                    d = get('https://rutube.ru/api/playlist/custom/%d/videos/?page=%d'
                            % (PL, page))
                    break
                except urllib.error.HTTPError as e:
                    if e.code != 403 or pop >= 8:
                        raise
                    pop += 1
                    print('  страница %d: снова 403, жду %d с (попытка %d)'
                          % (page, PAUZA, pop), flush=True)
                    time.sleep(PAUZA)
            r = d.get('results') or []
            for v in r:
                items.append({'id': v['id'], 'title': v['title'],
                              'duration': v.get('duration')})
            print('  страница %d: +%d видео (всего %d)' % (page, len(r), len(items)), flush=True)
            if not d.get('next') or not r:
                break
            page += 1
            time.sleep(1)

        meta['items'] = items
        meta['_vsego_vytashcheno'] = len(items)
        VREM.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding='utf-8')
        print('ГОТОВО: %d видео -> %s' % (len(items), OUT), flush=True)
        return 0

    print('НЕ ДОЖДАЛСЯ: за %d попыток блок так и не сняли' % POPYTKI, flush=True)
    return 1


if __name__ == '__main__':
    sys.exit(main())
