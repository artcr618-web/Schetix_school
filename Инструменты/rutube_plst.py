#!/usr/bin/env python3
"""Скачивает плейлист Rutube целиком (все страницы) в JSON.

    python3 Инструменты/rutube_plst.py <id> [<id> ...]

Кладёт результат в Временные/rutube/plst_<id>.json.
Важно: нужен заголовок User-Agent, иначе Rutube отвечает 403.
"""
import json
import os
import subprocess
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
KUDA = os.path.join(ROOT, 'Временные', 'rutube')
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36'


def skachat(url):
    p = subprocess.run(['curl', '-sS', '-m', '40', '-A', UA, url],
                       capture_output=True)
    return p.stdout.decode('utf-8', 'replace')


def plenist(pid):
    vse = []
    stranica = 1
    while True:
        url = f'https://rutube.ru/api/playlist/custom/{pid}/videos/?page={stranica}'
        txt = skachat(url)
        try:
            d = json.loads(txt)
        except Exception as e:
            print(f'  ! страница {stranica}: не JSON ({e}) -> {txt[:120]!r}')
            break
        if 'results' not in d:
            print(f'  ! страница {stranica}: {str(d)[:160]}')
            break
        for v in d['results']:
            vse.append({
                'id': v.get('id'),
                'title': (v.get('title') or '').strip(),
                'url': v.get('video_url'),
                'duration': v.get('duration'),
                'published': (v.get('publication_ts') or '')[:10],
                'hits': v.get('hits'),
            })
        if not d.get('has_next') and not d.get('next'):
            break
        stranica += 1
        time.sleep(0.4)
        if stranica > 40:
            break
    return vse


def main():
    os.makedirs(KUDA, exist_ok=True)
    for pid in sys.argv[1:]:
        vse = plenist(pid)
        put = os.path.join(KUDA, f'plst_{pid}.json')
        with open(put, 'w', encoding='utf-8') as f:
            json.dump(vse, f, ensure_ascii=False, indent=1)
        print(f'plst/{pid}: {len(vse)} видео -> {os.path.relpath(put, ROOT)}')


if __name__ == '__main__':
    main()
