#!/usr/bin/env python3
"""Привязать вопросы тренажёра к параграфам учебников.

Зачем: в «Настройках» тренажёра выбирают параграф, который проходят
сейчас, и вопросы идут «с начала курса до этого параграфа». Значит,
у каждого вопроса должен быть свой параграф.

Откуда берём:

* **Даты.** В начале каждой главы обоих учебников стоит рамка «Россия /
  Мир» со списком дат этой главы. Первый столбец рамки в учебнике
  истории России — Россия, во всеобщей истории — Мир: это и есть наш
  предмет. Записи рамки сравниваем с датами из приложений по годам и
  словам события — так дата попадает в свою главу.
* **Определения.** Термин ищем в тексте учебника (без словаря в конце):
  первая страница, где он встретился, и есть глава, где его проходят.

Номер параграфа берём из шапки страницы: «§ 14–15». Список параграфов
учебника — по порядку страниц, это и есть порядок курса.

Результат — «Проект/База данных/Тренажёры/История, 7 класс/параграфы.json»:
список параграфов по курсу и номер параграфа у каждого вопроса.

Запуск: python3 Временные/привязать_параграфы.py
"""
import io
import json
import os
import re
import sys

import pymupdf

KOREN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UCH = os.path.join(KOREN, 'Временные', 'учебники')
BAZA = os.path.join(KOREN, 'Проект', 'База данных', 'Тренажёры',
                    'История, 7 класс')

# Учебник, файл, где начинается его словарь (дальше текста глав нет) и
# какой столбец рамки наш: в «Истории России» первым идёт Россия, во
# «Всеобщей истории» — Мир.
KNIGI = {
    'История России': {
        'fayl': 'istoriya-rossii-7.pdf', 'slovar': 264, 'stolbec': 'Россия',
    },
    'Всеобщая история': {
        'fayl': 'vseobshchaya-7.pdf', 'slovar': 226, 'stolbec': 'Мир',
    },
}

# Служебные слова: по ним событие с рамкой не сличить.
STOP = set('''гг год года году века век вв начало начало конец конец
первый первая первое первых принятие принят принята издание создание
строительство правление царствование война мир договор указ отмена
учреждение восстание поход битва осада взятие захват основание
введение установление заключение смерть рождение провозглашение
начало окончание в ходе после до'''.split())


def glavy_knigi(teksty):
    """[(страница, номер параграфа, название)] — порядок курса.

    Шапка страницы выглядит так: «47\\n§ 10–11\\nПрисоединение Поволжья.
    Начало Ливонской войны» — номер и название у первого абзаца главы.
    """
    glavy = []
    for i, tekst in enumerate(teksty):
        stroki = [s.strip() for s in tekst.split('\n')]
        for n, s in enumerate(stroki[:4]):
            m = re.match(r'^§\s*(\d+(?:\s*[–—-]\s*\d+)?)\.?\s*(.*)$', s)
            if m:
                nomer = re.sub(r'\s+', '', m.group(1)).strip('–-')
                nazvanie = m.group(2).strip()
                # название может занимать две строки
                for s2 in stroki[n + 1:n + 3]:
                    if not nazvanie:
                        nazvanie = s2
                        continue
                    if nazvanie.endswith(('.', '?', '!')) or len(nazvanie) > 60:
                        break
                    if not s2 or re.match(r'^[§?\d]', s2):
                        break
                    if len(s2) > 55 or s2.endswith('?'):
                        break
                    nazvanie += ' ' + s2
                nazvanie = re.sub(r'\s+', ' ', nazvanie).strip(' .')
                # Названия глав бывают из двух предложений («Начало Смуты.
                # Самозванец на троне»), поэтому режем не по точке, а по
                # началу вопроса: в учебниках после заголовка сразу идёт
                # «Почему…», «Как…», «Какие…» — это уже текст.
                vopros = re.search(r'\s+(Почему|Как|Какие|Каким|Каков|Что|Кто|'
                                   r'Когда|Где|Сколько|Можно|Удалось|Зачем|'
                                   r'Чем|В чём|Насколько)\s', nazvanie)
                if vopros:
                    nazvanie = nazvanie[:vopros.start()].strip(' .')
                if nazvanie.count('?') > 1 or nazvanie.endswith('?'):
                    nazvanie = nazvanie.split('?')[0].strip(' .')
                if not any(g[1] == nomer for g in glavy):
                    glavy.append((i + 1, nomer, nazvanie))
                break
    return glavy


