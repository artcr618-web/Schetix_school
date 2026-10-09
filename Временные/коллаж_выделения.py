# -*- coding: utf-8 -*-
"""Коллаж «до/после»: выделение и отступы строк списков.

Собирает пары снимков из Временные/снимки (их снимает
Временные/снимок_выделения.js: «до» — из копии со старым css, «после» —
из собранного «Проекта») в одну картинку: слева «до», справа «после».
Нужен, чтобы одним взглядом видеть: строка стала ниже и компактнее,
номер прижат к левому краю, а выделение — рамка и флажок.

Запуск: python3 Временные/коллаж_выделения.py
"""
import os

from PIL import Image, ImageDraw, ImageFont

SHDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'снимки')
SHIRINA = 420          # ширина каждой картинки в коллаже
OTSTUP = 12
POLOSA = 58
FON = (14, 17, 22)
TEKST = (243, 245, 249)
TUSKLY = (152, 162, 179)

# Строка коллажа: (подпись, имя снимка)
RYADY = [
    ('Панель плейлиста (курсор на § 3)',
     'выделение-плейлист'),
    ('Боковое меню (курсор на «Алгебре»)',
     'выделение-меню'),
    ('Названия плейлистов под кадром',
     'выделение-под-кадром'),
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
             'Строки списков: меньше шрифт, ближе к краю, '
             'выделение — рамка с флажком',
             font=shrift(20, 1), fill=TEKST)

    y = POLOSA
    for (podpis, _), (do, posle) in zip(RYADY, kolonki):
        ris.text((OTSTUP, y), podpis, font=shrift(18, 1), fill=TEKST)
        y += 28
        ris.text((OTSTUP, y), 'до', font=shrift(17, 1), fill=TUSKLY)
        ris.text((SHIRINA + OTSTUP * 2, y), 'после',
                 font=shrift(17, 1), fill=(255, 210, 63))
        y += 22
        karta.paste(do, (OTSTUP, y))
        karta.paste(posle, (SHIRINA + OTSTUP * 2, y))
        y += max(do.height, posle.height) + OTSTUP * 2

    kuda = os.path.join(SHDIR, 'выделение-сравнение.png')
    karta.save(kuda)
    print('готово:', kuda, karta.size)


if __name__ == '__main__':
    main()
