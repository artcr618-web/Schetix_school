# -*- coding: utf-8 -*-
"""Общие пути. Подключается из всех скриптов папки Инструменты.

    from _пути import *        # если запускать из папки Инструменты
"""
import glob
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # /home/user

VREM = os.path.join(ROOT, 'Временные')          # рабочие данные
INSTR = os.path.join(ROOT, 'Инструменты')        # скрипты

ARH = os.path.join(ROOT, 'Архив')
"""Подробные страницы-исходники: их читают и печатают, но на флешку
не кладут. Исходник для каждой страницы пакета «Проект»."""

STRAN = {
    '5ист': os.path.join(ARH, '5 класс', 'История'),
    '5гео': os.path.join(ARH, '5 класс', 'География'),
    '7ист': os.path.join(ARH, '7 класс', 'История'),
    '7анг': os.path.join(ARH, '7 класс', 'Английский'),
    '7алг': os.path.join(ARH, '7 класс', 'Алгебра'),
    '8алг': os.path.join(ARH, '8 класс', 'Алгебра'),
    '8гео': os.path.join(ARH, '8 класс', 'Геометрия'),
}

CSS_ISTOCHNIK = os.path.join(STRAN['5ист'], 'istoriya-5-klass-sborniki-vpr.html')
"""Откуда берётся оформление. Стили лежат внутри этой страницы;
остальные страницы переиспользуют их, поэтому внешнего вида не нужно
держать в семи местах."""

# Все HTML-страницы проекта — их проверяют proverka_html.py и proverka_ssylok.py
VSE_STRANICY = [
    os.path.join(STRAN['5ист'], 'istoriya-5-klass-video.html'),
    os.path.join(STRAN['5ист'], 'kino-5-klass-istoriya.html'),
    os.path.join(STRAN['5ист'], 'istoriya-5-klass-sborniki-vpr.html'),
    os.path.join(STRAN['5ист'], 'istoriya-5-klass-trenazhery.html'),
    os.path.join(STRAN['5гео'], 'geografiya-5-klass-video.html'),
    os.path.join(STRAN['7ист'], 'istoriya-7-klass-video.html'),
    os.path.join(STRAN['7ист'], 'kino-7-klass-istoriya.html'),
    os.path.join(STRAN['7ист'], 'kontrolnye-7-klass-istoriya.html'),
    os.path.join(STRAN['7ист'], 'sborniki-i-vpr-7-klass-istoriya.html'),
    os.path.join(STRAN['7ист'], 'trenazhery-7-klass-istoriya.html'),
    os.path.join(STRAN['7анг'], 'trenazhery-7-klass-angliyskiy.html'),
    os.path.join(STRAN['7алг'], 'algebra-7-klass-video.html'),
    os.path.join(STRAN['7алг'], 'algebra-7-klass-trenazhery.html'),
    os.path.join(STRAN['7алг'], 'algebra-7-klass-kontrolnye.html'),
    os.path.join(STRAN['7алг'], 'algebra-7-klass-vpr-i-sborniki.html'),
    os.path.join(STRAN['8алг'], 'algebra-8-klass-video.html'),
    os.path.join(STRAN['8алг'], 'algebra-8-klass-trenazhery.html'),
    os.path.join(STRAN['8алг'], 'algebra-8-klass-kontrolnye.html'),
    os.path.join(STRAN['8алг'], 'algebra-8-klass-vpr-i-sborniki.html'),
    os.path.join(STRAN['8гео'], 'geometriya-8-klass-video.html'),
    os.path.join(STRAN['8гео'], 'geometriya-8-klass-trenazhery.html'),
    os.path.join(STRAN['8гео'], 'geometriya-8-klass-kontrolnye.html'),
    os.path.join(STRAN['8гео'], 'geometriya-8-klass-itogovye-i-sborniki.html'),
]

# Пакет «Проект» берётся списком, а не перечислением: файлы там лежат
# по папкам (класс -> предмет) и меняются, проверка не должна
# из-за этого ломаться. Обход рекурсивный.
PROEKT = os.path.join(ROOT, 'Проект')

for _put, _papki, _fayly in os.walk(PROEKT):
    for _f in _fayly:
        if _f.endswith('.html'):
            VSE_STRANICY.append(os.path.join(_put, _f))
