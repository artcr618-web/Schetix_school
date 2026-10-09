# -*- coding: utf-8 -*-
"""Коллаж «до/после» для панели плейлиста.

Собирает пары снимков из Временные/снимки (их снимает
Временные/снимок_панели.js: страница видеоуроков с открытой панелью и
одним играющим уроком — до правки и после) в одну картинку: слева «до»,
справа «после», и так по строке на каждое окно. Нужен, чтобы одним
взглядом видеть: у обычных пунктов больше нет плашек, а у играющего
отметка осталась.

Запуск: python3 Временные/коллаж_панели.py
"""
import os

from PIL import Image, ImageDraw, ImageFont

SHDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'снимки')
SHIRINA = 640          # ширина каждой картинки в коллаже
OTSTUP = 12
POLOSA = 58
FON = (14, 17, 22)
TEKST = (243, 245, 249)
TUSKLY = (152, 162, 179)

# Строка коллажа: (подпись, ширина окна)
RYADY = [
    ('Панель плейлиста · окно 1600, играет третий урок', 1600),
    ('Панель плейлиста · окно 800: панель во всю ширину', 800),
]


def shrift(razmer, zh=0):
    put = ('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if zh else
           '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
    return ImageFont.truetype(put, razmer)


def umenshit(im):
    v = round(im.height * SHIRINA / im.width)
    return im.resize((SHIRINA, v), Image.LANCZOS)


def main():
    kolonki = []
    for _, w in RYADY:
        para = []
        for kogda in ('до', 'после'):
            f = os.path.join(SHDIR, f'панель-{w}-{kogda}.png')
            para.append(umenshit(Image.open(f).convert('RGB')))
        kolonki.append(para)

    vysota = sum(max(a.height, b.height) + OTSTUP * 3 + 54
                 for a, b in kolonki) + OTSTUP
    shirina = SHIRINA * 2 + OTSTUP * 3
    karta = Image.new('RGB', (shirina, vysota + POLOSA), FON)
    ris = ImageDraw.Draw(karta)
    ris.text((OTSTUP * 2, 12),
             'Панель плейлиста: плашка только у играющего пункта, '
             'у остальных — ничего',
             font=shrift(20, 1), fill=TEKST)

    y = POLOSA
    for (podpis, _), (do, posle) in zip(RYADY, kolonki):
        ris.text((OTSTUP, y), podpis, font=shrift(19, 1), fill=TEKST)
        y += 30
        ris.text((OTSTUP, y), 'до', font=shrift(18, 1), fill=TUSKLY)
        ris.text((SHIRINA + OTSTUP * 2, y), 'после',
                 font=shrift(18, 1), fill=(255, 210, 63))
        y += 24
        karta.paste(do, (OTSTUP, y))
        karta.paste(posle, (SHIRINA + OTSTUP * 2, y))
        y += max(do.height, posle.height) + OTSTUP * 2

    kuda = os.path.join(SHDIR, 'панель-плейлиста-сравнение.png')
    karta.save(kuda)
    print('готово:', kuda, karta.size)


if __name__ == '__main__':
    main()
