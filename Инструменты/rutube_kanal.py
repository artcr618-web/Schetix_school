# -*- coding: utf-8 -*-
"""Вытягивает все видео с канала Rutube.

    python3 Инструменты/rutube_kanal.py 37297900
    python3 Инструменты/rutube_kanal.py 37297900 --iskat "древн|египет|греци|рим"

Работает через endpoint канала, по 20 видео на страницу:

    /api/channel/<id>/            — то же, что /api/video/person/<id>/

Почему не через плейлисты: на канале могут лежать видео, не разложенные
ни по одному плейлисту. Смотреть надо всё подряд.

Без --iskat печатает просто список всех видео (на канале Мединского их
несколько сотен, поэтому обычно нужен --iskat). Поиск идёт по названию
без учёта регистра, регулярные выражения разрешены.
"""
import io, json, os, re, subprocess, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _пути import VREM

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/126.0 Safari/537.36')


def get(url):
    r = subprocess.run(['curl', '-s', '-L', '--max-time', '30', '-A', UA, url],
                       capture_output=True, text=True)
    return r.stdout


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not args:
        print(__doc__)
        return 1
    cid = args[0]

    iskat = None
    for a in sys.argv[1:]:
        if a.startswith('--iskat'):
            iskat = a.split('=', 1)[1] if '=' in a else None
        elif iskat is None and a.startswith('"') is False and '--' not in a and a != cid:
            iskat = a
    # проще: всё после --iskat считаем выражением
    if '--iskat' in sys.argv:
        k = sys.argv.index('--iskat')
        iskat = sys.argv[k + 1] if len(sys.argv) > k + 1 else None
    elif len(sys.argv) > 2:
        iskat = sys.argv[2]

    items, page = [], 1
    while page <= 40:
        raw = get(f'https://rutube.ru/api/channel/{cid}/?page={page}')
        try:
            d = json.loads(raw)
        except Exception:
            print(f'страница {page}: не разобралось, стоп')
            break
        res = d.get('results') or []
        if not res:
            break
        items.extend(res)
        print(f'  страница {page}: +{len(res)}')
        if not d.get('has_next'):
            break
        page += 1
        time.sleep(0.2)

    out = [{'id': i.get('id'), 'title': i.get('title'), 'dur': i.get('duration'),
            'url': f"https://rutube.ru/video/{i.get('id')}/"} for i in items]

    os.makedirs(VREM, exist_ok=True)
    path = os.path.join(VREM, f'kanal_{cid}.json')
    io.open(path, 'w', encoding='utf-8').write(json.dumps(out, ensure_ascii=False, indent=1))
    print(f'\nВсего видео на канале: {len(out)}')
    print(f'Сохранено: {path}\n')

    if iskat:
        rx = re.compile(iskat, re.I)
        hits = [i for i in out if rx.search(i['title'] or '')]
        print(f'Совпадения по «{iskat}»: {len(hits)}\n')
        for i in hits:
            m = f"{i['dur'] // 60}:{i['dur'] % 60:02d}" if i['dur'] else '?'
            print(f"  {m:>7}  {i['title']}")
            print(f"          {i['url']}")
        return 0

    for i in out:
        m = f"{i['dur'] // 60}:{i['dur'] % 60:02d}" if i['dur'] else '?'
        print(f"  {m:>7}  {i['title']}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
