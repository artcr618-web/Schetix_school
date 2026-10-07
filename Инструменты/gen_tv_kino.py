# -*- coding: utf-8 -*-
"""Страницы «Кино и документалистика».

Устроены ровно как страница видеоуроков: полоса учебника, кадр и под ним
списки-плейлисты. Ничего своего, чтобы ребёнок не учил два разных экрана.

Данные — в «Временные/kino_<предмет>_<класс>.json». Их собирает
«Временные/kino_sborka.py»: он берёт названия и длительность у Rutube,
поэтому в файле не бывает выдуманных подписей.

Подборки показываются в том порядке, в каком лежат в файле; первая
открывается сразу при входе на страницу (как и на видеоуроках).
"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _tv  # noqa: E402

KOREN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VREM = os.path.join(KOREN, 'Временные')


def dannye_est(fayl):
    """Путь к файлу данных подборок (без проверки, что он есть)."""
    return os.path.join(VREM, fayl)


def nabor_iz_dannyh(fayl):
    """Подборки в том виде, в каком их ждёт `_tv.blok_playera`."""
    if not os.path.exists(fayl):
        raise SystemExit(f'Нет файла с подборками: {fayl}')
    R = json.load(io.open(fayl, encoding='utf-8'))
    nabor = []
    for p in R['подборки']:
        ryady = []
        for v in p['видео']:
            podpis, kod, sek = v[0], v[1], (v[2] if len(v) > 2 else 0)
            # Время словами: «48 мин», «1 ч 21 мин», «3 ч 42 мин» —
            # у полнометражных «222 мин» читалось бы плохо.
            ryady.append((_tv.dlitelnost(sek), podpis,
                          f'https://rutube.ru/video/{kod}/'))
        if ryady:
            nabor.append((p['имя'], ryady))
    return R, nabor


def main(fayl, put, dannye, menyu_spisok=None, menyu_zagolovok='', kniga=None,
         klassy=None):
    """Собрать страницу кино.

    `fayl`, `put` — пути от корня пакета; `dannye` — имя файла подборок
    в «Временные». Остальное передаёт gen_tv_paket: меню, учебник и
    хлебные крошки одинаковы на всех страницах предмета.
    """
    R, nabor = nabor_iz_dannyh(dannye)
    if not nabor:
        raise SystemExit(f'В файле {dannye} нет ни одной подборки')
    blok_pleera, panel_pleylista = _tv.blok_playera(nabor)
    bloki = [blok_pleera]
    put_fayla, razmer = _tv.sobrat(R['заголовок'], R['подзаголовок'], bloki,
                                   fayl, put=put, indeks=True,
                                   menyu_spisok=menyu_spisok,
                                   menyu_zagolovok=menyu_zagolovok,
                                   kniga=kniga, klassy=klassy,
                                   telo_klass='pleylist-otkryto',
                                   paneli=panel_pleylista)
    print(f'  {fayl:<46} ' + ', '.join(f'{i} ({len(r)})' for i, r in nabor) +
          f', {razmer:>6} байт')
    return put_fayla


if __name__ == '__main__':
    # По одной странице руками — на случай, когда генератор пакета
    # трогать не хочется.
    print('Этот файл вызывается из gen_tv_paket.py: страница кино — часть '
          'пакета, а не отдельная сборка.')
