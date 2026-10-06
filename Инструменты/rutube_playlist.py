# -*- coding: utf-8 -*-
"""Шаг 1. Вытаскивает видео из плейлистов Rutube через их открытый API.

    python3 Инструменты/rutube_playlist.py

Пишет Временные/playlists.json: название плейлиста, число видео,
и по каждому видео — id, название, длительность, ссылка.

Почему не парсим страницу: rutube.ru отдаёт страницы скриптами,
в HTML нет ни названий, ни ссылок. А API отдаёт всё чисто:

    /api/playlist/custom/<id>/            — описание плейлиста
    /api/playlist/custom/<id>/videos/     — видео, по 20 на страницу
    /api/video/<id>/                      — одно видео (название, автор)

Известная особенность: /api/search/... отдаёт 0 результатов без авторизации,
поэтому искать по Rutube этим способом нельзя — только по известным id.
"""
import io, json, os, subprocess, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _пути import PLAYLISTS, DATA_PLAYLISTS, VREM

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/126.0 Safari/537.36')


def get(url):
    r = subprocess.run(['curl', '-s', '-L', '--max-time', '30', '-A', UA, url],
                       capture_output=True, text=True)
    return r.stdout


def playlist(pid):
    """Все видео плейлиста, со всеми страницами."""
    items, page = [], 1
    while page <= 20:
        try:
            d = json.loads(get(
                f'https://rutube.ru/api/playlist/custom/{pid}/videos/?page={page}'))
        except Exception:
            break
        res = d.get('results') or []
        if not res:
            break
        items.extend(res)
        if not d.get('next'):
            break
        page += 1
    return items


def main():
    os.makedirs(VREM, exist_ok=True)
    out, problems = {}, []

    for key, pid in PLAYLISTS.items():
        items = playlist(pid)
        try:
            meta = json.loads(get(f'https://rutube.ru/api/playlist/custom/{pid}/'))
            title, declared = meta.get('title'), meta.get('videos_count')
        except Exception:
            title, declared = None, None

        out[key] = {
            'pid': pid,
            'title': title,
            'count': declared,
            'items': [{'id': i.get('id'),
                       'title': i.get('title'),
                       'dur': i.get('duration'),
                       'url': f"https://rutube.ru/video/{i.get('id')}/"} for i in items],
        }
        got = len(items)
        flag = '' if (declared is None or got >= declared) else '  <-- НЕСОВПАДЕНИЕ'
        print(f'{key:<11} [{pid:>7}]  заявлено {declared}, вытащено {got}{flag}')
        if flag:
            problems.append(key)
        time.sleep(0.2)

    io.open(DATA_PLAYLISTS, 'w', encoding='utf-8').write(
        json.dumps(out, ensure_ascii=False, indent=1))
    print(f'\nСохранено: {DATA_PLAYLISTS}')
    if problems:
        print('Внимание, проверить: ' + ', '.join(problems))


if __name__ == '__main__':
    main()
