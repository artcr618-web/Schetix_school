# -*- coding: utf-8 -*-
"""Собирает страницу «География, 5 класс — видео по параграфам».

    python3 Инструменты/gen_video_geografiya_5klass.py

Читает Временные/geografia_video.json (данные вынимаются из Rutube
скриптом rutube_zhdat_63539.py), оформление берёт из CSS_ISTOCHNIK,
пишет «5 класс/География/geografiya-5-klass-video.html».

Никаких ссылок и длительностей в коде нет: всё приходит из JSON.
Если в данных нет какого-то параграфа — скрипт упадёт, а не нарисует
страницу с дыркой.
"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _пути import DATA_GEO_VIDEO, CSS_ISTOCHNIK, STRAN

OUT = os.path.join(STRAN['5гео'], 'geografiya-5-klass-video.html')

# Разделы в том порядке, как они идут в видеокурсе (а не в школьном плане —
# школа проходит их в другом порядке, это видно по колонке «уроки»).
RAZDELY = [
    (1, 7, 'Географическое изучение Земли', 'уроки 1—9'),
    (8, 11, 'Земля — планета Солнечной системы', 'уроки 21—25'),
    (12, 20, 'Изображения земной поверхности', 'уроки 10—20'),
    (21, 28, 'Литосфера и рельеф', 'уроки 26—34'),
]


def mm(s):
    s = int(s)
    return f'{s // 60}:{s % 60:02d}'


def video_url(v):
    return f'https://rutube.ru/video/{v["id"]}/'


def main():
    R = json.load(io.open(DATA_GEO_VIDEO, encoding='utf-8'))
    CSS = io.open(CSS_ISTOCHNIK, encoding='utf-8').read().split('<style>')[1].split('</style>')[0]

    kurs = R['курс']
    uroki = R['уроки']
    src = R['источник']

    # номер параграфа -> сам ролик (курс + extras из шестиклассной части)
    byn = {v['n']: v for v in kurs}
    for v in R.get('доп', []):
        byn.setdefault(v['n'], v)

    # обратный указатель: параграф -> номера уроков, на которых он нужен
    rev = {}
    for u in uroki:
        for p in [x.strip() for x in str(u['par']).split(',') if x.strip()]:
            rev.setdefault(int(p), []).append(u['n'])

    # ---- таблица «видео по параграфам» ----
    nachalo = {a: (t, u) for a, b, t, u in RAZDELY}
    tr = []
    for v in kurs:
        if v['n'] in nachalo:
            t, u = nachalo[v['n']]
            tr.append(f'<tr class="chapter"><td colspan="4">{t} · {u}</td></tr>')
        uu = rev.get(v['n'], [])
        col_u = ', '.join(str(x) for x in uu) if uu else '—'
        tr.append(f'<tr><td class="n">§ {v["n"]}</td><td>{v["t"]}</td>'
                  f'<td class="c">{col_u}</td>'
                  f'<td class="c"><a href="{video_url(v)}">{mm(v["d"])}</a></td></tr>')
    KURS = '\n'.join(tr)

    # ---- таблица «что смотреть на каком уроке» ----
    tr = []
    for u in uroki:
        ps = [x.strip() for x in str(u['par']).split(',') if x.strip()]
        if ps:
            links = []
            for p in ps:
                n = int(p)
                if n not in byn:
                    raise SystemExit(f'В данных нет § {n}, а на урок {u["n"]} он сослан')
                links.append(f'<a href="{video_url(byn[n])}">§ {n}</a>')
            col = ', '.join(links)
        else:
            col = '—'
        note = f'<span class="note">{u["note"]}</span>' if u.get('note') else ''
        tr.append(f'<tr><td class="n">{u["n"]}</td><td>{u["tema"]}{note}</td>'
                  f'<td class="c">{col}</td></tr>')
    UROKI = '\n'.join(tr)

    # ---- таблица «что проходят» ----
    tr = []
    for a, b, t, u in RAZDELY:
        tr.append(f'<tr><td class="big">{t}</td><td>§ {a}—{b}</td><td>{u}</td></tr>')
    CHTO = '\n'.join(tr)

    total = sum(v['d'] for v in kurs)

    body = f"""