def ramki(teksty, slovar):
    """Рамки «Россия / Мир»: [(страница, [запись, …])].

    Запись — «1533—1538 гг. — регентство и реформы Елены Глинской».
    Берём только свой столбец: он идёт первым, а чужой начинается там,
    где год ушёл назад (в обоих учебниках столбцы заполнены по годам).
    """
    itog = []
    for i, tekst in enumerate(teksty):
        if i + 1 >= slovar:
            break
        zapisi = [' '.join(s.split()) for s in
                  re.findall(r'Ǖ\s*([0-9][^\n]*(?:\n(?!Ǖ)[^\n]*)*)', tekst)]
        if not zapisi:
            continue
        svoi, posledniy = [], 0
        for z in zapisi:
            gody = [int(g) for g in re.findall(r'\d{3,4}', z)]
            if not gody:
                continue
            if svoi and gody[0] < posledniy:
                break
            svoi.append(z)
            posledniy = max(posledniy, gody[0])
        if svoi:
            itog.append((i + 1, svoi))
    return itog


def sekciya(stranica, glavy):
    """Номер параграфа, который проходят на этой странице.

    Страницы до первого параграфа (титул, вводная часть) — не наши:
    там ничего не проходят, поэтому параграфа нет.
    """
    nomer = None
    for str_, nom, _naz in glavy:
        if str_ <= stranica:
            nomer = nom
    return nomer


def gody(stroka):
    return {int(g) for g in re.findall(r'\d{3,4}', stroka)}


def slova(stroka):
    slova = re.findall(r'[а-яё]{5,}', stroka.lower())
    return {s for s in slova if s not in STOP}


def sravnit(sobytie, zapis):
    """Похожа ли запись рамки на событие из приложения.

    Считаем общие годы (главное) и общие слова события.
    """
    a, b = gody(sobytie), gody(zapis)
    obshchie = len(a & b)
    if not obshchie:
        return 0.0
    sl = len(slova(sobytie) & slova(zapis))
    return obshchie * 10 + sl


def prilozheniya(imya):
    fayl = os.path.join(BAZA, imya)
    with io.open(fayl, encoding='utf-8') as f:
        dannye = json.load(f)
    klyuch = 'даты' if 'даты' in dannye else 'определения'
    return dannye, klyuch


