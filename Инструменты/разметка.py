# -*- coding: utf-8 -*-
"""Разметка: модели экранов и раскладка плашек.

ЕДИНСТВЕННОЕ место, где записано, сколько плашек в ряд на каждой модели
экрана и какого они размера. Отсюда берётся всё:

  * `setka_css()` — CSS сетки плашек; его подставляет _tv.py в каждую
    страницу при сборке, поэтому в самих страницах этот блок править
    нельзя — перезапишется;
  * `zapisat()` — Временные/разметка.json для проверки
    (Временные/proverka_setki.js): сверка вёрстки идёт по той же таблице,
    по которой она собрана, а не по числам, записанным в проверке руками;
  * таблица моделей — в РАЗМЕТКА.md, для людей.

МОДЕЛЬ ЭКРАНА — как у Тильды. Пять контрольных точек: 320 / 480 / 640 /
960 / 1200. Ниже 320 px страница не ужимается (у Тильды это нижний
артборд). Новых контрольных точек не заводим: вся адаптация идёт только
по этим пяти, иначе вёрстка начинает жить на десятке незаметных порогов.

Шесть моделей (так их называет Тильда и так же называем мы):

    Широкий экран           1440 и шире
    Обычный экран           1200 – 1439
    Планшет горизонтальный   960 – 1199
    Планшет вертикальный     640 –  959
    Телефон горизонтальный   480 –  639
    Телефон вертикальный     320 –  479

Плашки: три в ряд на обоих десктопах, две — на обоих планшетах, одна
во всю ширину — на обоих телефонах. Размер задан долями кадра
(minmax(0, 1fr)), а не пикселями: плашки в ряду всегда одного размера,
ряд заполнен целиком, а при сужении окна они уменьшаются в масштабе.
"""

# Контрольные точки Тильды. Их не сдвигаем.
TOCHKI = (1200, 960, 640, 480, 320)

# Ширина, ниже которой страница не ужимается.
DNO = 320

# Шесть моделей экрана: имя, от какой ширины, до какой (включительно).
MODELI = (
    ('Широкий экран',          1440, None),
    ('Обычный экран',          1200, 1439),
    ('Планшет горизонтальный',  960, 1199),
    ('Планшет вертикальный',    640,  959),
    ('Телефон горизонтальный',  480,  639),
    ('Телефон вертикальный',    320,  479),
)

# Раскладка плашек по полосам ширины. Полоса — от одной контрольной
# точки до следующей; `do` — её нижняя граница (включительно), у самой
# широкой полосы границы нет.
#
#   v_ryadu — сколько плашек в ряду
#   gap     — зазор между плашками
#   nazv    — размер названия плашки
#   poyas   — размер подписи под названием
#   polosa  — ширина жёлтой полосы слева
#   radius  — скругление плашки
#   chislo  — размер цифры на плашке класса
#   otstup  — внутренние поля плашки
POLOSY = (
    dict(imya='десктопы', do=None, v_ryadu=3, gap=24,
         nazv=36, poyas=20, polosa=18, radius=22,
         chislo='clamp(110px, 12vw, 186px)', kadr='16 / 9',
         otstup='24px 26px 24px calc(var(--polosa) + 28px)'),
    dict(imya='планшет горизонтальный', do=1199, v_ryadu=2, gap=20,
         nazv=36, poyas=18, polosa=16, radius=18,
         chislo='clamp(110px, 12vw, 186px)', kadr='16 / 9',
         otstup='22px 24px 22px calc(var(--polosa) + 26px)'),
    # Плашка вдвое уже десктопной, поэтому название и подпись здесь
    # мельче: иначе длинные названия («Кино и документалистика») не
    # влезали и вылезали за плашку.
    dict(imya='планшет вертикальный', do=959, v_ryadu=2, gap=18,
         nazv=28, poyas=15, polosa=13, radius=14,
         chislo='clamp(70px, 11vw, 150px)', kadr='16 / 9',
         otstup='20px 22px 20px calc(var(--polosa) + 24px)'),
    # Телефон горизонтальный: плашка во всю ширину, 16/9 хватает.
    dict(imya='телефоны горизонтальные', do=639, v_ryadu=1, gap=16,
         nazv=32, poyas=17, polosa=13, radius=14,
         chislo='clamp(80px, 30vw, 186px)', kadr='16 / 9',
         otstup='22px 24px 22px calc(var(--polosa) + 26px)'),
    # Телефон вертикальный — самая узкая полоса: плашка во всю ширину,
    # но кадр узкий, и длинное название с подписью в 16/9 не
    # помещаются. Плашка становится выше (4/3), оставаясь одного
    # размера с соседями.
    dict(imya='телефоны вертикальные', do=479, v_ryadu=1, gap=16,
         nazv=32, poyas=17, polosa=13, radius=14,
         chislo='clamp(80px, 30vw, 186px)', kadr='4 / 3',
         otstup='22px 24px 22px calc(var(--polosa) + 26px)'),
)