<div class="ok">
<strong>Коротко.</strong> Учебник географии один сразу на 5 и 6 класс, и по нему
есть <strong>полный видеокурс — все параграфы подряд, озвучены и разобраны</strong>.
На долю 5 класса приходится <strong>{len(kurs)} параграфов</strong>
(общее время {total // 3600} ч {(total % 3600) // 60} мин) — ровно до темы
«Литосфера и человек», которой пятой классная программа и заканчивается.
Ниже — эти ролики, и отдельная таблица: что включить перед конкретным уроком.
</div>

<h2 id="what">1. Что именно проходят в 5 классе</h2>

<div class="work">
<p><strong>Учебник.</strong> Алексеев А. И., Николина В. В., Липкина Е. К.
«География. 5—6 классы», 12-е издание, переработанное. Издательство «Просвещение»,
линия «Полярная звезда». Одна и та же книга на два года.</p>

<p><strong>Объём.</strong> По рабочей программе школы — <strong>1 час в неделю,
34 часа за год</strong>: 3 контрольные работы и 5 практических.
Всероссийская проверочная работа стоит в плане на уроках 30—31,
то есть в конце темы «Литосфера».</p>

<p><strong>Порядок важнее номера.</strong> Школа идёт не подряд по учебнику:
сначала история открытий, затем планы и карты, потом Земля как планета
и в конце — литосфера с рельефом. Поэтому в таблице ниже у каждого
параграфа указано, к какому уроку он относится.</p>

<table>
<tr><th>Раздел</th><th>Параграфы</th><th>Когда проходят</th></tr>
{CHTO}
</table>
</div>

<h2 id="kurs">2. Видео по параграфам</h2>

<p>Курс читает канал «Учебник вслух». Нажимайте на время — откроется ролик.
Колонка «уроки» показывает, когда этот параграф пригодится по школьному плану.</p>

<table class="plan">
<tr><th>§</th><th>Тема</th><th>Уроки</th><th>Смотреть</th></tr>
{KURS}
</table>

<p class="tt">Кроме этих {len(kurs)} параграфов в плейлисте есть ещё ролики —
гидросфера, атмосфера, биосфера. Это программа 6 класса, поэтому сюда они
не вынесены. Полный список — <a href="{src["плейлист"]}">в плейлисте на Rutube</a>.</p>

<h2 id="uroki">3. Что смотреть на каком уроке</h2>

<p>Обратный порядок: идёте по расписанию, находите номер урока — и сразу
видите, что включить накануне. Все 34 урока учебного года.</p>

<table class="plan">
<tr><th>Урок</th><th>Тема урока по школьному плану</th><th>Видео</th></tr>
{UROKI}
</table>

<h2 id="nomer">4. Про нумерацию параграфов</h2>

<div class="work">
<p>Номера параграфов в таблицах — по изданию, с которого снят видеокурс.
В более старых изданиях того же учебника нумерация другая: например,
«Градусная сетка» была § 13, а в переработанном издании стала § 17.
Поэтому <strong>ориентируйтесь на название темы</strong>, а не на номер —
названия совпадают во всех изданиях.</p>

<p>Две мелкие нестыковки, о которых стоит знать: в названии ролика про
земную кору опечатка канала («верхняя часть атмосферы» вместо «литосферы») —
по содержанию всё верно; а § 12 «Ориентирование на местности» канал снял
для другой линейки учебников и включил в этот курс — тема та же самая.</p>
</div>

<h2 id="links">5. Все ссылки</h2>

<div class="work">
<h4>Видеокурс</h4>
<ul>
<li><a href="{src["плейлист"]}">Плейлист «География 5-6 классы, Полярная звезда» —
{src["всего_видео"]} видео целиком</a></li>
<li><a href="{src["канал_url"]}">Канал «Учебник вслух» — плейлисты по разным учебникам</a></li>
</ul>
<h4>Соседние страницы</h4>
<ul>
<li><a href="../История/istoriya-5-klass-video.html">История, 5 класс — видео по параграфам</a></li>
<li><a href="../История/istoriya-5-klass-sborniki-vpr.html">История, 5 класс — сборники и ВПР</a></li>
<li><a href="../История/kino-5-klass-istoriya.html">История, 5 класс — кино и документалистика</a></li>
</ul>
</div>
"""

    extra_css = """
  table.plan td.n{text-align:center;font-family:system-ui,sans-serif;color:#6a6355;width:52px}
  table.plan td.c{text-align:center;font-family:system-ui,sans-serif;white-space:nowrap}
  table.plan tr.chapter td{background:#2b2620;color:#f5f1e8;font-family:system-ui,sans-serif;
    font-size:14px;font-weight:600;letter-spacing:.02em}
  table.plan td a{white-space:nowrap}
  span.note{display:block;margin-top:2px;font-size:13px;color:#6a6355;font-style:italic}
"""

    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>География, 5 класс — видео по параграфам учебника Алексеева</title>
<style>{CSS}{extra_css}</style>
</head>
<body>
<header><div class="inner">
  <h1>География, 5 класс: видео по параграфам</h1>
  <p>Учебник Алексеева, линия «Полярная звезда» · полный курс по всем
  {len(kurs)} параграфам 5 класса · что включить перед каждым уроком.
  Ссылки проверены 5 октября 2026 г.</p>
</div></header>
<div class="wrap">
{body}
<p class="tt">Ссылки проверены 5 октября 2026 г. Что-то перестало работать — напишите, найду замену.</p>
</div>
</body>
</html>
"""
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    io.open(OUT, 'w', encoding='utf-8').write(html)
    print(f'Готово: {OUT} ({len(html)} байт)')


if __name__ == '__main__':
    main()
