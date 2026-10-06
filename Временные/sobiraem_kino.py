# -*- coding: utf-8 -*-
"""Собирает данные для страниц «Кино и документалистика».

    python3 Временные/sobiraem_kino.py видео <id> [<id> ...]
    python3 Временные/sobiraem_kino.py плейлист <номер> [сколько]

Проверяет каждый ролик на Rutube: есть ли он, сколько идёт, какого
возраста и на каком канале. Для плейлиста достаёт из его страницы все
видео и проверяет их разом: плейлисты Rutube встроить нельзя, а
отдельные видео — можно.
"""
import io
import json
import re
import sys
import urllib.request

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/124 Safari/537.36')


def stranica(u):
    r = urllib.request.Request(u, headers={'User-Agent': UA,
                                           'Referer': 'https://rutube.ru/'})
    return urllib.request.urlopen(r, timeout=40).read().decode('utf-8', 'replace')


def api(u):
    r = urllib.request.Request(u + ('&' if '?' in u else '?') + 'format=json',
                               headers={'User-Agent': UA,
                                        'Referer': 'https://rutube.ru/',
                                        'Accept': 'application/json'})
    return json.load(urllib.request.urlopen(r, timeout=40))


def o_video(kod, korotko=True):
    try:
        d = api(f'https://rutube.ru/api/video/{kod}/')
    except Exception as e:
        return {'id': kod, 'беда': str(e)[:60]}
    avt = d.get('author') or {}
    vozrast = ((d.get('pg_rating') or {}).get('age')) or ''
    return {'id': kod, 'название': d.get('title') or '',
            'секунд': d.get('duration') or 0, 'возраст': vozrast,
            'канал': avt.get('name') or '', 'канал_id': avt.get('id'),
            'ссылка': f'https://rutube.ru/video/{kod}/'}


def iz_pleylista(nomer, skolko=None):
    h = stranica(f'https://rutube.ru/plst/{nomer}/')
    # в странице лежит готовый ответ getPlaylistVideos
    kusok = h[h.find('getPlaylistVideos'):]
    ids = list(dict.fromkeys(re.findall(r'"id"\s*:\s*"([0-9a-f]{32})"', kusok)))
    if skolko:
        ids = ids[:skolko]
    return ids


def pokazat(v):
    if 'беда' in v:
        print(f"   {v['id']}  НЕДОСТУПНО: {v['беда']}")
        return
    m, s = divmod(v['секунд'], 60)
    print(f"   {v['id']}  {m:>3}:{s:02d}  {v['возраст']:>3}  "
          f"{v['название'][:66]:<68} [{v['канал'][:26]}]")


if __name__ == '__main__':
    chto = sys.argv[1] if len(sys.argv) > 1 else 'видео'
    if chto == 'видео':
        for kod in sys.argv[2:]:
            pokazat(o_video(kod))
    elif chto == 'плейлист':
        nomer = sys.argv[2]
        skolko = int(sys.argv[3]) if len(sys.argv) > 3 else None
        ids = iz_pleylista(nomer, skolko)
        print(f'# плейлист {nomer}: видео {len(ids)}')
        for kod in ids:
            pokazat(o_video(kod))