VSE_STRANICY = sorted(set(VSE_STRANICY))

PLAYLISTS = {
    # ключ            id        что это
    'geliossar':  1195208,   # весь учебник вслух, все классы 5—11
    'gdz':        1481100,   # короткие пересказы по параграфам, 5 класс
    'vigasin':     63545,    # старый курс по учебнику Вигасина
    'sov':        324601,    # советские научные фильмы «История. Древний мир»
    'egypt_zdf':  914362,    # ZDF «Древний Египет: Хроники империи»
    'bbc_rome':   851600,    # BBC «Древний Рим: Расцвет и падение империи»
    'myths_gr':   856545,    # «Мифы Древней Греции», 40 серий
    'rome_super': 898267,    # «Рим: Первая сверхдержава»
    'dt_greece':  153187,    # Discovery Tour — Древняя Греция, видеоэкскурсии
    'docs_hist':  565327,    # «Расцвет древних цивилизаций» и прочее
    'films_rome': 836981,    # полнометражные фильмы о Риме
}

CSS_DOP = """
  nav{background:#efeae1;border-bottom:1px solid var(--line)}
  nav .inner{max-width:960px;margin:0 auto;padding:9px 22px;display:flex;
    flex-wrap:wrap;gap:6px 18px}
  nav a{font-family:system-ui,sans-serif;font-size:13.5px;color:#4a3f30;
    text-decoration:none;border-bottom:1px dotted #b3a894}
  nav a:hover{color:var(--accent);border-bottom-color:var(--accent)}
  .lead{background:#fff;border:1px solid var(--line);
    border-left:4px solid var(--accent);border-radius:8px;
    padding:14px 18px;margin:16px 0;font-size:16px;line-height:1.5}
  .grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:18px 0}
  .card{background:#fff;border:1px solid var(--line);border-radius:8px;
    padding:16px 18px}
  .tag.main{background:#efe4d6;color:#6b4a22;border-color:#d9c3a3}
  .card h3{margin-top:8px}
  .card p{margin:6px 0 0;font-size:14.5px}
  @media(max-width:720px){.grid{grid-template-columns:1fr}}
  .btnrow{display:flex;flex-wrap:wrap;gap:6px;margin:0}
  .btn{display:inline-block;font-family:system-ui,sans-serif;font-size:13px;
    line-height:1.25;text-decoration:none;color:#1a4f7a;background:#f3f6f9;
    border:1px solid #b9cddd;border-radius:6px;padding:4px 9px;white-space:nowrap}
  .btn:hover{background:#e4edf5;border-color:#7fa6c4}
  .btn .vremya{opacity:.75;font-size:12px;margin-left:5px;color:var(--muted)}
  .kids{background:#f2f6f2;border:1px solid #bcd3c4;border-radius:8px;
    padding:14px 18px;margin:16px 0;font-family:system-ui,sans-serif;
    font-size:14.5px;line-height:1.6}
  .small{font-size:13.5px;color:var(--muted);font-family:system-ui,sans-serif}
  tr.chapter td{background:#efeae1;font-weight:600;text-align:center}
  .net{color:#8a7a63;font-size:13px}
  .pills{display:flex;flex-wrap:wrap;gap:5px;margin:14px 0}
  .pill{display:inline-block;font-family:system-ui,sans-serif;font-size:12.5px;
    text-decoration:none;color:#1a4f7a;background:#fff;
    border:1px solid var(--line);border-radius:5px;padding:3px 7px}
  .pill:hover{background:#eef2f6;border-color:#b9cddd}
  @media print{
    nav{display:none}
    .btn,.pill{color:#000;border:none;background:none;text-decoration:underline}
  }
"""
"""Дополнительные стили для страниц математики: кнопки-ссылки,
карточки, верхняя навигация. Базовый CSS лежит в CSS_ISTOCHNIK,
этот кусок дописывается к нему."""

DATA_PLAYLISTS = os.path.join(VREM, 'playlists.json')
DATA_PARAGRAFY = os.path.join(VREM, 'paragrafy.json')
DATA_GEO_VIDEO = os.path.join(VREM, 'geografia_video.json')
LOG_SSYLKI = os.path.join(VREM, 'proverka_ssylok.log')