# Поля страницы по краям: на широком экране 44 px, на телефоне 20 px.
# Плашка занимает всю строку, и на телефоне лишние поля съедали бы
# четверть кадра.
POLYA = 'clamp(20px, 4vw, 44px)'


def _blok(p, otstup, baza=False):
    kolonki = f'repeat({p["v_ryadu"]}, minmax(0, 1fr))'
    # display:grid и отступ сверху задаются один раз, в базовой полосе:
    # в ступенях меняются только колонки и размеры.
    osnova = 'display:grid; margin-top:26px; ' if baza else ''
    return (
        f'{otstup}.setka{{{osnova}grid-template-columns:{kolonki}; '
        f'gap:{p["gap"]}px; '
        f'--polosa:{p["polosa"]}px; --radius:{p["radius"]}px}}\n'
        f'{otstup}a.plitka{{aspect-ratio:{p["kadr"]}; '
        f'padding:{p["otstup"]}}}\n'
        f'{otstup}a.plitka .nazv{{font-size:{p["nazv"]}px}}\n'
        f'{otstup}a.plitka .poyas{{font-size:{p["poyas"]}px}}\n'
        f'{otstup}a.plitka.klass .nazv .chislo{{font-size:{p["chislo"]}}}')


def setka_css():
    """CSS сетки плашек: базовая полоса и три ступени вниз."""
    shirokaya = POLOSY[0]
    chasti = [
        '/* РАСКЛАДКА ПЛАШЕК — собрана из Инструменты/разметка.py.\n'
        '   Здесь не править: при сборке блок перезаписывается.\n'
        '   Модели экрана — в РАЗМЕТКА.md. */',
        _blok(shirokaya, '', baza=True),
    ]
    for p in POLOSY[1:]:
        chasti.append(f'@media (max-width:{p["do"]}px){{\n'
                      f'  /* {p["imya"]}: {p["v_ryadu"]} в ряд */\n'
                      + _blok(p, '  ') + '\n}')
    return '\n'.join(chasti)


def polosa_dlya(shirina):
    """Полоса раскладки для ширины окна (для проверок)."""
    for p in reversed(POLOSY[1:]):
        if shirina <= p['do']:
            return p
    return POLOSY[0]


def zapisat():
    """Таблица для проверки: Временные/разметка.json."""
    import json
    import os

    sdvig = os.path.dirname(os.path.abspath(__file__))
    kuda = os.path.join(sdvig, '..', 'Временные', 'разметка.json')
    dannye = {
        'dno': DNO,
        'tochki': list(TOCHKI),
        'modeli': [dict(imya=i, ot=o, do=d) for i, o, d in MODELI],
        'polosy': [dict(imya=p['imya'], do=p['do'],
                        v_ryadu=p['v_ryadu'], nazv=p['nazv'],
                        kadr=p['kadr'])
                   for p in POLOSY],
    }
    with open(kuda, 'w', encoding='utf-8') as f:
        json.dump(dannye, f, ensure_ascii=False, indent=1)
    return kuda


if __name__ == '__main__':
    print('Модели экрана (как у Тильды):')
    for imya, ot, do in MODELI:
        polosa = polosa_dlya(ot)
        print(f'  {imya:<24} {ot}–{do if do else "…":<6} '
              f'плашек в ряд: {polosa["v_ryadu"]}')
    print(f'\nНиже {DNO} px страница не ужимается.')
    print('json для проверок:', zapisat())
