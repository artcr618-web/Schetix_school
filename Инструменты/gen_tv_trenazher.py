# -*- coding: utf-8 -*-
"""Страница «Тренажёры».

Устроена как страница видеоуроков: то же поле в кадре 16:9, та же
выезжающая панель справа. Отличается содержимое: в поле — карточка того,
что сейчас решаем, в панели — настройки тренажёра.

Панель здесь называют «Настройки», и это не список уроков: ребёнок не
выбирает «урок», он настраивает, что тренировать. Порядок настроек — от
общего к частному:

* что решаем — всё вместе, только даты, только определения;
* до какого параграфа — по умолчанию «весь курс»; выбран параграф —
  вопросы идут с начала курса до него, а флажок оставляет один этот
  параграф. Выбор — строкой с поиском: нажали, набрали номер или слово
  из названия, выбрали. Списком все пятьдесят параграфов не нужны.

Заходов и порций здесь нет: набор задаётся настройками и решается
подряд в случайном порядке, а бросить его можно в любой момент. Статистика и «работа над
ошибками» стоят ПОД полем, а не в панели: их видно всегда, не заглядывая
в настройки.

Данные берутся из базы самого пакета: «База данных/Тренажёры/История,
7 класс/Даты.json», «…/Определения.json» и «…/параграфы.json». Даты и
определения собирает «Временные/собрать_даты_и_определения.py», а
привязку вопросов к параграфам — «Временные/привязать_параграфы.py».

В поле идёт решение: вопрос, четыре варианта, отзыв и «Дальше».
Устроено оно так: стороны чередуются («событие → год» и «год → событие»,
«термин → значение» и «значение → термин»), неверные варианты подбираются
ближними по смыслу — соседние годы и слова из ближних параграфов, верный
ответ подсвечивается, а ошибки копятся и собираются в отдельный набор
для работы над ошибками.

Почему поле то же, а не своё: ребёнок не должен учить второй экран.
Ходит он по одному и тому же месту — слева кадр, справа панель, — и
тренажёр встаёт в знакомые рамки.
"""
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _tv  # noqa: E402
import разметка as _razmetka  # noqa: E402

BAZA_TREN = os.path.join(_tv.PAKET, _tv.BAZA, 'Тренажёры')

# Что решаем. Ключ живёт в настройках страницы, подписи — в панели.
# Что тренируем: ключ и надпись. Пояснений при строках нет — как идут
# вопросы, видно по первому же вопросу, а на пустом экране эти пояснения
# только занимали место (и число вопросов при них — тоже).
VIDY = [
    ('vse', 'Даты и определения'),
    ('daty', 'Только даты'),
    ('opredeleniya', 'Только определения'),
]
OSHIBSKI = 'Работа над ошибками'
# Пояснение к «Работе над ошибками»: сама строка говорит, куда ведёт,
# и длинных пояснений на экране больше нет.
TEKST_OSHIBSKI = 'Сюда попадут вопросы, в которых ты ошибался.'
# Кольцо выбора: точка внутри загорается у выбранной строки. Тот же
# знак, что у пункта без параграфа в плейлисте (см. _tv.ZNAK_BEZ_NOMERA),
# только точка отдельным кружком — её и прячет оформление.
# Порядок учебников в настройках: сперва «История России», за ней
# «Всеобщая история» — так их и называют в курсе. Незнакомый учебник
# встаёт в конец списка, а не теряется.
UCH_PORYADOK = ['История России', 'Всеобщая история']
KOLCO = ('<svg viewBox="0 0 24 24" aria-hidden="true">'
         '<circle cx="12" cy="12" r="8.6" fill="none" stroke="currentColor" '
         'stroke-width="2.4"/>'
         '<circle class="tochka" cx="12" cy="12" r="3.4" '
         'fill="currentColor"/></svg>')


def po_tire(dannye):
    """Пройти правило тире по всем строкам данных (см. _tv.tire).

    Страница отдаёт эти строки как есть — и в вопрос, и в ответ, и в
    подсказку. Промежутки между числами в них («1607—1610», «12–13»)
    приводим к одному виду прямо при чтении базы: тогда правило видно
    везде, где строка ни всплывёт.
    """
    if isinstance(dannye, dict):
        return {k: po_tire(v) for k, v in dannye.items()}
    if isinstance(dannye, list):
        return [po_tire(v) for v in dannye]
    if isinstance(dannye, str):
        return _tv.tire(dannye)
    return dannye


def dannye_est(klass, predmet):
    """Прочитать «Даты» и «Определения» из базы тренажёров.

    Возвращает {'даты': [...], 'определения': [...], 'учебники': [...]}.
    Если файлов нет — сборку останавливаем: страница с пустым тренажёром
    хуже, чем понятная ошибка сборки.
    """
    papka = os.path.join(BAZA_TREN, f'{predmet}, {klass}')
    itog = {'даты': [], 'определения': [], 'учебники': []}
    for imya, klyuch in (('Даты.json', 'даты'),
                         ('Определения.json', 'определения')):
        put = os.path.join(papka, imya)
        if not os.path.exists(put):
            raise SystemExit(f'Нет файла базы тренажёров: {put}')
        with io.open(put, encoding='utf-8') as f:
            dannye = po_tire(json.load(f))
        itog[klyuch] = dannye[klyuch]
        for u in dannye.get('учебники', []):
            if u not in itog['учебники']:
                itog['учебники'].append(u)
    if not itog['даты'] or not itog['определения']:
        raise SystemExit(f'База тренажёров пуста: {papka}')
    return itog


def paragrafy_est(klass, predmet):
    """Прочитать список параграфов курса («параграфы.json»).

    Порядок в файле — порядок курса: сначала всеобщая история, потом
    история России. У каждого вопроса в базе стоит код параграфа, и «до
    какого параграфа» — это сравнение кодов. Без файла настройка не
    работала бы молча, поэтому останавливаем сборку.
    """
    put = os.path.join(BAZA_TREN, f'{predmet}, {klass}', 'параграфы.json')
    if not os.path.exists(put):
        raise SystemExit(f'Нет списка параграфов: {put} — его собирает '
                         'Временные/привязать_параграфы.py')
    with io.open(put, encoding='utf-8') as f:
        dannye = po_tire(json.load(f))
    return dannye['параграфы']


def skolko(chislo):
    """«96 вопросов», «181 вопрос» — с числом и правильным окончанием.

    На самой странице эта подпись теперь не встречается: пустой экран
    обходится без числа вопросов, а у статистики под полем свои подписи.
    Оставлено нарочно — вернётся, если число понадобится где-то ещё.
    """
    return _tv.sklonenie(chislo, 'вопрос', 'вопроса', 'вопросов')


def stroka_vida(klyuch, imya, aktiven=False):
    """Строка «что решаем»: кольцо и подпись.

    Без числа вопросов: сколько их в наборе, сказано один раз — строкой
    «в работе» под настройками. Числа у каждой кнопки спорят друг с
    другом и читаются как три отдельных тренажёра вместо одного выбора.
    """
    return ('<a class="nastr-stroka' + (' aktiven' if aktiven else '') +
            f'" href="#" data-vid="{klyuch}" onclick="return shkVid(this)">'
            f'<span class="nastr-kolco">{KOLCO}</span>'
            f'<span class="nastr-tekst">{_tv.myagkie(imya)}</span></a>')


def stroka_uch(klyuch, imya, aktiven=False):
    """Строка «по какому учебнику»: кольцо и подпись.

    Учебников в курсе два, и вопросы у них разные: «История России» и
    «Всеобщая история» — две книги, а не главы одной. Строка выбирает
    одну из них или весь курс сразу. У курса с единственным учебником
    выбора нет, и раздела этого в настройках тоже нет (см.
    blok_trenazhera).
    """
    return ('<a class="nastr-stroka' + (' aktiven' if aktiven else '') +
            f'" href="#" data-uch="{_tv.myagkie(klyuch)}" '
            'onclick="return shkUchebnik(this)">'
            f'<span class="nastr-kolco">{KOLCO}</span>'
            f'<span class="nastr-tekst">{_tv.myagkie(imya)}</span></a>')


