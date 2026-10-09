#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Собирает «Даты» и «Определения» для тренажёра по истории, 7 класс.

Берёт два учебника (PDF в «Временные/учебники») и забирает из них ровно
то, что нужно: разделы в конце книги — «Основные события…» и «Словарь
понятий и терминов». Весь учебник не листается: пользователь просил
именно концевые списки.

Куда пишет:
  Проект/База данных/Тренажёры/История, 7 класс/Даты.json
  Проект/База данных/Тренажёры/История, 7 класс/Определения.json

Запуск:  python3 Временные/собрать_даты_и_определения.py
Требует PyMuPDF (pip install PyMuPDF) — как и другие разборы PDF.
"""
import json
import os
import re

import pymupdf

KOREN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UCH = os.path.join(KOREN, 'Временные', 'учебники')
KUDА = os.path.join(KOREN, 'Проект', 'База данных', 'Тренажёры',
                    'История, 7 класс')

KNIGI = (
    # файл, короткое имя, страницы дат, страницы определений
    ('istoriya-rossii-7.pdf', 'История России',
     (268, 269), range(263, 268),
     'История. История России. XVI—XVII вв. 7 класс — '
     'Мединский В. Р., Торкунов А. В.'),
    ('vseobshchaya-7.pdf', 'Всеобщая история',
     (234, 235), range(225, 234),
     'История. Всеобщая история. История Нового времени. '
     'Конец XV—XVII в. 7 класс — Мединский В. Р., Чубарьян А. О.'),
)

# «Чужие» строки: заголовки, колонтитулы и начало других разделов. На них
# статья закрывается — иначе к последней дате прилипает «ИНТЕРНЕТ-РЕСУРСЫ»
# и всё, что за ним, а к последнему термину — «Основные события…».
NADVIG = re.compile(r'^(ОСНОВНЫЕ СОБЫТИЯ|Основные события|'
                    r'СЛОВАРЬ ПОНЯТИЙ|Словарь понятий|'
                    r'ИНТЕРНЕТ-РЕСУРСЫ|Интернет-ресурсы|'
                    r'ОГЛАВЛЕНИЕ|ЗАКЛЮЧЕНИЕ|Заключение|'
                    r'Итоги главы|Рекомендуем посетить|'
                    r'Учебное издание|Подписано в печать|Для заметок)')
GOD = re.compile(r'^(?P<kogda>\d{4}(?:\s*—\s*\d{4})?)\s*гг?\.\s*—\s*(?P<chto>.+)$')


def skleit(tekst):
    """Склейка строк и переносов: «мо-\nнарх» → «монарх»."""
    t = tekst.replace('\xad', '').replace('\xa0', ' ')
    t = re.sub(r'-\s*\n\s*', '', t)
    t = re.sub(r'\s*\n\s*', ' ', t)
    return re.sub(r'\s+', ' ', t).strip()


def stroki(f, stranicy):
    """Строки страниц: (страница, отступ слева, шрифт, текст)."""
    d = pymupdf.open(os.path.join(UCH, f))
    for p in stranicy:
        for b in d[p - 1].get_text('dict')['blocks']:
            if b.get('type', 0) != 0:
                continue
            for l in b.get('lines', []):
                sp = [s for s in l['spans'] if s['text'].strip()]
                if not sp:
                    continue
                yield (p, round(sp[0]['bbox'][0], 1), sp[0]['font'],
                       ''.join(s['text'] for s in l['spans']))


def daty(f, stranicy):
    """Список «год(ы) — что произошло» со страниц с датами."""
    zap, tek = [], None
    for (p, x, sh, t) in stroki(f, stranicy):
        t = t.strip()
        if not t or re.fullmatch(r'\d{1,3}', t):
            continue
        if NADVIG.match(t):
            if tek:
                zap.append(tek)
                tek = None
            continue
        m = GOD.match(t)
        if m:
            if tek:
                zap.append(tek)
            tek = [p, m.group('kogda'), m.group('chto')]
        elif tek:
            tek[2] += '\n' + t
    if tek:
        zap.append(tek)
    return [(p, re.sub(r'\s*—\s*', '—', k), skleit(s)) for (p, k, s) in zap]


def opredeleniya(f, stranicy):
    """Список «термин — значение» со страниц словаря."""
    zap, tek = [], None
    for (p, x, sh, t) in stroki(f, stranicy):
        t = t.strip()
        if not t or re.fullmatch(r'\d{1,3}', t):
            continue
        if NADVIG.match(t):
            if tek:
                zap.append(tek)
                tek = None
            continue
        if x > 45.0 and 'Italic' in sh:      # новая словарная статья
            if tek:
                zap.append(tek)
            tek = [p, t]
        elif tek is not None:
            tek[1] += '\n' + t
    if tek:
        zap.append(tek)
    itog = []
    for (p, t) in zap:
        t = re.sub(r'\s*—\s*', ' — ', skleit(t))
        slovo, _, znach = t.partition(' — ')
        # «Парсуна (от лат. «персона» — личность, особа) — ранний жанр…»:
        # дефис внутри скобки разрывает статью — собираем её обратно.
        if slovo.count('(') > slovo.count(')'):
            k = t.find(') — ')
            if k > 0:
                slovo, znach = t[:k + 1], t[k + 4:]
                skobka = re.search(r'\(([^()]*)\)\s*$', slovo)
                if skobka:
                    slovo = slovo[:skobka.start()].strip()
                    znach = znach.rstrip('.') + ' (' + skobka.group(1) + ').'
        slovo, znach = slovo.strip(), znach.strip()
        if not slovo or not znach:
            raise SystemExit(f'Не разобралась статья на стр. {p}: {t[:80]}')
        itog.append((p, slovo, znach))
    return itog


def main():
    daty_vse, opred_vse, uchebniki = [], [], []
    for (f, imya, str_daty, str_opr, opisanie) in KNIGI:
        uchebniki.append(f'{opisanie} (стр. {str_daty[0]}—{str_daty[-1]}; '
                         f'словарь — стр. {str_opr[0]}—{str_opr[-1]})')
        d = daty(f, str_daty)
        o = opredeleniya(f, str_opr)
        print(f'{imya}: дат {len(d)}, определений {len(o)}')
        for (p, kogda, chto) in d:
            daty_vse.append({'когда': kogda, 'событие': chto,
                             'учебник': imya, 'страница': p})
        for (p, slovo, znach) in o:
            opred_vse.append({'термин': slovo, 'значение': znach,
                              'учебник': imya, 'страница': p})

    os.makedirs(KUDА, exist_ok=True)
    fayl_d = os.path.join(KUDА, 'Даты.json')
    fayl_o = os.path.join(KUDА, 'Определения.json')
    with open(fayl_d, 'w', encoding='utf-8') as fh:
        json.dump({
            'название': 'История, 7 класс — даты',
            'откуда': 'Раздел «Основные события» в конце каждого учебника',
            'учебники': uchebniki,
            'даты': daty_vse,
        }, fh, ensure_ascii=False, indent=1)
        fh.write('\n')
    with open(fayl_o, 'w', encoding='utf-8') as fh:
        json.dump({
            'название': 'История, 7 класс — определения',
            'откуда': 'Раздел «Словарь понятий и терминов» в конце '
                      'каждого учебника',
            'учебники': uchebniki,
            'определения': opred_vse,
        }, fh, ensure_ascii=False, indent=1)
        fh.write('\n')
    print(f'\nЗаписано:\n  {os.path.relpath(fayl_d, KOREN)} — {len(daty_vse)}\n'
          f'  {os.path.relpath(fayl_o, KOREN)} — {len(opred_vse)}')


if __name__ == '__main__':
    main()
