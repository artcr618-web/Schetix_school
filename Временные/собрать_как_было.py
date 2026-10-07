# -*- coding: utf-8 -*-
"""Собрать «как было» — копию пакета с прежним поведением ширины.

Нужна для честного сравнения «до/после»: берём нынешний собранный
«Проект» и обратным превращением возвращаем в нём прежнюю арифметику —
раскладку по ширине ОКНА, а не по рабочей ширине.

    python3 Временные/собрать_как_было.py /tmp/do2

Что именно возвращается назад:

* ступени `@container` → те же пороги, но по окну (`@media`) — ровно
  прежняя арифметика;
* `cqw` → `vw` (доли окна);
* размер текста и обложки карточки — от `body`, а не от рабочей ширины;
* панель на узком окне — снова «почти весь кадр» (`min(420px, 100vw−40px)`)
  вместо во всю ширину, и ручка ширины остаётся;
* кадр плашки на вертикальном планшете — снова 16/9;
* поля страницы — только по окну (без `@supports (width:1cqw)`);
* блок запасного пути (`data-polosa`) — как его не было.

Скрипт ничего не трогает в самом «Проекте»: он работает с копией.
"""
import io
import os
import re
import shutil
import sys

OTKUDA = 'Проект'
POLOSY_V_STRANICE = [
    ('планшет вертикальный', '3 / 2', '16 / 9'),
]


def main(kuda):
    if os.path.exists(kuda):
        shutil.rmtree(kuda)
    shutil.copytree(OTKUDA, kuda)
    f = os.path.join(kuda, 'База данных', 'оформление.css')
    s = io.open(f, encoding='utf-8').read()
    bylo = s

    # ступени по рабочей ширине — снова по ширине окна, с ТЕМИ ЖЕ
    # порогами: тогда получается ровно прежнее поведение (в прежней
    # сборке пороги считались от окна и меню не замечали)
    s, skolko = re.subn(r'@container stranica \(max-width:(\d+)px\)',
                        r'@media (max-width:\1px)', s)
    if not skolko:
        raise SystemExit('не нашлось ни одной контейнерной ступени')
    # доли рабочей ширины — доли окна
    s = s.replace('cqw', 'vw')
    # текст и карточка меряются от body, как было
    s = s.replace('.wrap{font-size:26px}', 'body{font-size:26px}')
    # поля страницы — только по окну
    s = re.sub(r'@supports \(width:1cqw\)\{[^}]*\}\}', '', s)
    # кадр плашки на вертикальном планшете — прежний
    s = s.replace('a.plitka{aspect-ratio:3 / 2;', 'a.plitka{aspect-ratio:16 / 9;')
    # панель на узком окне — прежняя, с ручкой ширины
    s = s.replace("""@media (max-width:959px){
  /* Вертикальный планшет и телефоны: панель во всю ширину */
  body{--panel-shirina:100vw}
  body.menu-otkryto, body.pleylist-otkryto{padding-right:0}
  body.menu-otkryto .panel-tyanulka.menyu,
  body.pleylist-otkryto .panel-tyanulka.pleylista,
  .panel-tyanulka{display:none}
}""",
"""@media (max-width:639px){
  body{--panel-shirina:min(420px, calc(100vw - 40px))}
  body.menu-otkryto, body.pleylist-otkryto{padding-right:0}
}""")
    # блок запасного пути (data-polosa) — выключить
    s = re.sub(r'@supports not \(container-type: inline-size\)\{.*?\n\}',
               '', s, flags=re.S)
    if s == bylo:
        raise SystemExit('ничего не изменилось — обратное превращение '
                         'не сработало, проверь правила')
    io.open(f, 'w', encoding='utf-8').write(s)

    # скрипт: полосу по data-polosa больше не считаем (её некому читать)
    for koren, _, faily in os.walk(kuda):
        for imya in faily:
            if not imya.endswith('.html'):
                continue
            p = os.path.join(koren, imya)
            t = io.open(p, encoding='utf-8').read()
            t = t.replace('if(!est_konteynery){', 'if(false){')
            io.open(p, 'w', encoding='utf-8').write(t)
    print('собрано «как было»:', kuda)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '/tmp/do2')