def blok_trenazhera(dannye, paragrafy, priglashenie, niz='', ssylka_video='',
                    uchebniki=(), s_video=None):
    """Поле с карточкой и панель настроек.

    Возвращает пару: разметку страницы и разметку выезжающей панели — её
    страница ставит снаружи контейнера рабочей ширины (см. `_tv.sobrat`).

    `ssylka_video` — путь к странице видеоуроков от этой страницы.
    Отзыв после ответа ведёт по нему на урок нужного параграфа; если
    видеоуроков у предмета нет, ссылки не будет.

    `niz` — готовая разметка блока «Разделы» (плашки материалов
    предмета): под полем она даёт выход туда, куда с тренажёра идут, —
    в видеоуроки или на контрольную. Собирает её gen_tv_paket: у него
    под рукой дерево предмета.
    """
    # Кристалл в верхней строке поля — один: рядом число собранных.
    # Так счёт видно точно, и места он занимает одно (ставит скрипт,
    # см. nagrady в JS_TRENAZHERA).
    kristall = _tv.ikona('кристалл').replace('<svg ', '<svg class="kristall" ', 1)
    karta = ('<div class="trener-karta" id="trener-karta">'
             # Верхняя строка поля: слева место вопроса, справа награды и
             # «на весь экран». Она одна на все три вида поля, поэтому
             # стоит здесь, а не в скрипте.
             '<div class="trener-verh">'
             '<span class="trener-schet-za" id="trener-schet-za" hidden></span>'
             # Слева от строки — сначала кристалл с числом правильных,
             # затем красный счётчик ошибок. Они относятся к «N / M» и
             # не должны разъезжаться по правому краю.
             '<span class="trener-nagrady" id="trener-nagrady">'
             '<span class="trener-kristally" id="trener-kristally">'
             + kristall +
             '</span>'
             '<span class="trener-chislo" id="trener-chislo">0</span>'
             '</span>'
             '<span class="trener-oshibki-schet" id="trener-oshibki-schet" '
             'hidden aria-label="Ошибки">'
             '<span class="trener-krestik">' + _tv.ikona('ошибка') +
             '</span>'
             '<b id="stat-oshibok">0</b></span>'
             # Справа остаются только вопрос и полноэкранный режим.
             '<span class="trener-znachki">'
             '<span class="trener-znachok vopros tuskly" id="trener-podskazka-znak" '
             'aria-label="Подсказка по этому вопросу" aria-disabled="true">'
             + _tv.ikona('вопрос') + '</span>'
             '<a class="trener-znachok" id="trener-vo-ves-ekran" href="#" '
             'aria-label="На весь экран" '
             'onclick="return shkVoVesEkran()">'
             + _tv.ikona('во весь экран') + '</a>'
             '</span>'
             '</div>'
             # Всё остальное поля — под верхней строкой: приглашение или
             # вопрос захода. Обёртка нужна ради трети высоты у вопроса.
             '<div class="trener-telo">'
             # Пустой экран — сам кнопка: ни плашки, ни подложки, только
             # белый контур во всё поле и крупная белая надпись по центру
             # (см. .trener-priglashenie). Нажимается всё поле.
             '<div class="trener-priglashenie" id="trener-priglashenie">'
             '<a class="trener-nachat" id="trener-nachat" href="#" '
             'onclick="return shkNachat()">Начать тренировку</a>'
             '</div>'
             # Заход идёт — вопрос встаёт сюда, вместо приглашения
             # (наполняет скрипт, см. pokazat() в JS_TRENAZHERA).
             '<div class="trener-igra" id="trener-igra"></div>'
             '</div>'
             '</div>')
    knopka = ('<a class="nastr-knopka" href="#" aria-label="Настройки" '
              'onclick="return shkNastroyki()">' + _tv.ikona('настройки') +
              '</a>')
    # Над кадром — не имя страницы, а сами настройки: «Даты и
    # определения · История России · до § 12». Крупно, тем же кеглем, что
    # подпись кадра на видеоуроках; подзаголовка под ним нет — настройки и
    # есть подпись, вторая строка повторяла бы их же. Меняются настройки —
    # меняется и строка (см. stroka_nastroek в JS_TRENAZHERA).
    stranica = ('<div class="pleyer-wrap">'
                '<div class="pleyer-shapka trener-shapka">'
                f'<span class="pleyer-zag" id="pleyer-zag">'
                f'{priglashenie["svodka"]}</span>'
                # Кнопка настроек — в той же строке, у правого края: так
                # она стоит на своём месте и не «подпрыгивает» под
                # надписью, когда та переносится на две строки.
                f'{knopka}'
                '</div>'
                '<div class="pleyer-mesto" id="pleyer-mesto">'
                # Класс trener-pleyer снимает у поля пропорции кадра: это
                # рабочий экран, он растёт по высоте содержимого.
                f'<div class="pleyer trener-pleyer" id="pleyer">{karta}</div>'
                # «Работа над ошибками» — под полем, во всю его ширину
                # (наполняет скрипт, см. oshibki_knopka): под экраном ей
                # просторнее, чем в поле, где она оттягивала ответы.
                '<div class="trener-oshibki-pod" id="trener-oshibki-mesto">'
                '</div>'
                # Окно подсказки: встаёт на место экрана теста и того же
                # размера (координаты считает скрипт, см. shkPodskazka).
                '<div class="trener-okno-podskazki" id="trener-okno-podskazki" '
                'aria-hidden="true">'
                '<div class="trener-okno-karta" id="trener-okno-karta" '
                'role="dialog" aria-label="Подсказка по вопросу">'
                '<div class="trener-okno-verh">'
                '<span class="trener-okno-zag" id="trener-okno-zag">'
                'Подсказка</span>'
                '<a class="trener-okno-zakryt" href="#" aria-label="Закрыть" '
                'onclick="return shkPodskazkaZakryt()">' + _tv.ikona('закрыть') +
                '</a></div>'
                '<div class="trener-okno-telo" id="trener-okno-telo"></div>'
                '</div></div>'
                '</div></div>')

    # Сноски об учебниках на странице нет: по какому учебнику вопросы,
    # видно и так — на учебник уводит строка под путём, а в отзыве после
    # ответа стоят параграф и страница.

    chislo_d = len(dannye['даты'])
    chislo_o = len(dannye['определения'])

    # Под полем статистики нет вовсе: и счёт вопросов, и счёт ошибок
    # стоят в верхней строке поля (см. trener-verh выше), а «Работа над
    # ошибками» — в нижней строке поля. Третьего счёта — «осталось
    # пройти» — не пишем: он и есть разница между «2 / 277» и номером.

    # Подписи для скрипта: он подменяет карточку в поле, когда меняются
    # настройки. Тексты те же, что в панели, — разойтись им нечем.
    podpisi = {klyuch: {'zag': imya} for (klyuch, imya) in VIDY}
    podpisi['oshibki'] = {'zag': OSHIBSKI, 'tekst': TEKST_OSHIBSKI}
    slov = json.dumps(podpisi, ensure_ascii=False, indent=2)
    js = JS_TRENAZHERA.replace('{TRENERY}', slov)
    js = js.replace('{PARAGRAFY}', slov_paragrafov(paragrafy))
    js = js.replace('{VOPROSY}', slov_voprosov(dannye, paragrafy))
    js = js.replace('{KOLCO}', KOLCO)
    js = js.replace('{OSHIBSKI}', OSHIBSKI)
    js = js.replace('{SHEVRON}', _tv.ikona('шеврон'))
    js = js.replace('{STRELKA_NAZAD}', _tv.ikona('назад'))
    js = js.replace('{STRELKA_VPERED}', _tv.ikona('вперёд'))
    js = js.replace('{SSYLKA_VIDEO}', ssylka_video or '')
    js = js.replace('{S_VIDEO}',
                    json.dumps(list(s_video or []), ensure_ascii=False))
    js = js.replace('MENYU-VO-VSYU', str(_razmetka.MENYU_VO_VSYU))

    # --- панель настроек ---
    # Подписи «что тренируем» берём из VIDY: разойтись панели со скриптом
    # нечем — он берёт те же подписи оттуда же.
    vidy = ''.join(stroka_vida(klyuch, imya, aktiven=(n == 0))
                   for n, (klyuch, imya) in enumerate(VIDY))
    # Раздел «Выбор учебника» — только там, где учебников больше одного:
    # у курса с одной книгой выбирать не из чего.
    ucheb = ''
    if len(uchebniki) > 1:
        ucheb = ('<div class="nastr-zag">Выбор учебника</div>'
                 + stroka_uch('', 'Весь курс', aktiven=True)
                 + ''.join(stroka_uch(u, u) for u in uchebniki))
    # Параграфы в панели списком не показываются: их пятьдесят, и такой
    # список вытеснял всё остальное. Выбор — через поиск (см. JS).
    panel = (
        '<aside class="panel" id="pleylist-panel">'
        '<div class="panel-verh"><span class="panel-zag" id="pl-zag">'
        'Настройки</span>'
        '<a class="panel-zakryt" href="#" aria-label="Закрыть настройки" '
        'onclick="return shkPleylist(false)">' + _tv.ikona('закрыть') +
        '</a></div>'
        '<div class="panel-telo">'
        '<div class="nastr-zag">Что тренируем</div>' + vidy + ucheb +
        # Раздел «Ограничить до» — только у выбранного учебника: «весь
        # курс» ничем не ограничен, и раздела там нет вовсе. Внутри —
        # одно поле: в него и набирают, а список найденного раскрывается
        # прямо под ним. Выбранный параграф встаёт в само поле, а справа
        # в поле — крестик: нажали — ограничение снято. Строки ниже нет:
        # выбранное видно там, где его и выбирали.
        '<div class="nastr-par" id="nastr-par" hidden>'
        '<div class="nastr-zag">Ограничить до</div>'
        '<div class="nastr-okno" id="nastr-okno">'
        '<span class="nastr-pole">'
        '<input class="nastr-poisk" id="nastr-poisk" type="text" '
        'placeholder="Выберите параграф" autocomplete="off" '
        'oninput="return shkPoiskParagraf(this.value)" '
        'onkeydown="return shkPoiskKlavesa(event)">'
        '<a class="nastr-krestik" id="nastr-krestik" href="#" hidden '
        'aria-label="Снять ограничение" '
        'onclick="return shkSnyatOgranichenie()">' + _tv.ikona('закрыть') +
        '</a></span>'
        '<div class="nastr-naydennoe" id="nastr-naydennoe" hidden></div>'
        '</div>'
        '</div>'
        # Одна настройка прохождения: переходить к следующему вопросу
        # автоматически при верном ответе. Заголовка у неё нет — строка
        # говорит сама за себя, а лишняя надпись только отодвигала её
        # вниз. По умолчанию галочка снята: решение идёт в своём темпе,
        # и решение об этом — за человеком.
        '<a class="nastr-stroka" id="nastr-avto" href="#" '
        'onclick="return shkAvto()">'
        '<span class="nastr-galochka">' + _tv.ikona('галочка') + '</span>'
        '<span class="nastr-tekst">Переходить к следующему вопросу '
        'автоматически</span>'
        '</a>'
        '</div>'
        # Сброс результатов — внизу панели, у самого нижнего края
        # экрана: редкое действие, и случайно его не нажать. Вне
        # прокручиваемого списка: сколько бы настроек ни набралось, он
        # остаётся на месте. Подтверждение — повторным нажатием
        # (см. shkSbrosit): сначала кнопка предупреждает, потом стирает.
        '<div class="panel-niz">'
        '<a class="knopka-malaya" id="trener-sbros" href="#" '
        'onclick="return shkSbrosit()">Сбросить результаты теста</a>'
        '</div></aside>'
        '<div class="panel-tyanulka pleylista" tabindex="0" '
        'role="separator" aria-orientation="vertical" '
        'aria-label="Изменить ширину" '
        'onkeydown="return shkTyan(event)"></div>')

    return stranica + niz + js, panel


def slov_paragrafov(paragrafy):
    """Параграфы для скрипта: код, место в курсе, номер и тема."""
    itog = []
    for i, par in enumerate(paragrafy, start=1):
        itog.append({'k': par['kod'], 'm': i, 'n': par['nomer'],
                     't': _tv.myagkie(par['nazvanie']),
                     'u': par['uchebnik'],
                     'v': par['даты'] + par['определения']})
    return json.dumps(itog, ensure_ascii=False, indent=1)


def slov_voprosov(dannye, paragrafy):
    """Вопросы для скрипта: чем спрашиваем, что отвечать и чей параграф.

    Даты — [когда, событие, параграф], определения — [термин, значение,
    параграф]. Ключ параграфа пустой, если привязка не нашлась: такие
    вопросы в суженный курс не попадают (см. привязать_параграфы.py).
    """
    daty = [[d['когда'], d['событие'], d.get('paragraf', ''),
             d.get('учебник', ''), d.get('страница', '')]
            for d in dannye['даты']]
    opred = [[o['термин'], o['значение'], o.get('paragraf', ''),
              o.get('учебник', ''), o.get('страница', '')]
             for o in dannye['определения']]
    return json.dumps({'daty': daty, 'opredeleniya': opred},
                      ensure_ascii=False, indent=1)