def main():
    knigi = {}
    for imya, k in KNIGI.items():
        d = pymupdf.open(os.path.join(UCH, k['fayl']))
        teksty = [d[i].get_text() for i in range(d.page_count)]
        knigi[imya] = {
            'glavy': glavy_knigi(teksty),
            'ramki': ramki(teksty, k['slovar']),
            'teksty': teksty,
            'slovar': k['slovar'],
        }
        print(f'{imya}: параграфов {len(knigi[imya]["glavy"])}, '
              f'рамок {len(knigi[imya]["ramki"])}')

    # Порядок курса — как в плейлисте седьмого класса: сначала всеобщая
    # история (её главы идут первыми), потом история России. Номер
    # параграфа в списке — это и есть место в курсе: «до § 12» значит
    # «всё, что встречается не позже двенадцатой строки этого списка».
    spisok = []
    nomera = {}          # «(учебник, номер)» → код параграфа
    for imya in ('Всеобщая история', 'История России'):
        for str_, nom, naz in knigi[imya]['glavy']:
            kod = f'{len(spisok) + 1:02d}'
            nomera[(imya, nom)] = kod
            spisok.append({'kod': kod, 'nomer': nom, 'nazvanie': naz,
                           'stranica': str_, 'uchebnik': imya})

    # --- даты: ищем запись рамки, больше всего похожую на событие
    dannye, _ = prilozheniya('Даты.json')
    bez = []
    for d in dannye['даты']:
        kn = knigi[d['учебник']]
        luchshiy, ochki = None, 0.0
        for str_, zapisi in kn['ramki']:
            for z in zapisi:
                o = sravnit(d['событие'] + ' ' + d['когда'], z)
                if o > ochki:
                    luchshiy, ochki = (str_, z), o
        nom_s = sekciya(luchshiy[0], kn['glavy']) if luchshiy else None
        if luchshiy and ochki >= 10 and nom_s:
            str_, z = luchshiy
            d['paragraf'] = nomera[(d['учебник'], nom_s)]
            d['iz_ramki'] = z
        else:
            d.pop('paragraf', None)
            d.pop('iz_ramki', None)
            bez.append(d['событие'])

    # --- определения: первый раз, когда термин встретился в тексте глав
    opred, _ = prilozheniya('Определения.json')
    bez_o = []
    for o in opred['определения']:
        kn = knigi[o['учебник']]
        termin = o['термин']
        naydeno = None
        obrazec = re.compile(re.escape(termin.split()[0][:8]), re.IGNORECASE)
        # Титул и вводная часть — не курс: ищем с первого параграфа.
        # Параграф выбираем не по первому упоминанию, а по тому, где термин
        # встречается чаще всего: в начале курса о нём часто говорят
        # вскользь («Смута» в главе про духовную жизнь XVI в.), а проходят
        # его много позже.
        schyot = {}
        for i, tekst in enumerate(kn['teksty'][kn['glavy'][0][0] - 1:
                                                kn['slovar'] - 1]):
            skolko = len(obrazec.findall(tekst))
            if skolko:
                nom_s = sekciya(i + kn['glavy'][0][0], kn['glavy'])
                if nom_s:
                    schyot[nom_s] = schyot.get(nom_s, 0) + skolko
        if schyot:
            luchshiy = max(schyot.values())
            naydeno = min(n for n, v in schyot.items() if v == luchshiy)
            naydeno = [g[0] for g in kn['glavy'] if g[1] == naydeno][0]
        nom_s = sekciya(naydeno, kn['glavy']) if naydeno else None
        if nom_s:
            o['paragraf'] = nomera[(o['учебник'], nom_s)]
            o['stranica_termina'] = naydeno
        else:
            o.pop('paragraf', None)
            bez_o.append(termin)

    with io.open(os.path.join(BAZA, 'Даты.json'), 'w', encoding='utf-8') as f:
        json.dump(dannye, f, ensure_ascii=False, indent=1)
        f.write('\n')
    with io.open(os.path.join(BAZA, 'Определения.json'), 'w', encoding='utf-8') as f:
        json.dump(opred, f, ensure_ascii=False, indent=1)
        f.write('\n')
    with io.open(os.path.join(BAZA, 'параграфы.json'), 'w', encoding='utf-8') as f:
        json.dump({'параграфы': spisok}, f, ensure_ascii=False, indent=1)
        f.write('\n')

    vse_d = len(dannye['даты'])
    vse_o = len(opred['определения'])
    print(f'Даты: привязано {vse_d - len(bez)} из {vse_d}')
    print(f'Определения: привязано {vse_o - len(bez_o)} из {vse_o}')
    if bez:
        print('  без параграфа (даты):', '; '.join(bez[:8]))
    if bez_o:
        print('  без параграфа (термины):', '; '.join(bez_o[:8]))


if __name__ == '__main__':
    sys.exit(main())
