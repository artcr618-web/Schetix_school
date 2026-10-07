# -*- coding: utf-8 -*-
"""Версия для телевизора: «География, 5 класс».

    python3 Инструменты/gen_tv_geografiya_5klass.py

Страница одна: уроки по параграфам и тематические видео — вместе.
Ребёнок не должен думать, куда идти за фильмом про путешествие:
он открывает география и видит все подборки в одном списке.

Данные лежат в двух файлах:

* «Временные/geografia_video.json» — уроки по параграфам (§ 1…§ 34);
* «Временные/geografia_temy.json» — тематические подборки: фильмы,
  мультфильмы, документальное кино. Каждая подборка — отдельный
  плейлист со своим названием.

Куда писать, говорит gen_tv_paket.py: он же знает, как раскладываются
папки.
"""
import io
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _пути import DATA_GEO_VIDEO
import _tv

ZAGOLOVOK = 'География, 5 класс'
POD = 'Учебник Климановой, «Землеведение» · уроки года'
"""Подзаголовок страницы видеоуроков. Фильмы и мультфильмы о
путешествиях стоят теперь на странице «Кино и документалистика»:
у них своя подборка, а тут остаются только уроки года."""

# Тематические подборки (фильмы и мультфильмы о путешествиях) больше не
# читаются здесь: у них своя страница «Кино и документалистика», и данные
# для неё собирает «Временные/kino_sborka.py» в «Временные/kino_geografiya_5.json».

# Уроки сгруппированы так, как их проходят в школе, а не подряд по учебнику.
BLOKI = [
    (1, 9, 'История географических открытий'),
    (10, 20, 'План местности и географическая карта'),
    (21, 25, 'Земля — планета Солнечной системы'),
    (26, 34, 'Литосфера и рельеф Земли'),
]


def main(fayl, put, menyu_spisok=None, menyu_zagolovok='', kniga=None,
         klassy=None):
    """Собрать страницу. `fayl` и `put` — пути от корня пакета.

    `kniga` — готовая полоса учебника (её собирает gen_tv_paket: она
    одна и та же на всех страницах предмета).
    """
    R = json.load(io.open(DATA_GEO_VIDEO, encoding='utf-8'))

    kurs = {v['n']: v for v in R['курс']}
    for v in R.get('доп', []):
        kurs.setdefault(v['n'], v)

    zagolovok_bloka = {a: t for a, b, t in BLOKI}
    bloki = []
    ryady = []
    for u in R['уроки']:
        if u['n'] in zagolovok_bloka:
            bloki.append(f'<h2>{zagolovok_bloka[u["n"]]}</h2>')

        ps = [x.strip() for x in str(u['par']).split(',') if x.strip()]
        prim = (f'<span class="primech">{_tv.myagkie(u["note"])}</span>'
                if u.get('note') else '')
        # Каждый параграф — свой пункт плейлиста: номер совпадает
        # с номером параграфа, видео открывается в плеере.
        for p in ps:
            n = int(p)
            if n not in kurs:
                raise SystemExit(f'В данных нет § {n}, а урок {u["n"]} на него ссылается')
            v = kurs[n]
            ryady.append((f'§ {n}', u['tema'],
                          f'https://rutube.ru/video/{v["id"]}/'))

    # На странице одни уроки: тематические подборки переехали на
    # страницу кино, чтобы ребёнок не искал фильмы среди параграфов.
    nabor = [('По параграфам', ryady)]
    blok_pleera, panel_pleylista = _tv.blok_playera(nabor)
    bloki = [blok_pleera]
    put_fayla, razmer = _tv.sobrat(ZAGOLOVOK, POD, bloki, fayl,
                                   put=put, indeks=True,
                                   menyu_spisok=menyu_spisok,
                                   menyu_zagolovok=menyu_zagolovok,
                                   kniga=kniga, klassy=klassy,
                                   telo_klass='pleylist-otkryto',
                                   paneli=panel_pleylista)
    print(f'  {fayl:<46} {len(ryady):>3} параграфов, {razmer:>6} байт')


if __name__ == '__main__':
    raise SystemExit('Эту страницу собирает gen_tv_paket.py — он знает пути.')
