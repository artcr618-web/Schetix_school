# -*- coding: utf-8 -*-
"""Проверяет пакет «Проект»: все внутренние ссылки ведут на существующие
файлы, у каждой страницы есть шапка с навигацией и javascript домашней
страницы.

    python3 Временные/proverka_paketa.py
"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), 'Инструменты'))
from _пути import PROEKT, VSE_STRANICY  # noqa: E402

oshel = 0
for polny in sorted(VSE_STRANICY):
    if PROEKT not in polny:
        continue
    s = open(polny, encoding='utf-8').read()
    papka = os.path.dirname(polny)
    otn = os.path.relpath(polny, PROEKT)

    for m in re.finditer(r'href="([^"#][^"]*)"', s):
        h = m.group(1)
        if h.startswith(('http://', 'https://', 'mailto:', 'javascript:')):
            continue
        # #menu и ?menu=1 — метки для javascript, а не часть пути
        cel = os.path.normpath(os.path.join(papka, h.split('?')[0]
                                            .split('#')[0]))
        if not os.path.exists(cel):
            print(f'  БИТАЯ ССЫЛКА  {otn}  ->  {h}')
            oshel += 1

    if '<nav class="verh">' not in s:
        print(f'  НЕТ ШАПКИ: {otn}')
        oshel += 1
    if "getElementById('pin')" not in s:
        print(f'  НЕТ СКРИПТА ДОМАШНЕЙ СТРАНИЦЫ: {otn}')
        oshel += 1
    if 'shkola.home' not in s:
        print(f'  НЕТ КЛЮЧА ЗАПОМИНАНИЯ: {otn}')
        oshel += 1

# в корне пакета ровно один файл
koren = [f for f in sorted(os.listdir(PROEKT))
         if os.path.isfile(os.path.join(PROEKT, f))]
if koren != ['Начать учиться.html']:
    print(f'  В КОРНЕ НЕ ОДИН ФАЙЛ: {koren}')
    oshel += 1

print(f'\nКорень пакета: {koren}')
print('Проблем:', oshel if oshel else 'нет')