JS_TRENAZHERA = """<script>
(function(){
  /* Настройки тренажёра, вопросы и движок решения. Подставлено при сборке —
     см. gen_tv_trenazher.py. Вопросы лежат здесь же: страница едет на
     флешке, взять их больше негде.

     Как идёт решение. Настройки выбирают набор вопросов, «Начать»
     перемешивает его и ведёт по всем вопросам подряд: вопрос, четыре
     варианта, отзыв, «Дальше». Заходов и порций нет — ни «сколько за
     раз», ни остановок между ними: набор один, и он идёт до конца,
     а ребёнок бросает тогда, когда захочет. Ошибки живут дольше —
     вопрос уходит из списка ошибок только тогда, когда на него
     ответили верно.

     Каждый вопрос задаётся с двух сторон, и стороны чередуются:
     «событие → год», потом «год → событие»; у определений — «термин →
     значение», потом «значение → термин». Год, к которому в базе
     привязано два события, спрашиваем только со стороны события: у
     вопроса «что было в 1534 году?» было бы два верных ответа.

     Неверные варианты подбираются ближними по смыслу: у дат — соседние
     годы, у определений — слова из того же или ближнего параграфа.
     Дальние подсказывали бы ответ самим своим видом. */
  var VIDY = {TRENERY};
  var PARAGRAFY = {PARAGRAFY};
  /* Кольцо выбора и подпись «Работа над ошибками» — из самой сборки:
     те же знаки, что в панели и под полем. */
  var KOLCO = '{KOLCO}';
  var OSHIBSKI = '{OSHIBSKI}';
  var VOPROSY = {VOPROSY};

  var MESTO = {};
  /* Параграф по коду: отзыву нужны его номер и тема — «§ 23. Правление
     Ивана IV Грозного», чтобы было понятно, где об этом прочитать. */
  var PAR_PO_KODU = {};
  for(var i = 0; i < PARAGRAFY.length; i++){
    MESTO[PARAGRAFY[i].k] = PARAGRAFY[i].m;
    PAR_PO_KODU[PARAGRAFY[i].k] = PARAGRAFY[i];
  }

  /* Все вопросы одним списком: [ключ, вид, параграф, что спрашиваем,
     что отвечать]. */
  var VSE = [];
  (function(){
    var d = VOPROSY.daty, o = VOPROSY.opredeleniya;
    for(var i = 0; i < d.length; i++){
      VSE.push({k:'d'+i, vid:'daty', par:d[i][2], sprash: d[i][0],
                otvet: d[i][1], uchebnik: d[i][3] || '', str: d[i][4] || ''});
    }
    for(var j = 0; j < o.length; j++){
      VSE.push({k:'o'+j, vid:'opredeleniya', par:o[j][2], sprash: o[j][0],
                otvet: o[j][1], uchebnik: o[j][3] || '', str: o[j][4] || ''});
    }
  })();

  /* Что выбрано сейчас. Так же называется и то, что прочитает движок:
     shkNastroykiState(). Учебник — короткое имя книги («История России»,
     «Всеобщая история»); пусто — весь курс, то есть обе книги. */
  var NASTR = {vid:'vse', par:'', uch:'', avto:false};
  /* Ошибки — ключи вопросов, где ошибался. Ни смена настроек, ни смена
     набора их не стирают: список ошибок уходит только по верному
     ответу. */
  var OSHIBKI = {};
  var OSHIBKI_BIL = false;
  /* Что отвечено за эту сессию: ключ вопроса → 'verno' или 'oshibka' —
     как ответили в последний раз. По этим отметкам считаются «пройдено»,
     «верно» и «ошибок» под полем. Смена набора отметки не стирает: это
     движение по курсу, а не счёт одного прохождения. */
  var SOSTOYANIE = {};
  /* Текущее решение: набор вопросов, место в нём и ответы. Null —
     ещё не начато. */
  var ZAHOD = null;
  /* Ссылка на страницу видеоуроков: отзыв ведёт по ней на урок того
     параграфа, о котором вопрос. Пустая строка — видеоуроков у предмета
     нет, и ссылки тоже не будет. Подставляет сборка. */
  var SSYLKA_VIDEO = '{SSYLKA_VIDEO}';
  /* Параграфы, по которым есть видеоурок: метки пунктов на странице
     видеоуроков (см. _tv.blok_playera). Ссылка «смотреть видео» ведёт
     только туда, где урок есть: видео записано не по всему курсу, а
     ссылка в пустоту хуже её отсутствия. */
  var S_VIDEO = {S_VIDEO};

  /* Строка настроек над кадром — она же заголовок страницы: что
     тренируем, по какому учебнику и до какого параграфа. Пустое место
     занимает «Весь курс» — так же называется и строка в настройках;
     параграф приписываем только выбранный. */
  function stroka_nastroek(){
    var ch = [VIDY[NASTR.vid].zag, NASTR.uch || 'Весь курс'];
    /* У параграфа в надписи — только номер: тема бывает на две строки
       («Введение опричнины…»), и название настройки превращалось бы
       в абзац. Тема стоит в строке настроек, там ей и место. */
    if(NASTR.par && PAR_PO_KODU[NASTR.par]){
      ch.push('до § ' + PAR_PO_KODU[NASTR.par].n);
    }
    return ch.join(' · ');
  }

  /* Номер параграфа — в метку пункта: «§ 10–11» → «10-11». Ровно то же
     делает _tv при разметке плейлиста. */
  function metka_paragrafa(nomer){
    return String(nomer).replace(/§/g, '').replace(/[–—]/g, '-')
      .replace(/\\s+/g, '').trim();
  }
  function est_video(par){
    return !!SSYLKA_VIDEO && !!par &&
      S_VIDEO.indexOf(metka_paragrafa(par.n)) >= 0;
  }
  /* Какой стороной спрашивать в следующий раз: 0 — «событие → год» и
     «термин → значение», 1 — наоборот. */
  var NAPR = {daty: 0, opredeleniya: 0};

  /* Галочка верного ответа — та же иконка, что у флажка в настройках
     (см. _tv.IKONY['галочка']), чтобы знак был один на всё приложение. */
  /* Шеврон — у ссылки «Подробнее»: он же стоит у строки параграфа
     в настройках и показывает, что строка раскрывается. */
  var SHEVRON = '{SHEVRON}';
  /* Стрелки листания по вопросам — те же знаки, что у стрелок полосы
     плашек и у поворотов браузера: назад и вперёд. */
  var STRELKA_NAZAD = '{STRELKA_NAZAD}';
  var STRELKA_VPERED = '{STRELKA_VPERED}';

  var GALKA = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" ' +
    'aria-hidden="true"><path d="M5.5 12.5l4.6 4.6L18.8 7.4"/></svg>';

  /* Элементы ищем при каждом показе, а не один раз при загрузке: скрипт
     стоит в странице раньше панели, и её строк при загрузке ещё нет —
     выбранное на панели просто не отражалось бы в поле. */
  function elem(id){ return document.getElementById(id); }

  /* Панель во всю ширину экрана сама не открывается: на телефонах и
     вертикальном планшете она заняла бы весь экран вместо поля — там её
     вызывает кнопка настроек. Правило то же, что у видеоуроков. */
  if(window.innerWidth < MENYU-VO-VSYU){
    document.body.classList.remove('pleylist-otkryto');
  }

  function vsego(){
    return VOPROSY.daty.length + VOPROSY.opredeleniya.length;
  }

  /* Подходит ли вопрос под настройки. Работа над ошибками — тот же
     фильтр поверх остальных: вид вопроса не смотрим, а ошибки — смотрим. */
  function podhodit(v){
    if(NASTR.vid === 'daty' && v.vid !== 'daty'){ return false; }
    if(NASTR.vid === 'opredeleniya' && v.vid !== 'opredeleniya'){ return false; }
    if(NASTR.vid === 'oshibki' && !OSHIBKI[v.k]){ return false; }
    if(NASTR.uch && v.uchebnik !== NASTR.uch){ return false; }
    if(NASTR.par){
      /* «Весь курс» значит «с начала и до этого параграфа»: позже
         пройденного спрашивать нечего — его ещё не проходили. */
      if(!v.par){ return false; }
      if(MESTO[v.par] > MESTO[NASTR.par]){ return false; }
    }
    return true;
  }

  function naydeno(){
    var itog = [];
    for(var i = 0; i < VSE.length; i++){
      if(podhodit(VSE[i])){ itog.push(VSE[i]); }
    }
    return itog;
  }

  function OSHIBSKI_KEYS(){
    var kk = [];
    for(var k in OSHIBKI){
      if(OSHIBKI.hasOwnProperty(k)){ kk.push(k); }
    }
    return kk;
  }

  /* Проверка читает настройки и набор отсюда: у страницы нет другого
     способа показать, что у неё внутри. */
  window.shkUroki = function(){ return naydeno(); };
  window.shkNastroykiState = function(){
    return {vid:NASTR.vid, paragraf:NASTR.par, uchebnik:NASTR.uch,
            avto:NASTR.avto, oshibki:OSHIBSKI_KEYS()};
  };
  /* Состояние решения для проверок: у страницы нет другого способа
     показать, что у неё внутри. */
  window.shkZahodSostoyanie = function(){
    if(!ZAHOD){ return null; }
    var q = ZAHOD.vopros || {};
    var varianty = [], verny = -1;
    if(q.varianty){
      for(var i = 0; i < q.varianty.length; i++){
        varianty.push(q.varianty[i].tekst);
        if(q.varianty[i].verno){ verny = i; }
      }
    }
    return {nomer: ZAHOD.i + 1, vsego: ZAHOD.spisok.length,
            verno: ZAHOD.verno, otvecheno: ZAHOD.otvecheno,
            oshibok: ZAHOD.oshibok, konec: !!ZAHOD.konec,
            otvechen: ZAHOD.otvechen, varianty: varianty, verny: verny,
            podskazka: q.podskazka || '', vopros: q.chto || '',
            polny: q.polny || '', klyuch: ZAHOD.spisok[ZAHOD.i].k,
            par: ZAHOD.spisok[ZAHOD.i].par || '',
            uchebnik: ZAHOD.spisok[ZAHOD.i].uchebnik || ''};
  };

  function imya_paragrafa(kod){
    for(var i = 0; i < PARAGRAFY.length; i++){
      if(PARAGRAFY[i].k === kod){
        return '§ ' + PARAGRAFY[i].n + '. ' + PARAGRAFY[i].t;
      }
    }
    return '';
  }

  /* ---- сборка вопроса ---- */

  function peremeshat(spisok){
    for(var i = spisok.length - 1; i > 0; i--){
      var j = Math.floor(Math.random() * (i + 1));
      var t = spisok[i]; spisok[i] = spisok[j]; spisok[j] = t;
    }
    return spisok;
  }

  /* Вопрос из базы — это подпись события («попытка Лжедмитрия II захватить
     власть…»), и в базе она строчными. Вопрос с маленькой буквы читается
     как обрывок строки, поэтому первую букву поднимаем. */
  function s_zaglavnoy(s){
    s = String(s);
    return s.charAt(0).toUpperCase() + s.slice(1);
  }

  function god(kogda){
    var m = String(kogda).match(/[0-9]{3,4}/);
    return m ? parseInt(m[0], 10) : 0;
  }

  function mesto(v){ return MESTO[v.par] || 0; }

  /* Сколько вопросов просят тот же год: если больше одного, «что было
     в этом году?» — вопрос с двумя верными ответами. */
  function za_god(kogda){
    var n = 0;
    for(var i = 0; i < VSE.length; i++){
      if(VSE[i].vid === 'daty' && VSE[i].sprash === kogda){ n++; }
    }
    return n;
  }

  /* Варианты-обманки, ближние вперёд. `kakie` говорит, что именно
     предлагаем: годы, события, значения или термины. Первый по каждому
     тексту остаётся, повторы дальше отпадают: два одинаковых варианта
     в списке — это не выбор. */
  function kandidaty(v, kakie){
    var itog = [], videno = {};
    for(var i = 0; i < VSE.length; i++){
      var x = VSE[i];
      if(x.vid !== v.vid || x === v){ continue; }
      var tekst, m;
      if(kakie === 'gody'){
        if(x.sprash === v.sprash){ continue; }
        tekst = x.sprash;
        m = Math.abs(god(x.sprash) - god(v.sprash));
      } else if(kakie === 'sobytiya'){
        if(x.sprash === v.sprash || x.otvet === v.otvet){ continue; }
        tekst = x.otvet;
        m = Math.abs(mesto(x) - mesto(v));
      } else if(kakie === 'znacheniya'){
        if(x.otvet === v.otvet){ continue; }
        tekst = x.otvet;
        m = Math.abs(mesto(x) - mesto(v));
      } else {
        if(x.sprash === v.sprash){ continue; }
        tekst = x.sprash;
        m = Math.abs(mesto(x) - mesto(v));
      }
      itog.push({tekst: tekst, m: m});
    }
    itog.sort(function(a, b){ return a.m - b.m; });
    var redkie = [];
    for(var j = 0; j < itog.length; j++){
      if(!videno[itog[j].tekst]){
        videno[itog[j].tekst] = true;
        redkie.push(itog[j]);
      }
    }
    return redkie;
  }

  /* Год пишем по-человечески: с разделением тысяч точкой и со словом
     «год» — «1.552 г.», а у промежутка «1.607—1.610 гг.». Иначе в списке
     ответов стояли голые цифры, и глаз спотыкался. Трогаем только те
     строки, что целиком год или промежуток годов: в названии события
     («Соборное уложение 1649 г.») цифры уже в своей фразе. */
  /* Разряды года разделяем пробелом — так пишут цены: «1 679». Точка
     («1.679») читалась как десятичная, и год выглядел дробью. Пробел
     нерушимый: год не должен разрываться по строке. Всё, кроме цифр
     (пробелы вокруг тире, сам знак), отбрасываем: сюда приходят части
     уже готового промежутка. */
  function razryad(chislo){
    var s = String(chislo).replace(/[^0-9]/g, ''), itog = '', n = 0;
    for(var i = s.length - 1; i >= 0; i--){
      itog = s.charAt(i) + itog;
      n++;
      if(n % 3 === 0 && i > 0){ itog = '\u00a0' + itog; }
    }
    return itog;
  }
  function eto_god(t){
    return /^[0-9]{3,4}$/.test(t) ||
           /^[0-9]{3,4}\\s*[—–-]\\s*[0-9]{3,4}$/.test(t);
  }
  /* Промежуток годов — коротким тире с пробелами: «1 607 – 1 610 гг.».
     Так знак отделён от цифр, и видно, что это промежуток, а не одно
     длинное число (см. правило тире на всю сборку). */
  function s_godom(s){
    var t = String(s).replace(/^[ \u00a0]+|[ \u00a0]+$/g, '');
    if(!eto_god(t)){ return String(s); }
    var ch = t.split(/[—–-]/);
    if(ch.length === 1){ return razryad(ch[0]) + ' г.'; }
    return razryad(ch[0]) + ' \u2013 ' + razryad(ch[1]) + ' гг.';
  }

  /* Слов «Дата» и «Определение» над вопросом нет: заголовком стоит
     сам вопрос — событие или значение, — а как его решать, сказано
     подзаголовком: «Когда это было?», «Как это называется?». */

  function sobran_vopros(v){
    var storona = NAPR[v.vid] ? 1 : 0;
    if(v.vid === 'daty' && storona === 1 && za_god(v.sprash) > 1){
      storona = 0;
    }
    NAPR[v.vid] = storona ? 0 : 1;

    var chto, podskazka, verny, drugie, polny;
    if(v.vid === 'daty'){
      if(storona === 0){
        chto = v.otvet; podskazka = 'Когда это было?'; verny = v.sprash;
        drugie = kandidaty(v, 'gody');
      } else {
        chto = v.sprash; podskazka = 'Что это за время?';
        verny = v.otvet; drugie = kandidaty(v, 'sobytiya');
      }
      polny = v.otvet + ' — ' + v.sprash;
    } else {
      if(storona === 0){
        chto = v.sprash; podskazka = 'Что это значит?'; verny = v.otvet;
        drugie = kandidaty(v, 'znacheniya');
      } else {
        chto = v.otvet; podskazka = 'Как это называется?';
        verny = v.sprash; drugie = kandidaty(v, 'terminy');
      }
      polny = v.sprash + ' — ' + v.otvet;
    }
    /* И вопрос, и варианты ответов — с заглавной буквы: события в базе
       записаны строчными, а вопрос со строчной буквы читается как
       обрывок строки. */
    chto = s_zaglavnoy(chto);
    verny = s_zaglavnoy(verny);

    /* Три ближайших — но не всегда одни и те же три: из восьми соседей
       берём случайные. Иначе к одной дате всегда предлагались бы те же
       самые годы, и ответ запоминался бы по списку, а не по времени. */
    var varianty = [{tekst: verny, verno: true}];
    var blizkie = peremeshat(drugie.slice(0, 8));
    for(var i = 0; i < blizkie.length && varianty.length < 4; i++){
      varianty.push({tekst: s_zaglavnoy(blizkie[i].tekst), verno: false});
    }
    /* Соседей не хватило (курс сужен до одного параграфа) — добираем из
       остальных: обманка может прийти откуда угодно, лишь бы не совпала. */
    for(var j = 3; j < drugie.length && varianty.length < 4; j++){
      var povtor = false;
      for(var k = 0; k < varianty.length; k++){
        if(varianty[k].tekst === drugie[j].tekst){ povtor = true; }
      }
      if(!povtor){
        varianty.push({tekst: s_zaglavnoy(drugie[j].tekst), verno: false});
      }
    }
    peremeshat(varianty);
    /* Годы показываем в человеческом виде: и когда спрашиваем годом
       («Что это за время?»), и когда годы стоят ответами. */
    if(v.vid === 'daty'){
      if(storona === 1){ chto = s_godom(chto); }
      else {
        for(var i = 0; i < varianty.length; i++){
          varianty[i].tekst = s_godom(varianty[i].tekst);
        }
      }
      /* Год стоит в подсказке с любой из сторон: «год — событие»
         и «событие — год». Пройдём по частям и оформим ту, которая
         и есть год. */
      var chasti_polnogo = String(polny).split(' — ');
      var pereobrali = false;
      for(var c = 0; c < chasti_polnogo.length; c++){
        if(eto_god(chasti_polnogo[c])){
          chasti_polnogo[c] = s_godom(chasti_polnogo[c]);
          pereobrali = true;
        }
      }
      if(pereobrali){ polny = chasti_polnogo.join(' — '); }
    }
    return {chto: chto, podskazka: podskazka, varianty: varianty,
            polny: polny};
  }

  /* Вопрос набора. К отвеченному вопросу можно вернуться кнопкой
     «Предыдущий»: тогда показываем его же (те же варианты, тот же ответ
     и отзыв), а не собираем новый — иначе возврат стирал бы результат.
     Что уже отвечено, лежит в ZAHOD.otvety по ключу вопроса. */
  function sdelat_vopros(){
    var spisok = ZAHOD.spisok;
    var klyuch = spisok[ZAHOD.i].k;
    var byl = ZAHOD.otvety[klyuch];
    if(byl){
      ZAHOD.vopros = byl.vopros;
      ZAHOD.otvechen = byl.otvechen;
      /* Подсказку к отвеченному вопросу показываем в том же виде,
         в каком её оставили: раскрытой или свёрнутой. */
      ZAHOD.podskazka = false;
      /* К отвеченному вопросу возвращаются затем, чтобы посмотреть свой
         ответ и отзыв, — их и показываем. */
      ZAHOD.prokrutit = 'niz';
      return;
    }
    ZAHOD.vopros = sobran_vopros(spisok[ZAHOD.i]);
    ZAHOD.otvechen = null;
    /* Куда поставить поле: новый вопрос показываем с начала, а после
       ответа — с конца, где отзыв и «Дальше». Иначе ответ на длинном
       определении прокручивал вопрос за верхний край, и его приходилось
       искать. */
    ZAHOD.prokrutit = 'verh';
  }

  /* ---- разметка поля ---- */

  function ekran(s){
    return String(s === null || s === undefined ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  /* Искры вокруг галочки: короткий салют, только при верном ответе. */
  function iskry(){
    var html = '<span class="trener-iskry">';
    for(var i = 0; i < 10; i++){
      var u = (i / 10) * Math.PI * 2;
      var r = 24 + (i % 3) * 10;
      html += '<i style="--x:' + Math.round(Math.cos(u) * r) + 'px;--y:' +
        Math.round(Math.sin(u) * r) + 'px"></i>';
    }
    return html + '</span>';
  }

  /* Строка управления — внизу поля: листание слева, «Работа над
     ошибками» и «Дальше» справа. Кнопки маленькие: это листание, а не
     главное действие. «Дальше» — у самого правого угла поля.
     «Следующий вопрос» тут не нужен: он и есть «Дальше», а две кнопки
     про одно только сбивали с толку. «Завершить» тоже нет: бросить
     можно в любой момент, ответы от этого не теряются, а итог и так
     показывается, когда вопросы кончились. */
  /* Стрелка листания — кнопка со значком. Без хода это не ссылка, а
     серая надпись: ссылка в никуда обещала бы переход. Назад хода нет
     на первом вопросе, вперёд — пока не отвечено. */
  function strelka(id, dejstvie, tuskly, nazvanie, znak){
    if(tuskly){
      return '<span class="trener-strelka tuskly" id="' + id +
        '" aria-disabled="true" aria-label="' + nazvanie + '">' + znak +
        '</span>';
    }
    return '<a class="trener-strelka" id="' + id + '" href="#" aria-label="' +
      nazvanie + '" onclick="return ' +
      dejstvie + '">' + znak + '</a>';
  }

  /* Нижняя строка поля: счёт ошибок и стрелки листания. На странице
     «Работа над ошибками» стоит под полем, а в полном экране встаёт
     сюда, в один ряд со стрелками — слева, а стрелки справа. Кнопки
     ошибок нет, пока ошибок нет (см. oshibki_knopka): без неё строка —
     одни стрелки. Пустой заход строки не имеет вовсе (итог — своя
     разметка, см. razmetka_itoga). */
  function upravlenie(){
    var z = ZAHOD;
    if(!z || z.konec){ return ''; }
    var posl = z.i + 1 >= z.spisok.length;
    return '<div class="trener-upravlenie">' +
      /* Полоса времени — у нижнего края поля, в одной строке со
         стрелками: длинная дорожка, которую жёлтая полоса наполняет
         ровно за минуту и начинает заново (см. vremya_* ниже). */
      '<span class="trener-vremya" id="trener-vremya">' +
      '<span class="trener-vremya-podpis" id="trener-vremya-podpis">' +
      '00:00</span></span>' +
      '<span class="trener-oshibki-v-pole"></span>' +
      '<span class="trener-strelki">' +
      strelka('trener-nazad', 'shkShagnut(-1)', z.i === 0,
              'Предыдущий вопрос', STRELKA_NAZAD) +
      strelka('trener-vpered', 'shkDalshe()', z.otvechen === null,
              posl ? 'Показать итог' : 'Следующий вопрос', STRELKA_VPERED) +
      '</span></div>';
  }

  /* ---- полоса времени: минута за минутой ----
     Дорожка у нижнего края поля наполняется ровно за минуту и, когда
     минута прошла, начинается заново. Это не счёт и не скорость: по
     полосе видно, сколько идёт нынешняя минута, — она подсказывает темп,
     а не гонит. Живёт полоса с заходом: начали решать — пошла, кончили
     (итог или сброс) — стала.
     Доля считается от времени, а не шагами таймера: если браузер
     придержит кадры, полоса не отстанет. Минуты идут кругом, поэтому
     у большой разницы берётся остаток — это и есть «сброс и заново». */
  var VREMYA_CIKL = 60000;
  var VREMYA_OT = 0;
  var VREMYA_IDYOT = false;
  var VREMYA_ZAPOLNENA = false;
  var VREMYA_OSTANOVLENA = false;
  function vremya_dolya(ot, seychas){
    var d = (seychas - ot) / VREMYA_CIKL;
    return d < 0 ? 0 : d;
  }
  function vremya_pokazat_tekst(dolya){
    var s = Math.max(0, Math.floor(dolya * VREMYA_CIKL));
    var min = Math.floor(s / 60000), sek = Math.floor((s % 60000) / 1000);
    var p = elem('trener-vremya-podpis');
    if(p){
      p.textContent = String(min).padStart(2, '0') + ':' +
        String(sek).padStart(2, '0');
    }
  }
  function vremya_narisovat(){
    var d = VREMYA_ZAPOLNENA ? 1 :
      vremya_dolya(VREMYA_OT, Date.now());
    var p = elem('trener-vremya-polosa');
    if(p){ p.style.width = (d * 100).toFixed(2) + '%'; }
    vremya_pokazat_tekst(d);
  }
  function vremya_kadr(){
    if(!VREMYA_IDYOT){ return; }
    vremya_narisovat();
    window.requestAnimationFrame(vremya_kadr);
  }
  function vremya_pustit(){
    if(VREMYA_IDYOT || VREMYA_ZAPOLNENA || VREMYA_OSTANOVLENA){ return; }
    VREMYA_IDYOT = true;
    vremya_kadr();
  }
  /* Новый вопрос — новая минута. */
  function vremya_snachala(){
    VREMYA_OT = Date.now();
    VREMYA_ZAPOLNENA = false;
    VREMYA_OSTANOVLENA = false;
    vremya_narisovat();
    vremya_pustit();
  }
  /* Нажали ответ — часы останавливаются на фактическом времени ответа. */
  function vremya_zavershit(){
    VREMYA_IDYOT = false;
    VREMYA_ZAPOLNENA = false;
    VREMYA_OSTANOVLENA = true;
    vremya_narisovat();
  }
  window.shkVremyaSostoyanie = function(){
    return {cikl: VREMYA_CIKL, idyot: VREMYA_IDYOT,
            zapolnena: false,
            dolya: VREMYA_ZAPOLNENA ? 1 :
              vremya_dolya(VREMYA_OT, Date.now())};
  };
  window.shkVremyaDolya = vremya_dolya;

  /* Подсказка — вместо прежнего отзыва. Слов «Верно!» и повтора
     выбранного ответа нет: верный вариант виден по зелёной рамке.
     Рассказ о событии (так, как он записан в учебнике) и место, где
     о нём прочитать — параграф, страница и ссылка на видеоурок —
     открываются в окне по значку вопроса в верхней строке поля.
     Кнопка живёт, только когда ответ уже дан: до ответа подсказка
     выдала бы верный вариант. */
  function telo_podskazki(q){
    var v = ZAHOD.spisok[ZAHOD.i];
    var par = PAR_PO_KODU[v.par] || null;
    var mesta = [];
    if(v.uchebnik){
      mesta.push('«' + ekran(v.uchebnik) + '»' +
                 (v.str ? ', стр. ' + ekran(v.str) : ''));
    }
    if(par){
      mesta.push('§ ' + ekran(par.n) + '. ' + ekran(par.t));
    }
    var html = '<p class="trener-poln">' + ekran(q.polny) + '</p>' +
      '<div class="trener-podrobno"><span>' + mesta.join(' · ') + '</span>';
    if(est_video(par)){
      html += '<a class="trener-video" href="' + SSYLKA_VIDEO + '#par-' +
        metka_paragrafa(par.n) + '">Смотреть видео по § ' +
        ekran(par.n) + '</a>';
    }
    return html + '</div>';
  }

  /* Сколько столбцов у ответов. Короткие (годы, термины) стоят плашками
     по ширине поля — по две в ряд, и четыре ответа ложатся двумя
     ровными рядами по два. Длинные (значения определений) идут в один
     столбец: в две колонки они не влезают и обрезаются. Столбцов всегда
     чётное число, поэтому ряды сверху и снизу одинаковые. Смотрим на
     САМЫЙ ДЛИННЫЙ ответ: по нему и видно, влезут ли два в ряд. */
  function klass_otvetov(q){
    var d = 0;
    for(var i = 0; i < q.varianty.length; i++){
      var s = String(q.varianty[i].tekst || '').length;
      if(s > d){ d = s; }
    }
    if(d <= 16){ return 'v-korotkie'; }
    return d <= 64 ? 'v-ryad' : 'v-stolbik';
  }

  function razmetka_voprosa(){
    var z = ZAHOD;
    if(z.konec){ return razmetka_itoga(); }
    var q = z.vopros;
    /* Задание — вопрос и ответы — стоит одной колонкой во всю ширину
       поля; стрелки листания живут в нижней строке поля (см.
       upravlenie), у правого нижнего угла. */
    var html = '<div class="trener-forma">' +
      /* Заголовком — сам вопрос: событие («Отмена мясничества») или
         значение («форма монархического правления…»). Подзаголовком —
         словами: «Когда это было?», «Как это называется?». Слов «Дата»
         и «Определение» здесь нет. */
      '<div class="trener-vopros-blok">' +
      '<span class="trener-vopros-zag">' + ekran(q.chto) +
      '</span></div>' +
      '<div class="trener-otvety ' + klass_otvetov(q) + '">';
    for(var i = 0; i < q.varianty.length; i++){
      var o = q.varianty[i];
      var klass = 'trener-otvet';
      if(z.otvechen !== null){
        if(o.verno){ klass += ' pokazat'; }
        if(z.otvechen === i){ klass += o.verno ? ' verno' : ' neverno'; }
      }
      /* Искры — вокруг галочки того ответа, который выбрали верно:
         награда за ответ, а не украшение страницы. */
      var iskra = (z.otvechen === i && o.verno) ? iskry() : '';
      html += '<a class="' + klass + '" href="#" data-n="' + i +
        '" onclick="return shkOtvet(this)">' +
        '<span class="trener-nomerok">' + (i + 1) + '</span>' +
        '<span class="trener-tekst-otveta">' + ekran(o.tekst) + '</span>' +
        '<span class="trener-galka">' + GALKA + iskra + '</span></a>';
    }
    html += '</div></div>';
    html += upravlenie();
    return html;
  }

  /* Итог. Заходов нет: вопросы идут подряд, и когда они кончились —
     вот итог; он ничего не запирает и ни к чему не зовёт. «Ещё захода»
     здесь потому и нет: пройти набор заново — это сброс результатов
     в настройках, и он честно стирает и пройденное, и ошибки. Если
     ошибки есть, единственный ход отсюда — работа над ними. */
  function razmetka_itoga(){
    var z = ZAHOD;
    var vsego_z = z.spisok.length;
    var html = '<p class="trener-vopros">Все вопросы пройдены</p>' +
      '<span class="trener-chto">Верно ' + z.verno + ' из ' + vsego_z +
      (z.oshibok ? ' · ошибок ' + z.oshibok : ' · ни одной ошибки') +
      '</span>';
    var kk = OSHIBSKI_KEYS().length;
    if(kk){
      html += '<div class="trener-knopki">' +
        '<a class="knopka" href="#" onclick="return shkOshibki()">' +
        'Работа над ошибками (' + kk + ')</a></div>';
    }
    return html;
  }

  /* ---- ход решения ---- */

  window.shkNachat = function(){
    var spisok = naydeno();
    if(!spisok.length){ return false; }
    spisok = peremeshat(spisok.slice());
    ZAHOD = {spisok: spisok, i: 0, verno: 0, oshibok: 0, otvecheno: 0,
             otvechen: null, konec: false, vopros: null, otvety: {},
             podskazka: false};
    NAPR = {daty: 0, opredeleniya: 0};
    /* Заход начался — минута у полосы времени пойдёт с нуля. */
    vremya_snachala();
    sdelat_vopros();
    shkStatistika({oshibki: OSHIBSKI_KEYS()});
    pokazat();
    return false;
  };

  window.shkOtvet = function(a){
    if(!ZAHOD || ZAHOD.konec || ZAHOD.otvechen !== null){ return false; }
    var n = parseInt(a.getAttribute('data-n'), 10);
    var q = ZAHOD.vopros;
    if(!q || !q.varianty[n]){ return false; }
    ZAHOD.otvechen = n;
    ZAHOD.otvecheno++;
    var klyuch = ZAHOD.spisok[ZAHOD.i].k;
    /* На ответ ничего не раскрывается: подсказка живёт в окне и открывается
       значком вопроса из верхней строки. Поле остаётся на месте — ответ
       виден и так, зелёной или красной рамкой. */
    ZAHOD.prokrutit = '';
    /* Запоминаем вопрос и ответ: к этому вопросу можно вернуться
       «Предыдущим» — там будет он же, с тем же ответом. */
    ZAHOD.otvety[klyuch] = {vopros: q, otvechen: n};
    if(q.varianty[n].verno){
      ZAHOD.verno++;
      delete OSHIBKI[klyuch];
      SOSTOYANIE[klyuch] = 'verno';
    } else {
      ZAHOD.oshibok++;
      OSHIBKI[klyuch] = true;
      OSHIBKI_BIL = true;
      SOSTOYANIE[klyuch] = 'oshibka';
    }
    /* Любой выбранный ответ — правильный или ошибочный — останавливает
       часы на фактическом времени выбора. */
    vremya_zavershit();
    /* Статистика под полем — из тех же отметок: отдельного счёта нет.
       shkStatistika() сама перерисует поле, поэтому второй раз pokazat()
       не зовём. */
    shkStatistika({oshibki: OSHIBSKI_KEYS()});
    /* Фокус на стрелку вперёд — чтобы пульт и Enter работали сразу, но
       без прокрутки: прокруткой распоряжается сам движок (см. его
       pokazat). */
    var d = elem('trener-vpered');
    if(d && d.focus && d.tagName === 'A'){
      try{ d.focus({preventScroll:true}); }
      catch(e){ try{ d.focus(); }catch(e2){} }
    }
    /* «Переходить к следующему вопросу сам»: включено — через мгновение
       открываем следующий. Мгновение нужно, чтобы увидеть и зелёный
       ответ, и кристалл; а если человек за это время сам куда-то ушёл
       (ответил иначе, вернулся назад), перехода не будет. */
    if(NASTR.avto && q.varianty[n].verno){
      var byl_nomer = ZAHOD.i, byl_otvet = n;
      window.setTimeout(function(){
        if(ZAHOD && !ZAHOD.konec && ZAHOD.i === byl_nomer &&
           ZAHOD.otvechen === byl_otvet){ shkDalshe(); }
      }, 900);
    }
    return false;
  };

  /* Листание по вопросам: ответы и баллы остаются на месте — к любому
     вопросу можно вернуться и посмотреть свой ответ с отзывом. */
  window.shkShagnut = function(na){
    if(!ZAHOD || ZAHOD.konec){ return false; }
    var i = ZAHOD.i + (na || 0);
    if(i < 0 || i >= ZAHOD.spisok.length){ return false; }
    ZAHOD.i = i;
    /* Назад — полоса полная и неподвижная: это отметка возврата,
       а не продолжение времени прежнего вопроса. */
    vremya_zavershit();
    sdelat_vopros();
    pokazat();
    return false;
  };

  /* Esc закрывает сперва окно подсказки и полный экран, а уж потом
     панель (см. общий обработчик в _tv.py). Слушаем в перехвате: иначе
     вместе с окном закрылись бы и настройки. */
  document.addEventListener('keydown', function(e){
    if(e.key !== 'Escape'){ return; }
    var okno = elem('trener-okno-podskazki');
    if(okno && okno.className.indexOf('vidno') >= 0){
      if(e.stopPropagation){ e.stopPropagation(); }
      shkPodskazkaZakryt();
      return;
    }
    if(document.body.classList.contains('trener-vo-ves-ekran')){
      if(e.stopPropagation){ e.stopPropagation(); }
      shkVoVesEkranZakryt();
    }
  }, true);
  /* Окно и полный экран стоят на месте поля — при прокрутке, повороте
     экрана и изменении окна место пересчитываем. */
  window.addEventListener('resize', function(){ postavit_okno(); });
  window.addEventListener('scroll', function(){
    var okno = elem('trener-okno-podskazki');
    if(okno && okno.className.indexOf('vidno') >= 0){ postavit_okno(); }
  });

  /* Окно подсказки: встаёт на то же место и того же размера, что экран
     теста, — считаем его прямоугольник и переносим в окно. На телефоне
     (узкий экран) окно занимает всю ширину экрана. Закрывается
     крестиком, Esc и нажатием по подложке. */
  function postavit_okno(){
    var okno = elem('trener-okno-podskazki');
    var karta = elem('trener-okno-karta');
    var mesto = elem('pleyer-mesto');
    if(!okno || !karta || !mesto){ return; }
    var r = mesto.getBoundingClientRect();
    var uzkij = window.innerWidth < 640 || r.width < 420;
    if(uzkij){
      karta.style.left = '0px';
      karta.style.width = window.innerWidth + 'px';
      karta.style.top = '0px';
      karta.style.height = window.innerHeight + 'px';
      return;
    }
    var otstup = 12;
    var top = Math.max(otstup, r.top);
    var niz = Math.min(window.innerHeight - otstup, r.bottom);
    karta.style.left = Math.round(r.left) + 'px';
    karta.style.width = Math.round(r.width) + 'px';
    karta.style.top = Math.round(top) + 'px';
    karta.style.height = Math.round(niz - top) + 'px';
  }

  window.shkPodskazka = function(){
    var okno = elem('trener-okno-podskazki');
    var telo = elem('trener-okno-telo');
    var zag = elem('trener-okno-zag');
    if(!okno || !telo || !ZAHOD || ZAHOD.konec){
      return false;
    }
    telo.innerHTML = telo_podskazki(ZAHOD.vopros);
    if(zag){ zag.textContent = 'Подсказка'; }
    okno.className = 'trener-okno-podskazki vidno';
    okno.setAttribute('aria-hidden', 'false');
    postavit_okno();
    return false;
  };

  window.shkPodskazkaZakryt = function(){
    var okno = elem('trener-okno-podskazki');
    if(okno){
      okno.className = 'trener-okno-podskazki';
      okno.setAttribute('aria-hidden', 'true');
      var telo = elem('trener-okno-telo');
      if(telo){ telo.innerHTML = ''; }
    }
    return false;
  };

  /* Нажатие по подложке (мимо карточки) закрывает окно: так его
     закрывают везде. */
  (function(){
    var okno = elem('trener-okno-podskazki');
    if(!okno || okno.getAttribute('data-shk-okno')){ return; }
    okno.setAttribute('data-shk-okno', '1');
    okno.addEventListener('click', function(e){
      if(e.target === okno){ shkPodskazkaZakryt(); }
    });
  })();


  /* ---- сброс результатов ---- */

  /* Сброс — только по подтверждению: за пройденным стоит вечер работы,
     а кнопка рядом с остальными. Спрашиваем тут же, в панели; окно
     браузера на телевизоре пультом не пройти. */
  /* Сброс результатов — одна кнопка внизу экрана, под полем. Спрашиваем
     тут же, повторным нажатием: первое нажатие превращает кнопку
     в предупреждение («нажмите ещё раз»), второе — стирает. Через
     несколько секунд кнопка возвращается к обычному виду: залипнуть
     в ожидании она не должна. Никаких окон и пяти строк в настройках:
     действие редкое, а место в панели дорогое. */
  var SBRAS_POZDNO = null;

  function sbras_kak_obychno(){
    var k = elem('trener-sbros');
    if(!k){ return; }
    /* Возврат к обычному виду снимает и ожидание: следующее нажатие
       снова спросит, а не сотрёт молча. */
    k.setAttribute('data-zhdet', '0');
    k.className = 'knopka-malaya';
    k.textContent = 'Сбросить результаты теста';
    if(SBRAS_POZDNO){ window.clearTimeout(SBRAS_POZDNO); SBRAS_POZDNO = null; }
  }

  window.shkSbrosit = function(){
    var k = elem('trener-sbros');
    if(!k){ return false; }
    if(k.getAttribute('data-zhdet') === '1'){
      /* Нажали второй раз — стираем: пройденное, ошибки и решение.
         Настройки (что решаем, учебник, параграф) остаются: их выбирали
         не ради результатов. */
      SOSTOYANIE = {};
      OSHIBKI = {};
      OSHIBKI_BIL = false;
      ZAHOD = null;
      sbras_kak_obychno();
      if(window.shkStatistika){ window.shkStatistika({oshibki: []}); }
      return false;
    }
    k.setAttribute('data-zhdet', '1');
    k.className = 'knopka-malaya glavnaya sbros-preduprezhdenie';
    k.textContent = 'Результаты тестирования будут сброшены. ' +
      'Нажмите ещё раз, чтобы подтвердить';
    if(SBRAS_POZDNO){ window.clearTimeout(SBRAS_POZDNO); }
    SBRAS_POZDNO = window.setTimeout(function(){
      var kk = elem('trener-sbros');
      if(kk){ kk.setAttribute('data-zhdet', '0'); }
      sbras_kak_obychno();
    }, 6000);
    return false;
  };

  /* Полный экран — разворот самого поля средствами страницы. Браузерный
     `requestFullscreen` на телевизоре и в предпросмотре не дают, и кнопка
     молчала; свой разворот работает всегда. Выход — тот же значок
     или Esc. */
  window.shkVoVesEkran = function(){
    var b = document.body;
    if(b.classList.contains('trener-vo-ves-ekran')){
      b.classList.remove('trener-vo-ves-ekran');
    } else {
      b.classList.add('trener-vo-ves-ekran');
      var mesto = elem('pleyer-mesto');
      if(mesto && mesto.scrollTo){ mesto.scrollTo(0, 0); }
    }
    oshibki_knopka();
    postavit_okno();
    return false;
  };
  window.shkVoVesEkranZakryt = function(){
    document.body.classList.remove('trener-vo-ves-ekran');
    oshibki_knopka();
    postavit_okno();
    return false;
  };

  window.shkDalshe = function(){
    if(!ZAHOD || ZAHOD.otvechen === null){ return false; }
    if(ZAHOD.i + 1 < ZAHOD.spisok.length){
      ZAHOD.i++;
      /* Следующий ответ — новая минута с нуля. */
      vremya_snachala();
      sdelat_vopros();
    } else if(NASTR.vid === 'oshibki' && OSHIBSKI_KEYS().length){
      /* В работе над ошибками правильный ответ выпадает из выдачи,
         а неправильный остаётся в OSHIBKI и возвращается новым вопросом.
         Когда дошли до конца списка, собираем выдачу заново только из
         оставшихся ошибок. Старый ответ стираем: его надо решить ещё раз,
         а не показать уже окрашенным. */
      ZAHOD.spisok = naydeno();
      ZAHOD.i = 0;
      ZAHOD.otvety = {};
      ZAHOD.otvechen = null;
      ZAHOD.konec = false;
      vremya_snachala();
      sdelat_vopros();
    } else {
      ZAHOD.konec = true;
      vremya_zavershit();
    }
    pokazat();
    return false;
  };

  /* Кнопка «Работа над ошибками» — под полем и на итоге:
     переключает на этот вид и запускает решение сразу. Пока ошибок нет,
     кнопка тусклая и молчит: обещать нечего. */
  window.shkOshibki = function(){
    if(!OSHIBSKI_KEYS().length){ return false; }
    otmetit_vid('oshibki');
    NASTR.vid = 'oshibki';
    ZAHOD = null;
    pokazat();
    return shkNachat();
  };

  /* Номером с клавиатуры: 1—4. Пультом работают стрелки и OK — ответы
     обычные ссылки, и браузер сам водит по ним фокус. */
  document.addEventListener('keydown', function(e){
    if(!ZAHOD || ZAHOD.konec || ZAHOD.otvechen !== null){ return; }
    var n = parseInt(e.key, 10);
    if(n >= 1 && n <= 4){
      var a = document.querySelector(
        '#trener-igra a.trener-otvet[data-n="' + (n - 1) + '"]');
      if(a){ shkOtvet(a); }
    }
  });

  /* ---- настройки ---- */

  /* Сводка над кадром и карточка в кадре: что выбрано и сколько ждёт.
     Одна и та же фраза в двух местах — над кадром коротко, в кадре
     подробно с пояснением, как вопросы идут. */
  /* Статистика под полем: по текущему набору считаем, сколько вопросов
     уже отвечено, сколько из них верно и сколько осталось пройти.
     Считается здесь, а не в движке: числа зависят от выбранного набора,
     и после смены настроек их надо пересчитать. */
  function statistika(spisok){
    /* Статистика не сужается до фильтра «Работа над ошибками»:
       фильтр меняет выдачу, но не общее число курса. Поэтому после
       исправления пяти ошибок счёт возвращается к «277 / 277», а число
       ошибок уменьшается отдельно. */
    var vid_byl = NASTR.vid;
    if(vid_byl === 'oshibki'){ NASTR.vid = ''; }
    var baza = naydeno();
    NASTR.vid = vid_byl;
    var otvecheno = 0, verno = 0;
    for(var i = 0; i < baza.length; i++){
      var s = SOSTOYANIE[baza[i].k];
      if(s){
        otvecheno++;
        if(s === 'verno'){ verno++; }
      }
    }
    var oshibok = OSHIBSKI_KEYS().length;
    var ostalos = baza.length - otvecheno;
    /* Под полем — только то, чего в поле не видно: сколько осталось
       пройти и сколько ошибок. Пройденное и верные ответы в поле есть
       (счёт «N / M» и кристалл с числом), второй раз они не нужны. */
    var mesta = {'stat-oshibok': oshibok,
                 'stat-ostalos': ostalos > 0 ? ostalos : 0};
    for(var id in mesta){
      if(mesta.hasOwnProperty(id)){
        var uzel = elem(id);
        if(uzel){ uzel.textContent = mesta[id]; }
      }
    }
    /* Кристаллы в верхней строке поля — тот же счёт верных ответов. */
    nagrady(verno);
  }

  /* Кристаллы: пять гнёзд, за каждый верный ответ загорается одно.
     Больше пяти не показываем — вместо ряда пишем число: иначе ряд
     уезжал бы за край поля. */
  /* Кристалл загорается с первым верным ответом, а рядом стоит число
     собранных: сколько их всего, видно точно, и ряд не растёт. */
  function nagrady(verno){
    /* Пока не собран ни один кристалл, счётчика нет вовсе: серый
       кристалл с нулём только занимал место и выглядел как поломка.
       Появился первый — появился и счётчик. */
    var schyot = elem('trener-nagrady');
    if(schyot){ schyot.hidden = !verno; }
    var kristall = document.querySelector('#trener-kristally svg.kristall');
    if(kristall){
      kristall.setAttribute('class', 'kristall' + (verno > 0 ? ' vzyt' : ''));
    }
    var chislo = elem('trener-chislo');
    if(chislo){ chislo.textContent = String(verno); }
  }

  /* Кнопка «Работа над ошибками» одна на всю страницу и стоит в поле —
     в нижней строке, между стрелками. Пока идёт заход: на итоге стрелок
     нет, и кнопка там своя — в самом итоге, и вторая в нижней строке
     была бы дублем. Пока ошибок нет, кнопки нет вовсе: серенькая надпись
     «нажимать нечего» только занимала место — работать не над чем.
     Id у кнопки один: другой кнопки нет. */
  function knopka_oshibok(){
    var kk = OSHIBSKI_KEYS().length;
    if(!kk && !OSHIBKI_BIL){ return ''; }
    return '<a class="trener-oshibki-knopka' + (!kk ? ' net-oshibok' : '') +
      '" id="trener-oshibki" href="#" aria-label="Работа над ошибками" ' +
      'onclick="return shkOshibki()">' + OSHIBSKI + '</a>';
  }

  function oshibki_knopka(){
    var kk = OSHIBSKI_KEYS().length;
    var idyot = ZAHOD && !ZAHOD.konec;
    /* Под полем кнопка стоит на странице; на итоге и в полном экране
       ей там места нет (в полном экране поля под полем не видно, на
       итоге кнопка своя — в самом итоге). */
    var mesto = elem('trener-oshibki-mesto');
    if(mesto){ mesto.innerHTML = (kk && !(ZAHOD && ZAHOD.konec))
      ? knopka_oshibok(true) : ''; }
    var v_pole = document.querySelector('.trener-oshibki-v-pole');
    if(v_pole){
      var polnyj = document.body.classList.contains('trener-vo-ves-ekran');
      v_pole.innerHTML = (polnyj && kk && idyot) ? knopka_oshibok(false) : '';
    }
  }

  function pokazat(){
    var karta  = elem('trener-karta');
    var shapka = elem('pleyer-zag');
    var par_blok = elem('nastr-par');
    var poisk = elem('nastr-poisk');
    var krestik = elem('nastr-krestik');
    var prig   = elem('trener-priglashenie');
    var igra   = elem('trener-igra');
    var nachat = elem('trener-nachat');
    var spisok = naydeno();
    var chislo = spisok.length;
    /* Значок вопроса живой, пока идёт решение: по нему открывается
       подсказка — что это было и как об этом сказано в учебнике. Нет
       вопроса (приглашение, итог) — значок немой: подсказывать нечего. */
    var znak = elem('trener-podskazka-znak');
    if(znak){
      var gotov = ZAHOD && !ZAHOD.konec;
      /* На пустом экране знака вопроса нет вовсе: подсказывать нечего, и
         серая точка рядом с кнопкой только звала бы нажать впустую.
         Появляется он вместе с первым вопросом. */
      znak.hidden = !gotov;
      znak.className = 'trener-znachok vopros' + (gotov ? '' : ' tuskly');
      if(gotov){
        znak.setAttribute('role', 'button');
        znak.setAttribute('tabindex', '0');
        znak.removeAttribute('aria-disabled');
        znak.setAttribute('onclick', 'return shkPodskazka()');
      } else {
        znak.removeAttribute('role');
        znak.removeAttribute('tabindex');
        znak.setAttribute('aria-disabled', 'true');
        znak.removeAttribute('onclick');
      }
    }
    /* Вопрос сменился — окно подсказки закрываем: оно было про прежний
       вопрос, и показывать в нём новый рассказ само по себе незачем. */
    if(window.shkPodskazkaZakryt){ shkPodskazkaZakryt(); }

    /* Раздел «Ограничить до» показывается только у выбранного
       учебника: «весь курс» ничем не ограничивается, и раздела там нет.
       Ограничение — строкой ниже с крестиком; нет ограничения — нет
       и строки. */
    var vybrannyj = NASTR.par && PAR_PO_KODU[NASTR.par];
    if(par_blok){ par_blok.hidden = !NASTR.uch; }
    /* Выбранный параграф стоит в самом поле, а справа в поле — крестик.
       Идёт поиск — не трогаем ни то, ни другое: в поле набранное. */
    if(!POISK_IDYOT){
      if(poisk){
        poisk.value = vybrannyj ? '§ ' + vybrannyj.n : '';
        /* Выбранный параграф отмечен в поле жёлтой полосой у левого
           края — как выделенная строка списка. */
        poisk.className = 'nastr-poisk' + (vybrannyj ? ' vydelen' : '');
      }
      if(krestik){ krestik.hidden = !vybrannyj; }
    }
    statistika(spisok);
    oshibki_knopka();
    /* Решение идёт — в поле вопрос, приглашение спрятано; не начато —
       наоборот. Строка «Начать» есть только тогда, когда есть что
       решать: на пустом наборе она обещала бы то, чего нет. */
    if(prig){ prig.style.display = ZAHOD ? 'none' : ''; }
    if(nachat){ nachat.style.display = chislo ? '' : 'none'; }
    /* Пустой экран — сама кнопка: контур во всё поле. Класс нужен и
       росту поля: приглашение стоит поверх поля и само высоты не даёт
       (см. .trener-karta.pusto в оформлении). */
    if(karta){
      karta.className = 'trener-karta' +
        (!ZAHOD && chislo ? ' pusto' : '');
    }
    if(igra){
      igra.className = 'trener-igra' + (ZAHOD ? ' vidna' : '') +
        (ZAHOD && ZAHOD.konec ? ' itog' : '');
      igra.innerHTML = ZAHOD ? razmetka_voprosa() : '';
      /* Полоса времени нарисована заново вместе с вопросом: ставим её
         туда, где минута идёт сейчас (разметку строки перебирали
         целиком, и прежняя полоса ушла вместе с ней). */
      vremya_narisovat();
      /* Прокручивается страница, а не поле: рабочий экран растёт по
         высоте содержимого, своей прокрутки у него нет. Новый вопрос
         и возврат к прежнему — подводим к началу поля: на телефоне
         после ответа поле уезжает вниз, и без этого вопрос оказался бы
         за верхним краем. «nearest» ничего не двигает, если и так видно. */
      if(ZAHOD && ZAHOD.prokrutit){
        var kuda = elem('pleyer-mesto');
        if(kuda && kuda.scrollIntoView){
          try{ kuda.scrollIntoView({block:'nearest', behavior:'smooth'}); }
          catch(e){ kuda.scrollIntoView(false); }
        }
        ZAHOD.prokrutit = '';
      }
    }
    if(shapka){
      /* Над кадром — сами настройки, а не имя страницы: имя и так видно в
         хлебных крошках, а настройки — то, чем этот кадр налит. Счёт
         вопросов сюда не пишем: он стоит в карточке и в статистике. */
      shapka.textContent = stroka_nastroek();
    }
    /* В левом верхнем углу поля — где мы в наборе. Пока решение не
       начато и на итоге строки нет: там она ничего не значит. */
    schet = elem('trener-schet-za');
    if(schet){
      if(ZAHOD && !ZAHOD.konec){
        /* «2 / 277»: номер и общее число — через косую. Слова «Вопрос» и
           «из» тут лишние — по двум числам и косой всё понятно, и строка
           стала короткой. Нынешний номер светлее общего: он и меняется. */
        schet.innerHTML = '<b>' + (ZAHOD.i + 1) + '</b> / ' +
          ZAHOD.spisok.length;
        schet.hidden = false;
      } else {
        schet.hidden = true;
        schet.innerHTML = '';
      }
    }
    /* Счёт ошибок стоит рядом со счётом вопросов и живёт с ним заодно:
       нет захода — нет ни того, ни другого. */
    var schet_osh = elem('trener-oshibki-schet');
    /* Ошибок нет — нет и символа с нулём: он появляется только после
       первой ошибки и живёт дальше вместе с заходом. */
    if(schet_osh){ schet_osh.hidden = !(ZAHOD && !ZAHOD.konec &&
      OSHIBSKI_KEYS().length); }
    /* Полоса времени живёт с заходом: заход идёт — минута идёт, кончился
       (итог, сброс, смена настроек) — полоса стала. */
    if(ZAHOD && !ZAHOD.konec){ vremya_pustit(); }
    else { VREMYA_IDYOT = false; }
    /* «Работу над ошибками» расставляем в самом конце: поле к этому
       моменту перерисовано, и место в строке управления уже есть. */
    oshibki_knopka();
  }

  function otmetit_vid(vid){
    var spis = document.querySelectorAll('#pleylist-panel a[data-vid]');
    for(var i = 0; i < spis.length; i++){
      spis[i].classList.remove('aktiven');
      if(spis[i].getAttribute('data-vid') === vid){
        spis[i].classList.add('aktiven');
      }
    }
  }

  /* Значок настроек открывает и закрывает панель — как значок меню:
     второе нажатие прячет её обратно (см. shkPleylistTog в _tv.py). */
  window.shkNastroyki = function(){
    return shkPleylistTog();
  };
  window.shkVid = function(a){
    var vid = a.getAttribute('data-vid');
    if(!VIDY[vid]){ return false; }
    otmetit_vid(vid);
    NASTR.vid = vid;
    /* Сменили настройку — прежний набор к ней не подходит: другой
       будет и состав, и счёт. Незаконченное решение убираем, а не
       тянем его счётом в новый набор. */
    ZAHOD = null;
    pokazat();
    return false;
  };
  /* Учебник: «Весь курс» — пустая строка. Отметку строки ставим прямо
     здесь: строк с учебником в панели две-три, и общий ход по атрибуту
     тут короче любого отдельного счётчика. */
  window.shkUchebnik = function(a){
    var uch = a ? (a.getAttribute('data-uch') || '') : '';
    var spis = document.querySelectorAll('#pleylist-panel a[data-uch]');
    for(var i = 0; i < spis.length; i++){
      spis[i].classList.remove('aktiven');
      if((spis[i].getAttribute('data-uch') || '') === uch){
        spis[i].classList.add('aktiven');
      }
    }
    /* «Весь курс» ограничить нечем: две книги вместе не режутся по
       параграфу одной из них. А выбранный параграф мог остаться
       в другой книге: курс сузился до одной, и такого параграфа
       в нём больше нет. */
    if(!uch){ NASTR.par = ''; }
    if(uch && NASTR.par && PAR_PO_KODU[NASTR.par] &&
       PAR_PO_KODU[NASTR.par].u !== uch){
      NASTR.par = '';
    }
    NASTR.uch = uch;
    /* Сменили настройку — прежний набор к ней не подходит. */
    ZAHOD = null;
    pokazat();
    return false;
  };

  /* ---- выбор параграфа ---- */

  /* Идёт ли поиск: в поле набрали, и под ним раскрыт список находок.
     Пока поиск идёт, в поле — набранное, а не выбранное: выбор покажет
     себя, когда параграф возьмут (или когда поиск закроют). */
  var POISK_IDYOT = false;

  /* Список найденного прячется, а поле очищается. Само поле никуда не
     пропадает: оно стоит в панели всегда — в него и набирают. Что
     в поле стоит после этого, решает pokazat: есть выбранный параграф —
     он и встанет на место. */
  function zakryt_poisk(){
    var mesto = elem('nastr-naydennoe');
    var poisk = elem('nastr-poisk');
    if(mesto){ mesto.hidden = true; mesto.innerHTML = ''; }
    if(poisk){ poisk.value = ''; }
    POISK_IDYOT = false;
  }

  /* Ищем ТОЧНО: набранный номер должен совпасть с номером параграфа —
     со всем («12–13») или с одной его половиной («12», «13»). Примерных
     попаданий не показываем: список из десяти «похожих» только мешает,
     а нужного в нём может и не быть. Обычно находится один параграф,
     и он встаёт единственной строкой под полем. */
  function naydennye_paragrafy(poisk){
    var itog = [];
    var q = String(poisk || '').replace(/[^0-9]/g, '');
    if(!q){ return itog; }
    for(var i = 0; i < PARAGRAFY.length; i++){
      var p = PARAGRAFY[i];
      /* Выбран учебник — и параграфы ищем по нему: в другой книге свои
         номера, и § 12 оттуда — не тот § 12, что здесь. */
      if(NASTR.uch && p.u !== NASTR.uch){ continue; }
      var chasti = String(p.n).split(/[—–-]/);
      var tochno = false;
      for(var c = 0; c < chasti.length; c++){
        if(q === chasti[c].replace(/[^0-9]/g, '')){ tochno = true; }
      }
      /* У сдвоенного параграфа цифры сверяем по половинам: «12» находит
         § 12–13, но не § 1–2 — у того цифры «12» только в сумме. Набранное
         «1213» не находим: такого номера в учебнике нет. */
      if(tochno){ itog.push(p); }
    }
    return itog;
  }

  window.shkPoiskParagraf = function(znachenie){
    var mesto = elem('nastr-naydennoe');
    if(!mesto){ return false; }
    var q = String(znachenie || '').trim();
    if(!q){
      /* Поле очистили — поиска нет. В поле снова видно выбранное, если
         оно есть (см. pokazat), и крестик к нему возвращается. */
      zakryt_poisk();
      pokazat();
      return false;
    }
    POISK_IDYOT = true;
    /* На время поиска крестик прячем: поле сейчас про новое, а не про
       выбранное. Взяли параграф — вернётся вместе с ним. */
    var krestik = elem('nastr-krestik');
    if(krestik){ krestik.hidden = true; }
    var spis = naydennye_paragrafy(q);
    var html = '';
    if(!spis.length){
      html = '<div class="nastr-pusto">Такого параграфа нет. Наберите ' +
        'номер — например, 12.</div>';
    } else {
      for(var i = 0; i < spis.length; i++){
        var p = spis[i];
        html += '<a class="nastr-stroka' +
          (p.k === NASTR.par ? ' aktiven' : '') + '" href="#" data-par="' +
          p.k + '" onclick="return shkPoiskVzyat(this)">' +
          '<span class="nastr-nomer">§ ' + ekran(p.n) + '</span>' +
          '<span class="nastr-tekst">' + ekran(p.t) + '</span>' +
          '<span class="nastr-schet">' + (p.v || 0) + '</span></a>';
      }
    }
    mesto.innerHTML = html;
    mesto.hidden = false;
    return false;
  };

  /* Клавиши в поле поиска: Enter берёт первую находку — так параграф
     выбирается одним касанием, Esc закрывает поиск, стрелки водят по
     найденному (это же работает пультом). */
  window.shkPoiskKlavesa = function(e){
    if(e.key === 'Escape'){
      /* Esc чистит поле и список, а не закрывает панель: событие дальше
         не идёт — иначе вместе с полем закрылись бы и настройки. */
      if(e.stopPropagation){ e.stopPropagation(); }
      zakryt_poisk();
      pokazat();
      return false;
    }
    var spis = document.querySelectorAll('#nastr-naydennoe a[data-par]');
    if(e.key === 'Enter'){
      /* Первая находка, а не строка «Весь курс»: она в списке первая
         всегда, и Enter выбирал бы её вместо найденного параграфа. */
      for(var i = 0; i < spis.length; i++){
        var kod = spis[i].getAttribute('data-par');
        if(kod){ return shkParagraf(kod); }
      }
      return false;
    }
    if(e.key === 'ArrowDown' || e.key === 'ArrowUp'){
      if(!spis.length){ return false; }
      var n = 0;
      var a = document.activeElement;
      if(a && a.getAttribute && a.getAttribute('data-par') !== null){
        n = Array.prototype.indexOf.call(spis, a);
        if(n < 0){ n = 0; }
      }
      n = e.key === 'ArrowDown' ? Math.min(n + 1, spis.length - 1)
                                : Math.max(n - 1, 0);
      if(spis[n] && spis[n].focus){
        try{ spis[n].focus(); }catch(err){}
      }
      return false;
    }
    return true;
  };

  /* Строка из списка найденного: код параграфа лежит в самой строке. */
  window.shkPoiskVzyat = function(a){
    return shkParagraf(a ? a.getAttribute('data-par') : '');
  };

  /* Выбрали параграф (пустой код — «весь курс»). Поиск закрывается,
     а выбранное встаёт в само поле — там его и видно, там и крестик. */
  window.shkParagraf = function(kod){
    NASTR.par = kod || '';
    ZAHOD = null;
    zakryt_poisk();
    pokazat();
    return false;
  };

  /* Крестик у выбранной строки: снять ограничение. */
  window.shkSnyatOgranichenie = function(){
    return shkParagraf('');
  };

  /* «Переходить к следующему вопросу сам»: нажали — галочка встала или
     снялась. Строка отмечается как всякая выбранная настройка (см.
     aktiven), а сама галочка — и есть отметка, по ней и видно выбор. */
  window.shkAvto = function(){
    NASTR.avto = !NASTR.avto;
    var stroka = elem('nastr-avto');
    if(stroka){
      stroka.className = 'nastr-stroka' + (NASTR.avto ? ' aktiven' : '');
    }
    return false;
  };

  /* Статистику зовёт движок после каждого ответа: числа под полем
     считаются по отметкам ответов (см. statistika), а здесь только
     принимается список ошибок. */
  window.shkStatistika = function(z){
    z = z || {};
    if(z.oshibki){
      var novye = {};
      for(var i = 0; i < z.oshibki.length; i++){ novye[z.oshibki[i]] = true; }
      OSHIBKI = novye;
    }
    pokazat();
  };

  pokazat();
  if(window.shkStatistika){ window.shkStatistika({}); }
  /* Панель появляется в странице после скрипта: как только она собрана,
     показываем то же ещё раз — уже с её строками. */
  if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', pokazat);
  } else {
    pokazat();
  }
})();
</script>
"""


