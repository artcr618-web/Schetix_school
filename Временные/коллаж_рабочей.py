# -*- coding: utf-8 -*-
"""Коллаж «до/после» для рабочей ширины.

Собирает пары снимков из Временные/снимки (их снимает
Временные/snimki_rabochey.js: страница с ОТКРЫТЫМ меню — до правки и
после) в одну картинку: слева «до», справа «после», и так по строке на
каждое окно. Нужен, чтобы одним взглядом видеть, что меню больше не
сжимает плашки.

Запуск: python3 Временные/коллаж_рабочей.py
"""
import os

from PIL import Image, ImageDraw, ImageFont

SHDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'снимки')
SHIRINA = 620          # ширина каждой картинки в коллаже
OTSTUP = 12
POLOSA = 46            # полоса под подпись строки
FON = (14, 17, 22)
TEKST = (243, 245, 249)
TUSKLY = (152, 162, 179)

# Строка коллажа: (подпись строки, имя снимка)
RYADY = [
    ('Главная · окно 1600, меню открыто', 'рабочая-главная-1-широкий'),
    ('Главная · окно 1280, меню открыто', 'рабочая-главная-2-обычный'),
    ('Выбор предмета · окно 1100, меню открыто',
     'рабочая-предметы-3-планшет-гор'),
    ('Главная · окно 900, меню открыто: панель во всю ширину экрана',
     'рабочая-главная-4-планшет-верт'),
    ('География 5 класса · окно 640, меню открыто: заголовок больше не '
     'вылезает',
     'рабочая-география-4б-планшет-верт-узко'),
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
    for _, imya in RYADY:
        para = []
        for kogda in ('до', 'после'):
            f = os.path.join(SHDIR, f'{imya}-{kogda}.png')
            para.append(umenshit(Image.open(f).convert('RGB')))
        kolonki.append(para)

    vysota = sum(max(a.height, b.height) + OTSTUP * 3 + 54
                 for a, b in kolonki) + OTSTUP
    shirina = SHIRINA * 2 + OTSTUP * 3
    karta = Image.new('RGB', (shirina, vysota + POLOSA), FON)
    ris = ImageDraw.Draw(karta)
    ris.text((OTSTUP * 2, 12),
             'Открытое боковое меню: плашки считаются по рабочей ширине, '
             'а не по ширине окна',
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

    kuda = os.path.join(SHDIR, 'рабочая-ширина-сравнение.png')
    karta.save(kuda)
    print('готово:', kuda, karta.size)


if __name__ == '__main__':
    main()
