# -*- coding: utf-8 -*-
"""Страницы «Кино и документалистика» и «Лекции».

Устроены ровно как страница видеоуроков: полоса учебника, кадр и под ним
списки-плейлисты. Ничего своего, чтобы ребёнок не учил два разных экрана.
Страница лекций — из этого же ряда (см. `main`: `rezhim='лекции'`): тот же
кадр и те же подборки, отличаются только слова, да и тех всего два.

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
         klassy=None, zagolovok=None, podzagolovok=None, rezhim='', vopros=None,
         kak_v_dannyh=False, niz='', zag_spiska=''):
    """Собрать страницу кино или лекций.

    `fayl`, `put` — пути от корня пакета; `dannye` — имя файла подборок
    в «Временные». Остальное передаёт gen_tv_paket: меню, учебник и
    хлебные крошки одинаковы на всех страницах предмета.

    `zagolovok`, `podzagolovok` — заголовок страницы для окна браузера.
    По умолчанию берутся из файла подборок, как у кино: там этот файл
    и заведён под страницу. У лекций он общий с баннером, а у баннера
    свои слова («Лекции», «Мединский»), поэтому страница называет себя
    сама — из `ZAGOLOVKI` в gen_tv_paket.

    `rezhim='лекции'` — страница говорит плееру, что она не фильм:
    тогда кнопка после лекции называется «Следующая лекция», а в шапке
    стоит свой вопрос (`vopros`).

    `kak_v_dannyh` — не переставлять пункты плейлиста: у лекций порядок
    авторский, сериями, и в файле данных он уже такой (см. blok_playera).

    `niz` — готовая разметка блока «Разделы» (плашки материалов
    предмета): он идёт под списками, чтобы с этой страницы можно было
    уйти на контрольную или в кино. `zag_spiska` — надпись над списком
    («Подборки»).
    """
    R, nabor = nabor_iz_dannyh(dannye)
    if not nabor:
        raise SystemExit(f'В файле {dannye} нет ни одной подборки')
    blok_pleera, panel_pleylista = _tv.blok_playera(
        nabor, vopros=vopros, kak_v_dannyh=kak_v_dannyh,
        zag_spiska=zag_spiska, niz=niz)
    bloki = [blok_pleera]
    put_fayla, razmer = _tv.sobrat(zagolovok or R['заголовок'],
                                   podzagolovok or R['подзаголовок'], bloki,
                                   fayl, put=put, indeks=True,
                                   menyu_spisok=menyu_spisok,
                                   menyu_zagolovok=menyu_zagolovok,
                                   kniga=kniga, klassy=klassy,
                                   telo_klass='pleylist-otkryto',
                                   paneli=panel_pleylista,
                                   rezhim=rezhim)
    print(f'  {fayl:<46} ' + ', '.join(f'{i} ({len(r)})' for i, r in nabor) +
          f', {razmer:>6} байт')
    return put_fayla


if __name__ == '__main__':
    # По одной странице руками — на случай, когда генератор пакета
    # трогать не хочется.
    print('Этот файл вызывается из gen_tv_paket.py: страница кино — часть '
          'пакета, а не отдельная сборка.')