def main(fayl, put, dannye, menyu_spisok=None, menyu_zagolovok='', kniga=None,
         klassy=None, zagolovok=None, niz='', ssylka_video='', s_video=None):
    """Собрать страницу тренажёров и записать её в «Проект».

    `dannye` — то, что вернул `dannye_est`. Остальное — как у других
    страниц материалов (см. `_tv.sobrat`): путь, хлебные крошки, меню,
    строка учебника. `zagolovok` — имя страницы для окна браузера.
    """
    klass = '7 класс'
    predmet = 'История'
    paragrafy = paragrafy_est(klass, predmet)
    chislo_d = len(dannye['даты'])
    chislo_o = len(dannye['определения'])
    # Учебники курса — из самих параграфов: у каждого там стоит его книга
    # (см. Временные/привязать_параграфы.py). Порядок — как у UCH_PORYADOK.
    vse_uch = []
    for p in paragrafy:
        if p['uchebnik'] and p['uchebnik'] not in vse_uch:
            vse_uch.append(p['uchebnik'])
    uchebniki = [u for u in UCH_PORYADOK if u in vse_uch]
    uchebniki += [u for u in vse_uch if u not in uchebniki]
    # «svodka» — та самая строка над кадром: она и есть заголовок страницы,
    # поэтому здесь не число вопросов, а настройки: что тренируем и по
    # какому курсу. Счёты живут в статистике под полем.
    # «svodka» — та самая строка над кадром: она и есть заголовок
    # страницы, поэтому здесь настройки, а не число вопросов. В самом
    # поле на пустом экране — только название набора и кнопка: сколько
    # вопросов и как они идут, видно с первых же вопросов.
    priglashenie = {'svodka': f'{VIDY[0][1]} · Весь курс'}
    # Число вопросов у каждого параграфа — своё: считаем один раз и там,
    # где оно нужно, — в строках списка и в сноске.
    chisla = {p['kod']: {'даты': 0, 'определения': 0} for p in paragrafy}
    for d in dannye['даты']:
        if d.get('paragraf') in chisla:
            chisla[d['paragraf']]['даты'] += 1
    for o in dannye['определения']:
        if o.get('paragraf') in chisla:
            chisla[o['paragraf']]['определения'] += 1
    for p in paragrafy:
        p['даты'] = chisla[p['kod']]['даты']
        p['определения'] = chisla[p['kod']]['определения']
    bloki, panel = blok_trenazhera(dannye, paragrafy, priglashenie, niz=niz,
                                   ssylka_video=ssylka_video,
                                   uchebniki=uchebniki, s_video=s_video)
    put_fayla, razmer = _tv.sobrat(zagolovok or 'Тренажёры', 'Проверь себя',
                                   [bloki], fayl, put=put, indeks=True,
                                   menyu_spisok=menyu_spisok,
                                   menyu_zagolovok=menyu_zagolovok,
                                   kniga=kniga, klassy=klassy,
                                   telo_klass='pleylist-otkryto',
                                   paneli=panel)
    print(f'  {fayl:<46} дат {chislo_d}, определений {chislo_o}, '
          f'параграфов {len(paragrafy)}, {razmer:>6} байт')
    return put_fayla


if __name__ == '__main__':
    print('Этот файл вызывается из gen_tv_paket.py: страница тренажёров — '
          'часть пакета, а не отдельная сборка.')
