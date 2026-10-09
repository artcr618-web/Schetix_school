# -*- coding: utf-8 -*-
"""Общее оформление страниц рабочего проекта «Проект».

Подключается из gen_tv_geografiya_5klass.py и gen_tv_paket.py, чтобы
все страницы пакета выглядели одинаково и правились в одном месте.

Главное отличие от обычных страниц: ими управляют пультом — стрелками
и кнопкой OK. Поэтому:

  * шрифт крупный, мишени большие, плитки во всю ширину экрана;
  * у всего, что может получить фокус, яркая рамка — иначе непонятно,
    где ты сейчас;
  * никаких внешних ресурсов: ни шрифтов, ни скриптов, ни картинок.
    Один файл, открывается мгновенно на слабом телевизоре;
  * свой javascript — только на шапку: «Назад/Вперёд», «Домой»,
    «Закрепить» и переход на закреплённую страницу при запуске.
    Пространственную навигацию пультом браузеры телевизоров
    (TV Bro, Puffin TV) делают сами;

  * ссылки открываются в той же вкладке, поэтому «Назад» на пульте
    возвращает к списку, а кнопки в шапке работают по истории браузера.

КАК УСТРОЕНА ШАПКА. На каждой странице одна и та же полоса сверху:
кнопки «Назад» и «Вперёд», хлебные крошки («8 класс › Геометрия ›
Видеоуроки»), «Домой», «Закрепить» и «Меню». Страницы — обычные
отдельные файлы, открываются в том же окне, поэтому история браузера
накапливается и кнопки «Назад/Вперёд» работают как положено. Никаких
iframe: по file:// браузеры запрещают заглядывать внутрь вложенной
страницы, и кнопки перестали бы понимать, где мы находимся.

КАК УСТРОЕНА ДОМАШНЯЯ СТРАНИЦА. Кнопка «Закрепить» (📌) запоминает
текущую страницу в localStorage браузера — то есть на этом устройстве,
в этом браузере. Запомненное живёт в браузере, а не на флешке: на
телевизоре ребёнок закрепил «8 класс › Геометрия», и флешка везде
останется общей. После этого:

  * кнопка «Домой» ведёт сразу на закреплённую страницу;
  * при открытии «Начать учиться.html» браузер сам переходит
    на закреплённую страницу;

  * чтобы вернуться к выбору класса, есть кнопка «Меню» — она
    открывает вход с #menu, и перехода не происходит.

Если браузер не даёт пользоваться localStorage (в предпросмотрах и при
запуске в песочнице бывает), весь блок «Домой / Закрепить» просто
прячется, а страницы работают как раньше.

ПУТИ. Все функции принимают пути от корня пакета (например
«База данных/HTML/8 класс/Геометрия/видеоуроки.html»). Относительные
ссылки для каждой страницы считаются здесь же, поэтому при переезде
файлов править html не нужно.
"""
import io
import os
import posixpath
import sys
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAKET = os.path.join(ROOT, 'Проект')
"""Рабочий проект: то, что целиком копируют на флешку.

В корне лежит ровно один файл — «Начать учиться.html». Всё остальное
убрано в «База данных/», чтобы конечный пользователь не видел простыню
из десятков файлов: он открывает один файл и дальше ходит по ссылкам.
"""

BAZA = 'База данных'
"""Папка со всем содержимым пакета, кроме главной страницы. Имена
папок и файлов — по-русски."""

HTML = BAZA + '/HTML'
"""Папка со страницами: класс -> предмет -> материал.

Единственное имя латиницей в пакете — так его прочитает любое
устройство, а имена страниц внутри остаются русскими. Путь каждой
страницы собирается в gen_tv_paket (put_klassa, put_predmeta,
put_materiala) — там эта папка и подставляется."""

VHOD = 'Начать учиться.html'

# Оформление страниц лежит отдельным файлом, а не внутри каждой страницы.
# В html остаётся только разметка; файл подключается ссылкой, путь до
# него считается от самой страницы (otnositelno), поэтому он работает
# и с флешки, и из любой папки. Собирает его ta же сборка, что и
# страницы: см. zapisat_css().
CSS_FAYL = BAZA + '/оформление.css'
"""Единственный файл в корне пакета (и в корне флешки)."""

KOREN = '.'
"""Путь от корня пакета до корня пакета — для хлебных крошек."""


def otnositelno(otkuda, kuda):
    """Ссылка со страницы `otkuda` на страницу `kuda` (обе от корня)."""
    papka = posixpath.dirname(otkuda)
    put = posixpath.relpath(kuda, papka) if papka else kuda
    return put


def put_kartinki(kartinka):
    """Путь к рисунку для `--kartinka` — от файла оформления, а не от страницы.

    `url()` внутри своего свойства разворачивается от того файла, где
    значение объявлено, а у нас это «База данных/оформление.css».
    Поэтому «Фоны/История.jpg» — верно, а «../Фоны/История.jpg» уезжает
    на уровень выше, в «Проект/Фоны», и рисунок не находится: плашки
    классов оставались без фонов. Считать путь от страницы, как для
    ссылок, здесь нельзя — пути разные.
    """
    return otnositelno(CSS_FAYL, kartinka)


def perevesti_puti(html, fayl):
    """Ссылки, ведущие от корня пакета, сделать относительными.

    stroit() выдаёт внутренние ссылки путями от корня («База данных/…»),
    потому что сам не знает, куда ляжет страница. Здесь это
    исправляется: ссылка, которая от корня пакета существует на диске,
    переписывается относительно `fayl`.
    """
    def pod(m):
        h = m.group(2)
        if h.startswith(('http://', 'https://', 'mailto:', 'javascript:',
                         '#')):
            return m.group(0)
        put, _, hvost = h.partition('?')
        if not os.path.isfile(os.path.join(PAKET, *put.split('/'))):
            return m.group(0)
        nov = otnositelno(fayl, put) + ('?' + hvost if hvost else '')
        return f'{m.group(1)}{nov}{m.group(3)}'
    return re.sub(r'(href=")([^"]+)(")', pod, html)


def mm(s):
    """Секунды → «7:22»."""
    s = int(s)
    return f'{s // 60}:{s % 60:02d}'


def podgotovit_paket(nuzhnye):
    """Удалить из пакета html-файлы, которых больше нет.

    Без этого после переименования в папке остаются старые файлы под
    прежними именами — две копии одной страницы, и непонятно, какую
    открывать. Удаляются только .html и только внутри папки пакета.
    Обход рекурсивный: файлы лежат по папкам классов и предметов.
    """
    nuzhnye = {n.replace(os.sep, '/') for n in nuzhnye}
    os.makedirs(PAKET, exist_ok=True)
    # Служебные файлы пакета в списке страниц не значатся, но и удалять
    # их нельзя. Сейчас таких в пакете нет: список «Что не нашлось»
    # переехал в «Документацию» (собирает Инструменты/gen_spisok.py).
    sluzhebnye = {'Что не нашлось.html'}
    for papka, podpapki, fayly in os.walk(PAKET):
        for imya in sorted(fayly):
            if not imya.endswith('.html') or imya in sluzhebnye:
                continue
            polny = os.path.join(papka, imya)
            otn = os.path.relpath(polny, PAKET).replace(os.sep, '/')
            if otn not in nuzhnye:
                os.remove(polny)
                print(f'  удалён устаревший файл: {otn}')
    # За файлами убираем и осиротевшие папки: после переезда страниц
    # в «HTML» на флешке не должно остаться пустых следов прежней
    # раскладки. Удаляем только пустые — где что-то лежит, не трогаем.
    for papka, podpapki, fayly in os.walk(PAKET, topdown=False):
        if papka == PAKET:
            continue
        try:
            os.rmdir(papka)
        except OSError:
            pass


CSS = """
:root{
  --fon:#0e1116; --kart:#1b212b; --ramka:#ffd23f;
  --tekst:#f3f5f9; --tuskly:#98a2b3; --knopka:#2b3543; --knopka-focus:#3d4c5f;
}
*{box-sizing:border-box}
/* Ниже 320 px страница не ужимается: это нижний артборд Тильды.
   Окно уже — появится боковая прокрутка, но вёрстка не поедет. */
html{min-width:320px}
html{-webkit-text-size-adjust:100%}
body{
  /* --panel-shirina — сколько места освобождается справа, когда меню
     выехало. Страница при этом не перекрывается: она перестраивается
     по оставшейся ширине, как в Arena. */
  --panel-shirina:420px;
  margin:0; background:#0e1116; color:#f3f5f9;
  font-family:system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;
  font-size:30px; line-height:1.35; padding:0 0 120px;
  transition:padding-right .32s ease;
}
body.menu-otkryto{padding-right:var(--panel-shirina)}

/* ---- рабочая ширина страницы ----
   Рабочая ширина — ширина ТОЙ ОБЛАСТИ, где стоят плашки и строки, а не
   ширина окна. Открытое боковое меню забирает у страницы своё место
   (padding-right у body выше), поэтому раскладку надо считать по
   остатку: иначе на широком экране с открытым меню в ряд по-прежнему
   встают три плашки, места им не хватает и цифры вылезают наружу.

   Контейнер — внешний блок вокруг .wrap: его ширина и есть рабочая.
   Поля страницы (.wrap) в неё не входят, поэтому модель экрана та же,
   как если бы окно было ровно такой ширины. Раскладка по этой ширине
   собирается в Инструменты/разметка.py (@container stranica).

   Панели (меню и плейлист) стоят СНАРУЖИ контейнера: внутри него
   position:fixed считался бы от него, а не от окна. */
.ZONA-KLASS{container-type:inline-size; container-name:KONTEYNER-IMYA}
.wrap{max-width:SHIRINA-STRANICYpx; margin:0 auto}
/* ПОЛЯ-СТРАНИЦЫ */

/* ---- шапка, одинаковая на всех страницах ---- */
nav.verh{
  position:relative;
  display:flex; align-items:center; gap:14px; flex-wrap:wrap;
  background:#16202b; border-radius:18px; padding:12px 18px; margin-bottom:26px;
}
/* Имя ребёнка — по середине шапки, там, где у сайтов стоит логотип.
   Оно из памяти браузера: то же, что написано на главном экране.
   Пустое — строки нет. На узких экранах имени нет: оно наехало бы
   на кнопки. */
.verh-imya{
  position:absolute; left:50%; transform:translateX(-50%);
  max-width:38%; overflow:hidden; text-overflow:ellipsis;
  white-space:nowrap; font-size:26px; font-weight:600; color:#f3f5f9;
}
.verh-imya[hidden]{display:none}
@container stranica (max-width:959px){
  .verh-imya{display:none}
}
a.tumbler{
  display:inline-block; background:#2b3543; color:#f3f5f9; text-decoration:none;
  border:4px solid transparent; border-radius:14px; padding:12px 22px;
  font-size:25px; white-space:nowrap;
}
a.tumbler:focus, a.tumbler:hover, a.tumbler:active{
  outline:none; border-color:#ffd23f; background:#3d4c5f;
}
/* Закреплённая страница: скрепка горит акцентным цветом. Никаких
   надписей про домашнюю страницу — по ней это видно сразу. */
a.tumbler.zakrep{background:#4a3d16; border-color:#ffd23f; color:#ffd23f}
a.tumbler.net{background:#22262c; color:#7d8695}
/* ---- путь: тусклая строка под шапкой, без подложки ----
   Внутри шапки путь спорил с кнопками и перетягивал внимание на себя.
   Здесь он отдельной строкой и приглушён: это подпись «где мы», а не
   навигация. Жёлтой строка становится только в фокусе — иначе по ней
   не пройтись пультом и не видно, на чём мы стоим. */
.put-stroka{
  display:flex; align-items:center; flex-wrap:wrap; gap:12px;
  margin:0 0 4px; padding:2px 4px;
  font-size:23px; color:#7b8494;
}
.put-stroka a{
  color:#8d97a8; text-decoration:none;
  border-bottom:1px dotted #3a4351;
}
.put-stroka a:focus{
  outline:3px solid #ffd23f; outline-offset:3px;
  color:#f3f5f9; border-bottom-color:transparent;
}
.put-stroka .zdes{color:#b9c1d0}
.put-stroka .razd{color:#4d5666}

/* ---- главный экран: имя и цель ----
   Ни заголовка, ни подзаголовка, ни черты под строкой: это две строки
   для ввода, а надписи «Введи своё имя» и «чего ты хочешь достичь…» —
   подсказки внутри самих строк. Что человек написал, видно крупно и
   ярко, как прежде выглядел заголовок; подсказка же стоит приглушённой
   и, как только в строке появляется текст, пропадает сама.

   Слово «Цель:» — не подсказка, а часть строки: оно стоит приглушённым,
   как название учебника и путь на других страницах, и не стирается.
   Строки идут одна под другой вплотную, как один элемент интерфейса:
   между ними всего 10 px. */
.privet{width:100%; margin:36px 0 0}
.privet input[type="text"]{
  display:block; width:100%; box-sizing:border-box;
  margin:0; padding:6px 4px; text-align:center;
  background:transparent; border:0; border-radius:0;
  font-family:inherit; font-weight:600; line-height:1.15;
  font-size:clamp(30px, 3.6vw, 48px); color:#f3f5f9;
  caret-color:#ffd23f;
}
.privet input[type="text"]::placeholder{color:#6b7688; opacity:1}
.privet input[type="text"]:focus{outline:none}
.privet-tsel{
  display:flex; justify-content:center; align-items:baseline;
  gap:14px; margin-top:10px; max-width:100%;
}
.privet-tsel .privet-slovo{
  flex:0 0 auto; color:#8b95a5; font-weight:400;
  font-size:clamp(23px, 2.3vw, 31px); line-height:1.15;
  hyphens:manual; white-space:nowrap;
}
/* Строка цели шириной по своему тексту: тогда «Цель:» и написанное
   стоят по центру вместе, как подзаголовок. Ширину считает скрипт по
   невидимой мерке — она набрана тем же шрифтом, что и поле. */
.privet-merka{
  position:absolute; left:-9999px; top:0; white-space:pre;
  visibility:hidden; font:inherit; font-weight:400;
  font-size:clamp(23px, 2.3vw, 31px);
}
.privet input#tsel{
  /* Ширину считает скрипт по тексту, поэтому поле СЖИМАЕМОЕ: на узком
     экране строка цели не влезает целиком, и поле уступает первым —
     иначе оно вылезало за кадр и страница уезжала вбок. Раскрытое
     до конца поле по-прежнему показывает всю надпись. */
  flex:0 1 auto; min-width:0; width:20px; padding:4px 2px; text-align:left;
  font-weight:400; font-size:clamp(23px, 2.3vw, 31px); color:#dbe3ee;
}
.privet + .setka{margin-top:46px}

/* ---- учебник: мелкая строка под путём, прямо на фоне ----
   Не плашка и не список: одна подпись, по какому учебнику собраны
   материалы. Подробности (авторы, издательство, год) — на плитках
   выбора предмета. */
.kniga-stroka{
  margin:0 0 18px; padding:0 4px;
  font-size:24px; color:#8b95a5;
  hyphens:manual; overflow-wrap:break-word;
}
/* Название учебника и стрелка — в одну строку, ничего перед названием.
   Разметку строки браузер сам превращает в раскрывающийся список и
   рисует свой треугольник; list-style снимает его, а flex ставит
   стрелку рядом с названием, а не под ним. */
.kniga-stroka > summary{
  display:flex; align-items:center; gap:16px; cursor:pointer;
  padding:2px 0; list-style:none;
  font-size:24px; color:#8b95a5;
  hyphens:manual; overflow-wrap:break-word;
}
.kniga-stroka > summary::-webkit-details-marker{display:none}
.kniga-stroka > summary::marker{content:''}
.kniga-stroka .kn-nazv{flex:1 1 auto; min-width:0}
.kniga-stroka .strela{flex:0 0 auto; display:flex; color:inherit}
.kniga-stroka .strela svg{width:26px; height:26px; display:block}
details.kniga-stroka[open] .strela{transform:rotate(180deg)}
/* Раскрытая часть — карточка учебника: маленькая обложка и подписи
   рядом с ней. Обложка здесь ровно вполовину прежнего (было 180 px,
   стало 90): рядом со строками текста большая картинка выглядела
   плакатом, а у предмета с двумя учебниками обложки смыкались друг с
   другом. Рассмотреть её подробно можно нажатием — она открывается во
   весь экран (см. окно обложки ниже). */
.kn-podrobno{padding:12px 0 4px}
.kn-kartochka{display:flex; align-items:flex-start; gap:24px}
/* Две карточки подряд (у предмета с двумя учебниками) раньше стояли
   вплотную: низ одной обложки упирался в верх следующей. */
.kn-kartochka + .kn-kartochka{margin-top:26px}
.kn-oblozhka{
  flex:0 0 auto; display:block; line-height:0; cursor:zoom-in;
  border:3px solid transparent; border-radius:12px;
}
.kn-oblozhka:focus, .kn-oblozhka:focus-visible{
  outline:3px solid #ffd23f; outline-offset:2px;
}
.kn-kartochka img{
  width:90px; height:auto; display:block; border-radius:9px;
}
.kn-kartotekst{
  display:flex; flex-direction:column; gap:10px; min-width:0;
  padding-top:2px;
}
.kn-knazv{
  font-size:27px; font-weight:600; color:#f3f5f9; line-height:1.2;
  hyphens:manual; overflow-wrap:break-word;
}
/* На узком экране обложка встаёт над описанием: рядом они не помещаются,
   и обложка выдавливала текст в столбик шириной в пару букв. Ширина —
   рабочая: с открытым меню она тоже сужается, и карточка перестраивается
   вместе со страницей (Инструменты/разметка.py). */
@container stranica (max-width:959px){
  .kn-kartochka{flex-direction:column; gap:12px}
  .kn-kartochka + .kn-kartochka{margin-top:22px}
  .kn-kartochka img{width:78px}
}
.kn-kavt{font-size:23px; color:#98a2b3; line-height:1.3}

/* ---- обложка во весь экран ----
   Нажали на обложку — она открылась крупно, чтобы рассмотреть
   подробности. Окно поверх всего: тёмный фон, обложка по центру,
   закрывается нажатием в любое место или клавишей Esc (её ловит тот же
   обработчик, что закрывает панели). Самого окна в разметке нет: его
   собирает скрипт при первом нажатии — на страницах без учебника оно
   ни к чему. */
#shk-oblozhka{
  position:fixed; inset:0; z-index:80; padding:24px;
  display:flex; align-items:center; justify-content:center;
  background:rgba(6,8,12,.9); cursor:zoom-out;
}
#shk-oblozhka[hidden]{display:none}
#shk-oblozhka img{
  width:auto; height:auto;
  max-width:min(92vw, 620px); max-height:86vh;
  border-radius:14px; box-shadow:0 26px 70px rgba(0,0,0,.65);
}

/* ---- обложка учебника — фон всей плашки ----
   Обложка ложится на плашку целиком (cover), а не полосой сбоку:
   плашка и есть книга. Поверх неё — затемнение по диагонали: сверху
   картинка видна, к нижнему левому углу уходит в тень, где стоит
   название. Надписи с самой обложки мы не читаем — она нужна как
   картинка, поэтому текст наш, поверх затемнения. */
a.plitka.s-kartinkoy, a.banner-znak.s-kartinkoy{
  /* Рисунок сам тёмный, сюжет вверху справа, поэтому затемнение
     слабое: свет гасим только там, где стоит текст — внизу слева.
     Знак-баннер с рисунком живёт по этому же правилу: селектор с двумя
     классами перебивает базовое правило знака, где слоёв три. */
  --sloi:
    linear-gradient(200deg,
      rgba(10,13,18,.10) 0%, rgba(10,13,18,.42) 46%,
      rgba(10,13,18,.88) 80%, rgba(10,13,18,.95) 100%),
    var(--kartinka),
    var(--fon-kart);
  background-size:var(--polosa) 100%, 100% 100%, cover, 100% 100%;
  background-position:left center, left center, center 32%, left center;
  background-repeat:no-repeat, no-repeat, no-repeat, no-repeat;
}

/* ---- плеер на страницах видеоуроков ----
   Порядок такой: путь, учебник, воздух, что за урок, кадр, плейлист.
   Название урока стоит над кадром: под ним оно прижималось к плейлисту,
   а сверху у него своё место, и до кадра остаётся пустая полоса, чтобы
   текст не липнул к видео. */
.pleyer-wrap{margin-top:46px}
.pleyer-shapka{
  /* Заголовок страницы встаёт в столбик: над ним — глава (подзаголовок). */
  display:flex; flex-direction:column; align-items:flex-start;
  gap:8px; margin-bottom:28px; min-height:56px;
}
/* Глава — ПОД кадром: «Глава I. Эпоха Великих географических
   открытий». Над кадром остаётся название урока («§ 3. …»), а глава
   стоит подписью к списку плейлистов, который идёт за ней: она
   отвечает на вопрос «что в этих плейлистах». Появляется вместе с
   пунктом (её приносит плейлист), до выбора урока строки нет. */
.pleyer-podzag{
  max-width:88ch; font-size:26px; color:#8b95a5; line-height:1.3;
  hyphens:manual; overflow-wrap:break-word;
}
.pleyer-podzag[hidden]{display:none}
.pleyer-zag{
  flex:1 1 auto; min-width:0; font-size:40px; font-weight:600;
  line-height:1.2; color:#f3f5f9;
  hyphens:manual; overflow-wrap:break-word;
}
.pleyer{
  position:relative; width:100%; aspect-ratio:16 / 9;
  background:linear-gradient(165deg,#171f2a 0%,#0f141b 100%);
  border-radius:18px; overflow:hidden;
}
.pleyer-ramka{border:0}
/* Растягиваем на весь блок только кадр большого плеера. Баннерный кадр
   носит тот же класс — по нему его находит восстановление позиции, —
   но живёт в обычном потоке: абсолютный кадр в баннере не имел
   позиционированного предка и накрывал собой всю страницу: сверху
   чернел экран, а нажатия по списку лекций доставались кадру. */
.pleyer .pleyer-ramka{position:absolute; inset:0; width:100%; height:100%}
/* Кнопки вариантов плейлиста — под плеером. Появляются, только когда
   вариантов больше одного: уроки по параграфам, короткие пересказы,
   разборы домашних заданий, повторение. */
/* ---- плейлисты под кадром ----
   Под кадром стоит СПИСОК ПЛЕЙЛИСТОВ, а не их содержимое: сами уроки
   живут в панели справа, и держать их ещё и на странице незачем —
   страница уезжала на несколько экранов. Название плейлиста — строка,
   нажатие открывает этот плейлист в панели.
   Оформление — как у пунктов бокового меню (a.panel-plitka): обычный
   текст без подложки и полосы, при наведении серая подложка, а
   открытый плейлист отмечен подложкой и жёлтой скруглённой полосой
   слева. Строки идут тем же классом, поэтому вид у них буквально один
   и тот же — отдельных правил под кадром нет. */
/* ---- под кадром: глава, разделительная линия, плейлисты, разделы ----
   Порядок такой: кадр, глава (подзаголовок), линия-разделитель, надпись
   «Плейлисты», строки плейлистов, надпись «Разделы» и плашки разделов —
   те же, что на странице выбора материала. Линия такая же, как под
   шапкой панели (2 px, #2a3340): она отделяет кадр от списков. */
.pleyer-niz{margin-top:20px}
.pl-razd{height:0; border-top:2px solid #2a3340; margin:24px 0 0}
/* Надпись стоит на левом краю, как «Пройдено …» под полем и как сами
   плашки ниже: раньше у неё было своё поле слева, и она уходила вправо
   от всего остального. */
.pl-zagolovok{
  font-size:21px; color:#8b95a5; margin:22px 0 12px;
  hyphens:manual; overflow-wrap:break-word;
}
.pl-vse{margin-top:0}
.pl-plitka{margin-bottom:2px}
/* Плашки разделов под плейлистами: те же плитки, что на странице
   предмета, поэтому и вид, и размер — оттуда. Отступ сверху — тот же,
   что от надписи над кадром до текста выше неё (46 px): блок отделён
   от статистики так же, как шапка страницы от строки учебника. */
.pl-razdely{margin-top:46px}
.pl-razdely > .pl-polosa{position:relative; margin-top:14px}
/* Сколько полоса выходит за поля страницы: ровно до краёв окна. Это поля
   страницы (те же, что у .wrap) плюс пустое место вокруг блока, если окно
   шире его. Считается от ширины рабочей зоны (100cqw), а не окна: открытая
   панель отнимает место справа, и полоса не должна уезжать под неё. В
   браузере без контейнерных запросов — только поля, до края блока.
   Один пиксель справа не отдаём: дробные доли при вылете во всю ширину
   давали бы странице горизонтальную полосу прокрутки. */
:root{--pl-vydvizhenie:calc(clamp(20px, 4cqw, 44px) +
        max(0px, (100cqw - SHIRINA-STRANICYpx) / 2))}
@supports not (width:1cqw){
  :root{--pl-vydvizhenie:clamp(20px, 4vw, 44px)}
}
/* Плашки идут ПОЛОСОЙ в один ряд с прокруткой, а не сеткой: разделов
   бывает пять-шесть, и сеткой они уводили бы низ страницы далеко вниз,
   хотя это выход «на всякий случай», а не главное на странице. Видно
   две с половиной плашки — половина третьей говорит, что за краем ещё
   есть. На телефоне то же самое, но видна одна плашка и половина
   следующей: так делают подборки в YouTube, и это понятно без подписи.
   Полоса идёт во всю ширину экрана, а не обрывается по ширине блока: за
   краем видно обрезанную плашку, и обрезка приходится на край экрана, как
   в подборках YouTube, Rutube и Canva. Внутренним полем того же размера
   первая плашка возвращается на место надписи «Ещё по курсу». Полосы
   прокрутки нет: листают пальцем и стрелками. */
.pl-razdely .setka{
  display:flex; align-items:stretch; gap:24px;
  overflow-x:auto; overscroll-behavior-x:contain;
  scroll-snap-type:x proximity; scroll-behavior:smooth;
  /* Прилипание — к тому же месту, где плашки стоят в покое (к полю
     страницы), иначе браузер подтянул бы первую плашку к самому краю
     экрана и она разошлась бы с надписью. */
  scroll-padding-inline:var(--pl-vydvizhenie);
  margin:0 calc(1px - var(--pl-vydvizhenie)) 0 calc(-1 * var(--pl-vydvizhenie));
  padding:0 var(--pl-vydvizhenie);
  scrollbar-width:none;
}
.pl-razdely .setka::-webkit-scrollbar{display:none}
.pl-razdely .setka > a.plitka{
  flex:0 0 auto; width:calc((100% - 48px) / 2.5); scroll-snap-align:start;
}
/* Сколько плашек видно, считаем от ширины РАБОЧЕЙ ЗОНЫ, а не от блока:
   полоса идёт во всю ширину, и «две с половиной» остаются теми же на
   любой ширине — иначе за полями страницы вылезала бы четвёртая
   (в браузерах без контейнерных запросов остаётся счёт от блока —
   там полоса и не выходит за него). */
@supports (width:1cqw){
  .pl-razdely .setka > a.plitka{width:calc((100cqw - 48px) / 2.5)}
}
/* Подсказка о прокрутке: надпись с рукой посреди полосы. Показывается
   только там, где листают пальцем, — на устройствах с мышью полоса
   листается стрелками и колесом, и подсказка там лишняя; и только пока
   список не сдвинули: сдвинули — дальше понятно без слов. Как в Tilda,
   рука ходит влево-вправо: движение и есть подсказка. */
.pl-podskazka{display:none}
@media (hover:none) and (pointer:coarse){
  .pl-polosa[data-kon="1"]:not([data-listano]) .pl-podskazka{
    display:flex; position:absolute; left:50%; top:50%; z-index:3;
    transform:translate(-50%,-50%); align-items:center; gap:9px;
    /* Ширина по надписи: надпись короткая, и переносить её на две
       строки не за чем. */
    width:max-content; max-width:88%;
    padding:9px 17px; border-radius:999px; pointer-events:none;
    background:rgba(10,13,18,.82); color:#f3f5f9; font-size:16px;
    box-shadow:0 6px 20px rgba(0,0,0,.35);
  }
  .pl-podskazka svg{
    width:24px; height:24px; display:block;
    animation:pl-rukoy 1.7s ease-in-out infinite alternate;
  }
}
@keyframes pl-rukoy{
  from{transform:translateX(-7px)}
  to{transform:translateX(7px)}
}

/* Стрелки листания — полупрозрачные круги поверх полосы, у самых краёв
   экрана: слева и справа, как в подборках YouTube, Rutube и Canva. Видно
   только ту, за которой есть ещё: в начале нет левой, в конце нет правой
   (что показывать, ставит скрипт сборки — см. gen_tv_paket.razdelov_setka). */
a.pl-strelka{
  position:absolute; top:50%; margin-top:-24px; z-index:2;
  width:48px; height:48px; border-radius:50%;
  display:flex; align-items:center; justify-content:center;
  background:rgba(10,13,18,.55); color:#f3f5f9;
  opacity:.6; text-decoration:none;
  transition:opacity .15s, background-color .15s;
}
a.pl-strelka svg{width:26px; height:26px; display:block}
a.pl-strelka:hover, a.pl-strelka:focus{opacity:1; background:rgba(10,13,18,.9)}
a.pl-strelka-nazad{left:calc(6px - var(--pl-vydvizhenie))}
a.pl-strelka-nazad svg{transform:rotate(90deg)}
a.pl-strelka-vpered{right:calc(6px - var(--pl-vydvizhenie))}
a.pl-strelka-vpered svg{transform:rotate(-90deg)}
.pl-polosa[data-nach="0"] a.pl-strelka-nazad,
.pl-polosa[data-kon="0"] a.pl-strelka-vpered{opacity:0; visibility:hidden}
@container stranica (max-width:639px){
  /* Телефон: одна плашка и половина другой — видно, что есть ещё.
     Стрелки меньше и бледнее: листают здесь пальцем, а круг — подсказка,
     что за краем есть ещё. */
  .pl-razdely .setka{gap:16px}
  .pl-razdely .setka > a.plitka{width:62%}
  .pl-razdely .setka > a.plitka .nazv{font-size:26px}
  .pl-razdely .setka > a.plitka .poyas,
  .pl-razdely .setka > a.plitka .skolko{font-size:17px}
  a.pl-strelka{width:40px; height:40px; margin-top:-20px; opacity:.5}
  a.pl-strelka svg{width:22px; height:22px}
}

/* Отступа у всего списка больше нет: строки панели и строки под кадром
   стоят на одном месте — от края панели их отделяет ровно внутреннее
   поле строки (18 px, из них 6 px — под флажок). Так номер параграфа
   и текст стоят ближе к кромке, как в списках YouTube. */

/* Плейлист — такая же выезжающая панель, как меню, и в тех же
   границах: та же ширина, тот же выезд, тот же крестик. Открывается
   сразу при входе на страницу видеоуроков. Вдвоём они не открываются:
   открыли меню — плейлист закрылся, и наоборот. */
/* Полоса под ручку ширины: сама ручка стоит слева от панели и без
   этого запаса накрывала бы содержимое страницы — на узком окне она
   перекрывала даже кнопки уведомления над кадром. */
body.pleylist-otkryto{padding-right:calc(var(--panel-shirina) + 10px)}

#pleylist-panel{transform:translateX(100%); visibility:hidden;
  transition:transform .32s ease, visibility 0s linear .32s}
body.pleylist-otkryto #pleylist-panel{transform:none; visibility:visible;
  transition:transform .32s ease, visibility 0s linear 0s}
.pleylist{margin:0; padding:0}

/* Пока урок не выбран, в кадре пусто — но не чёрное: тёмная подложка,
   вопрос стоит в шапке над кадром. Когда урок уже смотрели, в кадре
   стоит он сам на паузе, а поверх нижней части ложится карточка:
   что это за урок и что делать дальше. Видео за карточкой не играет. */
/* Кнопка плейлиста — на самом кадре, в правом верхнем углу: панель
   закрывают крестиком, а вернуть её можно только отсюда. Значок свой,
   плееру Rutube он не мешает: у него свои кнопки внизу. */
a.pleyer-knopka{
  position:absolute; top:16px; right:16px; z-index:6;
  display:inline-flex; padding:10px; border-radius:12px; line-height:0;
  background:rgba(10,13,18,.72); color:#f3f5f9;
  border:3px solid transparent;
}
a.pleyer-knopka svg{width:34px; height:34px; display:block}
a.pleyer-knopka:hover, a.pleyer-knopka:focus{
  border-color:#ffd23f; background:rgba(10,13,18,.92);
}
/* ---- уведомление над кадром ----
   Пока кадр достаточно широкий, карточка лежит ПОВЕРХ него: кадр
   вставлен абсолютно и без этого рисовался выше неё — уведомление
   «Вы остановились на параграфе…» было в разметке, а на экране нет.
   Когда места мало (узкое окно или открытая панель), карточка уходит
   ПОД кадр: над кадром шириной в ладонь она всё равно не читается.
   Размеры считаем от ширины кадра, а не окна: страницу сдвигает
   панель плейлиста, и окно о ней ничего не знает. */
.pleyer-mesto{position:relative; container-type:inline-size}
.pleyer-vybor{display:flex; justify-content:center; margin-top:16px}
.pleyer-vybor .vybor-karta{width:100%; max-width:920px}
.vybor-karta{
  position:relative; min-width:0;
  display:flex; flex-direction:column; gap:clamp(12px, 1.4vw, 18px);
  background:linear-gradient(180deg, rgba(10,13,18,.82), rgba(10,13,18,.96));
  border-radius:16px;
  padding:clamp(14px, 1.7vw, 22px) clamp(16px, 2vw, 26px);
}
@supports (width: 1cqw){
  /* Там, где браузер знает ширину кадра, всё считается от неё. */
  .vybor-karta{gap:clamp(12px, 1.4cqw, 18px);
    padding:clamp(14px, 1.7cqw, 22px) clamp(16px, 2cqw, 26px)}
  .vybor-tekst{font-size:clamp(18px, 2.3cqw, 32px)}
  .vybor-knopki{gap:clamp(10px, 1.2cqw, 16px)}
  a.vybor-knopka{font-size:clamp(17px, 2.15cqw, 30px);
    padding:clamp(9px, 1.2cqw, 16px) clamp(15px, 2cqw, 28px);
    border-radius:clamp(10px, 1cqw, 14px)}
  a.vybor-zakryt{width:clamp(36px, 4cqw, 52px); height:clamp(36px, 4cqw, 52px)}
  a.vybor-zakryt svg{width:clamp(18px, 2cqw, 26px); height:clamp(18px, 2cqw, 26px)}
}
@container (min-width: 560px){
  .pleyer-vybor{
    /* Карточка возврата ложится на кадр и должна быть поверх всего,
       что на кадре есть, — в том числе поверх кнопки плейлиста
       (z-index 6). Иначе на узком кадре её кнопки оказывались под
       ней и нажать их было нельзя. */
    position:absolute; inset:0; z-index:7; margin-top:0;
    align-items:center; overflow:auto;
    padding:clamp(14px, 2cqw, 26px) clamp(16px, 2.2cqw, 30px);
    border-radius:18px;
    background:linear-gradient(180deg, rgba(10,13,18,.5), rgba(10,13,18,.86));
  }
}
.vybor-tekst{
  font-size:clamp(18px, 2.2vw, 32px);
  font-weight:600; color:#f3f5f9; line-height:1.2;
  hyphens:manual; overflow-wrap:break-word;
  padding-right:clamp(40px, 4.4vw, 60px); /* место под крестик */
}
.vybor-knopki{display:flex; gap:clamp(10px, 1.2vw, 16px); flex-wrap:wrap}
a.vybor-knopka{
  display:inline-block; text-decoration:none; border-radius:clamp(10px, 1vw, 14px);
  padding:clamp(9px, 1.2vw, 16px) clamp(15px, 2vw, 28px);
  font-size:clamp(17px, 2.15vw, 30px); font-weight:700;
  background:#ffd23f; color:#12161c; border:4px solid transparent;
  /* Кнопка не шире своей карточки: на узком окне кадр сжимается до
     полоски, и кнопка, выставленная по ширине текста, вылезала за
     карточку — её накрывала ручка открытой панели плейлиста.
     Текст в этом случае переносится, кнопка остаётся кликабельной. */
  min-width:0; max-width:100%; white-space:normal; overflow-wrap:break-word;
  text-align:center;
}
a.vybor-knopka.vtoraya{
  background:#2b3543; color:#f3f5f9; font-weight:600;
}
/* Крестик уведомления — в правом верхнем углу карточки, иконкой:
   слова «Закрыть» там не пишем, как и у панелей. Убирает карточку,
   кадр остаётся на паузе. В покое спокойный, жёлтый — на наведении. */
a.vybor-zakryt{
  position:absolute; top:clamp(8px, .9vw, 12px); right:clamp(8px, .9vw, 12px);
  display:flex; align-items:center; justify-content:center;
  width:clamp(36px, 4vw, 52px); height:clamp(36px, 4vw, 52px);
  border-radius:clamp(10px, 1vw, 14px); color:#c9d2df;
  border:3px solid transparent; text-decoration:none;
}
a.vybor-zakryt svg{width:clamp(18px, 2vw, 26px); height:clamp(18px, 2vw, 26px)}
a.vybor-zakryt:hover, a.vybor-zakryt:focus, a.vybor-zakryt:focus-visible{
  outline:none; border-color:#ffd23f; background:#202836; color:#f3f5f9;
}
a.vybor-knopka:focus, a.vybor-knopka:hover{
  outline:none; border-color:#f3f5f9;
  box-shadow:0 0 0 6px rgba(255,210,63,.28);
}
/* Пункт плейлиста — просто текст, как и название плейлиста над ним.
   Ни подложки, ни жёлтой чёрточки слева в покое: это строка списка,
   а не кнопка. Синим не делаем никогда: цвет наш, серый.
   Размер строки — 24 px: набрано по эталону YouTube и Rutube, где
   строка списка заметно компактнее заголовка. Место под флажок
   оставлено у КАЖДОЙ строки (отступ слева 18 px, из них 6 px — под
   чёрточку), поэтому играющий пункт встаёт на своё место и список
   от него не сдвигается ни на пиксель. */
a.trek{
  display:flex; position:relative; align-items:baseline; gap:10px;
  text-decoration:none;
  color:#c9d2df; background:none;
  border:3px solid transparent; border-radius:10px;
  /* Отступ слева 28 px: номер параграфа не липнет к кромке строки —
     у играющего пункта там ещё и жёлтая полоса. */
  padding:8px 14px 8px 28px;
  hyphens:manual; overflow-wrap:break-word;
}
/* Наведение и фокус — серая подложка и жёлтая рамка. Рамка одинарная;
   у плашек при наведении рамка двойная (жёлтая плюс свечение), здесь
   свечения нет. Обычный фокус (клик мышью) — только подложка. */
a.trek:hover, a.trek:focus, a.trek:focus-visible{
  background-color:#1b212b; outline:none; color:#f3f5f9;
}
a.trek:hover, a.trek:focus-visible{border-color:#ffd23f}
/* Колонка номера: ширина по самому длинному номеру («§ 45» — 50 px при
   24 px), номер прижат ВЛЕВО, к самому краю строки: тогда «§» у всех
   строк стоит на одном месте, а до темы ровно один зазор (10 px).
   Так «§ 1» и «§ 45» начинают тему на одном месте, а пустоты между
   номером и текстом нет (было 58 px и 12 px — от номера до темы
   оставалась широкая дыра). Диапазон («§ 10–11») колонку растягивает
   сам — так и в учебнике. */
.trek-nomer{
  /* Колонка ФИКСИРОВАННОЙ ширины: 58 px — по самому широкому номеру
     («§ 45» — 50 px, «§ 10,» — 58 px при 24 px). Парные параграфы стоят
     двумя строками (см. nomer_stolbikom), поэтому номер больше не
     растягивает колонку и темы во всех строках начинаются на одном
     месте. Было `min-width:50px` — «§ 10–11» (93 px) раздвигала свою
     строку, и список выглядел порванным. */
  flex:0 0 58px; width:58px; text-align:left;
  font-size:24px; color:#8b95a5; line-height:1.3;
}
/* У кино и лекций в колонке не номер, а время проигрывания
   («1 ч 21 мин» — 78 px при 24 px). Фиксированная колонка его не
   вмещает, и время ломается на три строки, поэтому таким строкам колонку
   даём по содержимому, а перенос запрещаем. */
.trek-nomer.trek-vremya{flex:0 0 auto; width:auto; min-width:58px;
  white-space:nowrap}
/* Пункт без параграфа («Введение», «Итоговое повторение»): в колонке
   номера — кольцо с точкой, размером с цифру. По высоте оно стоит на
   первой строке темы, а не по центру всего пункта. */
.trek-kolco{display:flex; align-items:center; justify-content:flex-start;
  align-self:flex-start; height:1.3em}
.trek-kolco svg{width:22px; height:22px; display:block}
.trek-tema{flex:1 1 auto; min-width:0; font-size:24px; line-height:1.3}
/* ИГРАЮЩИЙ пункт — единственная строка с отметкой, и отметка эта такая
   же, как у плашки предмета (см. a.plitka): жёлтая полоса во всю высоту
   строки у левого края и подложка потемнее. Рамки в покое нет — у плашек
   её тоже нет, жёлтая появляется под курсором и на фокусе. Раньше здесь
   была короткая чёрточка посреди строки: она читалась как случайная
   метка, а не как выделение. */
a.trek.aktiven, a.nastr-stroka.aktiven, a.panel-plitka.tekushchiy{
  --polosa-stroki:8px;
  --fon-stroki:linear-gradient(#232c38, #232c38);
  background-image:linear-gradient(#ffd23f, #ffd23f), var(--fon-stroki);
  background-repeat:no-repeat, no-repeat;
  background-position:left center, left center;
  background-size:var(--polosa-stroki) 100%, 100% 100%;
  background-origin:border-box, border-box;
  background-clip:border-box, border-box;
  border-color:transparent;
  color:#f3f5f9;
}
/* У плашек меню (текущая страница, открытый плейлист под кадром) жёлтая
   рамка остаётся: плашка и в покое отмечена рамочкой, а полоса — та же,
   что у играющего пункта. У строк списка рамки нет — там в покое рамок
   не бывает ни у одной строки. */
a.panel-plitka.tekushchiy{border-color:#ffd23f}
/* Активная вкладка плейлиста под видеокадром — это именно пункт
   плейлиста, не активная страница: поэтому она повторяет .trek.aktiven
   из панели и не получает отдельной жёлтой рамки. */
a.pl-plitka.tekushchiy{border-color:transparent}
a.trek.aktiven .trek-nomer, a.nastr-stroka.aktiven .nastr-schet{
  color:#ffd23f;
}
/* Заголовок группы («Глава I. Первобытное общество») — подпись к идущим
   за ним пунктам. Он серый, как название учебника: его видно, но он не
   спорит с пунктами и не сбивает с ориентировки. Отступ слева 21 px —
   ровно там начинается колонка номеров, поэтому заголовок стоит над
   номерами, а не левее их. */
.trek-gruppa{
  font-size:21px; color:#8b95a5; margin:20px 0 14px; padding-left:31px;
  hyphens:manual; overflow-wrap:break-word;
}
.trek-gruppa:first-child{margin-top:0}


/* ---- ТРЕНАЖЁРЫ ----
   Страница устроена как видеоуроки: то же поле, та же выезжающая панель
   справа, та же пояснительная строка внизу. Своё у тренажёра только
   содержимое поля. Порядок в нём такой: верхняя строка (где мы в заходе,
   собранные кристаллы, «на весь экран»), вопрос на треть высоты, ответы
   в один столбик, подсказка «Подробнее» и строка управления. Поле держим
   тех же пропорций 16:9, что и кадр: страница не «прыгает» при смене
   тренажёра. */
/* Поле — сетка из двух рядов: верхняя строка и всё остальное. Сетка
   (а не flex) нужна ради высоты: она у ряда известна, и потому «треть
   поля» у вопроса считается от неё, а не от собственного текста. */
.trener-karta{
  position:relative; z-index:5; flex:1 1 auto; min-width:0;
  display:flex; flex-direction:column;
  gap:14px; padding:3.5% 5%;
}
.trener-telo{flex:1 1 auto; display:flex; flex-direction:column;
  min-height:0; min-width:0}
/* Заголовка в карточке нет: на пустом экране — только кнопка «Начать
   тренировку», а что решаем, видно в надписи над кадром. */
/* Верхняя строка поля: слева — где мы в заходе, справа — собранные
   кристаллы и «на весь экран». Счёт вопроса стоит здесь, а не внизу:
   это подпись ко всему кадру, а не кнопка. Вне захода он пустой и места
   не занимает, но строка остаётся — иначе кристаллы прыгали бы вниз. */
/* Строка переносится, если счёт и награды не влезают в одну: иначе
   она растянула бы собой всё поле шире кадра. */
.trener-verh{display:flex; align-items:center; flex-wrap:wrap;
  gap:8px 14px; flex:0 0 auto; min-width:0;
  /* Все элементы верхней строки центрируются по кнопке полного экрана.
     Ряд поднимается из внутреннего отступа поля к той же линии, что и
     кнопка плейлиста на видеокадре: 16 px от верхнего края экрана. */
  margin-top:calc(-3.5% + 16px);
  /* Строка знаков стоит над пустым экраном: на пустом экране кнопка —
     всё поле, и значки должны остаться нажимаемыми поверх неё. */
  position:static; z-index:2}
.trener-schet-za{font-size:20px; color:#8b95a5; margin-right:14px;
  white-space:nowrap}
.trener-schet-za b{color:#dbe3ee; font-weight:600}
.trener-schet-za[hidden]{display:none}
/* Счёт ошибок — рядом с кристаллом: красный крестик и число, и число
   тоже красное: это один знак, а не подпись к нему. Крестик нарисован
   как кристалл — тот же размер и тот же штрих (см. знак «ошибка»):
   знаки стоят рядом в одной строке и читаются парой. */
.trener-oshibki-schet{
  display:flex; align-items:center; gap:6px;
  font-size:20px; color:#ff6b6b; white-space:nowrap;
  /* От кристаллов счёт отодвинут вдвое против прочих знаков строки:
     это два разных счёта — ошибки и кристаллы, — и вплотную они
     читались одним знаком. */
  margin-right:8px;
}
.trener-oshibki-schet[hidden]{display:none}
.trener-oshibki-schet .trener-krestik{display:flex; color:#ff6b6b}
.trener-oshibki-schet .trener-krestik svg{width:26px; height:26px;
  display:block}
.trener-oshibki-schet b{color:#ff6b6b; font-weight:600}
/* Кристаллы — награда за верные ответы. Кристалл один, а рядом число:
   сколько их собрано. Ряд из пяти гнёзд показывал счёт хуже — по числу
   видно точно, и место оно занимает одно. Счёт тот же, что у «Верно»
   под полем, — числа не должны расходиться. */
.trener-nagrady{display:flex; align-items:center; gap:9px; flex:0 0 auto}
/* Настройка прохождения стоит без заголовка: отделяем её от списка
   учебников тем же отступом, что был у снятого заголовка, — иначе
   строка прилипала к «Всеобщей истории» и читалась вместе с ней. */
#nastr-avto{margin-top:26px}
/* Настройка прохождения — серой строкой, как надписи разделов («Выбор
   учебника»): это настройка, а не действие, и цветом она читается
   быстрее слов. */
#nastr-avto .nastr-tekst{color:#8b95a5; font-size:21px}

/* Пока не собран ни один кристалл, счётчика нет вовсе: серый кристалл
   с нулём выглядел поломкой. Скрытое — спрятано: у блока выше свой
   `display`, и без этого правила `hidden` его не гасит. */
.trener-nagrady[hidden]{display:none}
.trener-kristally{display:flex; align-items:center}
.trener-kristally svg{width:26px; height:26px; display:block; color:#39424f}
.trener-kristally svg.vzyt{
  color:#8fd8ff; filter:drop-shadow(0 0 7px rgba(143,216,255,.45));
}
.trener-chislo{font-size:22px; color:#8fd8ff; font-weight:600}

/* Стрелки листания по вопросам — кнопки со значком: назад и вперёд.
   Оформлены теми же кнопками, что и всё на странице (см.
   a.knopka-malaya): та же подложка, та же жёлтая рамка при наведении,
   только вместо надписи — значок. За стрелкой без хода (первый вопрос,
   ответ ещё не дан) — серая надпись, не ссылка. Стоят они в нижней
   строке поля, у правого нижнего угла (см. .trener-upravlenie).
   Задание — вопрос и ответы — идёт одной колонкой во всю ширину поля. */
.trener-forma{
  flex:1 1 auto; min-height:0; min-width:0;
  display:flex; flex-direction:column; gap:12px;
}
a.trener-strelka, span.trener-strelka{
  display:inline-flex; font-size:19px; padding:7px 13px; line-height:0;
  border:3px solid transparent; border-radius:12px; text-decoration:none;
  background:#232a35; color:#dbe3ee;
}
a.trener-strelka svg, span.trener-strelka svg{width:26px; height:26px; display:block}
a.trener-strelka:hover, a.trener-strelka:focus{
  border-color:#ffd23f; background:#2b3440; color:#f3f5f9; outline:none;
}
span.trener-strelka.tuskly{color:#6f7887; background:#1c222c; cursor:default}
/* Значки поля — тот же вид, что у кнопки поверх кадра видео («Открыть
   плейлист»): полупрозрачная тёмная подложка, значок 34×34, тонкая
   рамка, которая при наведении загорается жёлтым. Раньше здесь были
   крупные плашки 36×36 с серой подложкой — на кадре они читались
   заплатками, а эталон у нас страница видео. */
.trener-znachki{display:block; flex:0 0 auto; margin:0; padding:0}
/* Вопрос стоит вплотную к полноэкранной кнопке: 8 px между двумя
   одинаковыми 60-пиксельными полями. Обе координаты считаются от поля,
   как у кнопки плейлиста на видеокадре. */
#trener-podskazka-znak{position:absolute; top:16px; right:84px}
a.trener-znachok, span.trener-znachok{
  display:inline-flex; padding:10px; line-height:0;
  border:3px solid transparent; border-radius:12px;
  background:rgba(10,13,18,.72); color:#f3f5f9; text-decoration:none;
}
a.trener-znachok svg, span.trener-znachok svg{width:34px; height:34px; display:block}
/* Разворот — ровно тот же знак, что вызов плейлиста поверх видеокадра:
   16 px от верхнего и правого края поля, поле 10 px, знак 34 px. Он
   не участвует в промежутках счётов, а занимает своё место у угла. */
a#trener-vo-ves-ekran{position:absolute; top:16px; right:16px;
  background:rgba(10,13,18,.72); border-color:transparent}
a#trener-vo-ves-ekran:hover, a#trener-vo-ves-ekran:focus{
  background:rgba(10,13,18,.92); border-color:#ffd23f}
a.trener-znachok:hover, a.trener-znachok:focus{
  border-color:#ffd23f; background:rgba(10,13,18,.92); outline:none;
}
/* Пока подсказывать нечего (ответа ещё нет), значок вопроса немой:
   подложка та же, что у живого, а значок приглушён — как у немой
   стрелки. */
span.trener-znachok.tuskly{
  background:rgba(10,13,18,.72); color:#6f7887; cursor:default;
}
/* Спрятанное — спрятано: у значка свой `display`, и без этого правила
   `hidden` его не гасит (знак вопроса на пустом экране). */
span.trener-znachok[hidden], a.trener-znachok[hidden]{display:none}
/* Знак вопроса — жёлтый: это приглашение заглянуть в подсказку.
   Подложки под ним нет: он и так читается, а тёмный квадрат рядом
   с ответами выглядел ещё одной кнопкой. */
a.trener-znachok.vopros, span.trener-znachok.vopros{
  color:#ffd23f; background:none;
}
span.trener-znachok.vopros.tuskly{color:#7d8695}
/* Живой значок вопроса нажимается — он и есть кнопка. */
span.trener-znachok.vopros:not(.tuskly){cursor:pointer}
span.trener-znachok.vopros:not(.tuskly):hover,
span.trener-znachok.vopros:not(.tuskly):focus{
  border-color:#ffd23f; background:none; outline:none;
}

/* Низ панели настроек: сброс результатов. Лежит вне области списка
   (та прокручивается), поэтому всегда у самого нижнего края экрана —
   сколько бы настроек ни набралось. Кнопка во всю ширину: в панели
   строки тоже идут во всю ширину, и так она читается отдельным делом,
   а не случайной кнопкой. */
.panel-niz{
  /* Линия раздела над кнопкой сброса стоит вдвое выше прежнего: между
     ней и кнопкой было 12 px, и кнопка читалась приклеенной к линии. */
  flex:0 0 auto; padding:24px 14px 16px;
  background:#141a22; border-top:2px solid #2a3340;
}
.panel-niz #trener-sbros{
  display:block; width:100%; text-align:center; white-space:normal;
}
/* Карточка-приглашение стоит в поле до первого захода: что решаем,
   сколько вопросов и кнопка «Начать». Как только заход начался, её
   место занимает вопрос — та же рамка поля. */
/* Пустой экран — сама кнопка. Отдельной плашки в нём нет: поле пустует,
   и нажимается всё поле. Приглашение лежит поверх поля (`absolute`),
   поэтому поле растёт не от него, а от правила ниже — иначе на телефоне
   пустой экран схлопнулся бы в одну строку знаков. Пояснений и числа
   вопросов здесь нет: как идут вопросы, видно с первого же вопроса. */
.trener-karta.pusto .trener-telo{min-height:min(44vh, 470px)}
.trener-priglashenie{
  position:absolute; inset:12px; display:flex; align-items:center;
  justify-content:center; text-align:center;
}
/* «Начать тренировку» — белый контур во всё поле, по его ширине, и
   крупная белая надпись по центру. Так экран и читается кнопкой: целиться
   не во что, мишень — всё поле. */
a.trener-nachat{
  display:flex; align-items:center; justify-content:center;
  width:100%; height:100%; box-sizing:border-box;
  padding:16px; border:0; border-radius:16px;
  color:#ffffff; font-size:clamp(28px, 4.4cqw, 52px); font-weight:600;
  line-height:1.2; text-decoration:none; white-space:normal;
  background:transparent;
}
a.trener-nachat:hover, a.trener-nachat:focus, a.trener-nachat:active{
  outline:none; border:0; color:#ffffff;
  background:rgba(255,255,255,.06);
}

/* У тренажёра поле — не кадр 16:9, а рабочий экран: он растёт по высоте
   того, что в нём стоит (четыре ответа в два ряда, раскрытый рассказ),
   и ничего не прокручивает внутри себя — прокручивается страница.
   Пропорции кадра оставлены только плееру с видео. */
.pleyer.trener-pleyer{aspect-ratio:auto; display:flex; min-height:min(50vh, 560px);
  overflow:visible}
/* Всплывающие подписи тренажёра должны лежать поверх рабочего поля,
   а не обрезаться границей `.pleyer`. */
.trener-pleyer .trener-verh{z-index:20}
.trener-pleyer .trener-znachki,
.trener-pleyer .trener-schet-za,
.trener-pleyer .trener-oshibki-schet,
.trener-pleyer .trener-nagrady{align-self:center}
@container stranica (max-width:639px){
  .pleyer.trener-pleyer{min-height:0}
}

/* ---- ДВИЖОК ТРЕНАЖЁРА: вопрос, варианты, подсказка ----
   В поле встаёт вопрос захода: сам вопрос крупно по центру трети поля,
   ниже — четыре варианта ответа во всю ширину (по одному в строке:
   в две колонки длинные определения не влезали и обрезались), потом
   строка управления. Отзыва-плашки нет: верный вариант виден по зелёной
   рамке, а рассказ о событии прячется под ссылкой «Подробнее» — иначе
   слова заслоняли ответы. Никаких окон и переходов: всё в той же рамке
   16:9, где стояла карточка. Цвета ответа — единственное место в
   проекте, где есть зелёный и красный: они и значат «верно» и «неверно»
   без слов. */
.trener-igra{
  flex:1 1 auto; min-height:0; min-width:0; display:none;
  flex-direction:column; gap:12px;
}
.trener-igra.vidna{display:flex}
/* Итог захода — короткий: ставим его по середине поля, как приглашение. */
.trener-igra.itog{justify-content:center}
.trener-schet{
  display:flex; justify-content:space-between; gap:20px;
  font-size:21px; color:#8b95a5;
}
.trener-schet b{color:#dbe3ee; font-weight:600}
/* Вопрос — двумя строками: сверху заголовок, что это за вопрос («Дата»,
   «Определение»), под ним подзаголовком сам вопрос. Так у всякого
   вопроса видно, о чём он, ещё до чтения, и вопросы разных видов
   выглядят одинаково. */
.trener-vopros-blok{
  flex:0 0 auto; display:flex; flex-direction:column;
  align-items:center; justify-content:center; gap:10px;
  text-align:center;
  /* Отступы до верхней строки и до ответов — постоянные. Они сняты
     с задания в три строки: короткий вопрос воздуха не оттягивает,
     а длинный в те же отступы и упирается. Раньше блок занимал треть
     поля, и на коротком вопросе вокруг него зияла пустота. */
  padding:26px 0 30px;
}
.trener-vopros-zag{
  font-size:40px; font-weight:600; line-height:1.2; color:#f3f5f9;
  hyphens:manual; overflow-wrap:break-word;
}
.trener-vopros-pod{
  margin:0; font-size:26px; line-height:1.35; color:#98a2b3;
  max-width:70ch; hyphens:manual; overflow-wrap:break-word;
}
/* Варианты стоят по ширине поля: короткие (годы, термины) — плашками
   в два столбца, не больше: четыре ответа ложатся двумя ровными рядами
   по два. Ряды сверху и снизу всегда одинаковые — столбцов чётное
   число. Длинные ответы (значения определений) идут в один столбец.
   Что именно перед нами, решает страница по длине текста (классы
   v-ryad и v-stolbik), а на телефоне любой набор становится одним
   столбцом: две колонки на узком экране — это уже не плашки, а щели. */
.trener-otvety{
  display:grid; grid-template-columns:minmax(0, 1fr);
  gap:10px; width:100%;
}
.trener-otvety.v-korotkie{grid-template-columns:repeat(2, minmax(0, 1fr))}
.trener-otvety.v-ryad{grid-template-columns:repeat(2, minmax(0, 1fr))}
@container stranica (max-width:639px){
  .trener-otvety.v-ryad{grid-template-columns:minmax(0, 1fr)}
  /* А совсем короткие (годы, короткие термины) и на телефоне стоят
     двумя столбцами: в один они вытянули бы поле на три экрана, а сами
     занимают полторы строки. */
  .trener-otvety.v-korotkie{grid-template-columns:repeat(2, minmax(0, 1fr))}
}
a.trener-otvet{
  display:flex; align-items:flex-start; gap:12px;
  padding:9px 15px; border:3px solid #2a3340; border-radius:14px;
  background:#1a212b; color:#e8edf5; text-decoration:none;
  font-size:20px; line-height:1.35;
}
a.trener-otvet .trener-nomerok{
  flex:0 0 auto; min-width:30px; color:#8b95a5; font-weight:600;
}
a.trener-otvet .trener-tekst-otveta{
  flex:1 1 auto; min-width:0; overflow-wrap:break-word;
}
a.trener-otvet:hover, a.trener-otvet:focus, a.trener-otvet:focus-visible{
  border-color:#ffd23f; background:#212a36; outline:none;
}
a.trener-otvet.verno{border-color:#3ecf8e; background:rgba(62,207,142,.10)}
a.trener-otvet.pokazat{border-color:#3ecf8e}
a.trener-otvet.neverno{border-color:#ff6b6b; background:rgba(255,107,107,.10)}
/* Место под галочку зарезервировано заранее. Иначе после выбора
   галочка отнимает ширину у текста, однострочный ответ переносится,
   и ячейка внезапно становится выше. Невидимая галочка места не
   занимает визуально, но сохраняет одинаковую геометрию до и после.
   Появляется только у выбранного/показанного ответа. */
a.trener-otvet .trener-galka{display:flex; visibility:hidden;
  flex:0 0 26px; color:#3ecf8e}
a.trener-otvet .trener-galka svg{width:26px; height:26px; display:block}
a.trener-otvet.verno .trener-galka,
a.trener-otvet.pokazat .trener-galka{visibility:visible}
/* Подсказка живёт в окне (см. окно подсказки выше): под вопросом
   и под ответами её больше нет — там она оттесняла ответы и прыгала
   при раскрытии. Слова «Верно!» и повтор выбранного ответа тоже
   убраны — их работу делает зелёная рамка. */
.trener-podrobno{
  display:flex; flex-wrap:wrap; align-items:center; gap:8px 18px;
  font-size:20px; color:#98a2b3;
}
a.trener-video{
  color:#ffd23f; text-decoration:none;
  border-bottom:2px solid rgba(255,210,63,.5);
}
a.trener-video:hover, a.trener-video:focus{border-bottom-color:#ffd23f}
/* ---- окно подсказки ----
   Рассказ о нынешнем вопросе открывается во всплывающем окне: оно встаёт
   на то же место и того же размера, что экран теста (координаты считает
   страница, см. shkPodskazka), а на телефоне — во всю ширину экрана.
   Внутри — только подсказка: рассказ целиком, учебник, страница и ссылка
   на видеоурок. Закрыть — крестик, Esc или нажатие по подложке. */
.trener-okno-podskazki{
  position:fixed; inset:0; z-index:130; display:none;
  background:rgba(8,11,15,.66);
}
.trener-okno-podskazki.vidno{display:block}
.trener-okno-karta{
  position:absolute; display:flex; flex-direction:column;
  background:#131a23; border:3px solid #2a3340; border-radius:18px;
  box-shadow:0 24px 60px rgba(0,0,0,.5);
}
.trener-okno-verh{
  display:flex; align-items:center; gap:16px; flex:0 0 auto;
  padding:16px 22px; border-bottom:2px solid #2a3340;
}
.trener-okno-zag{font-size:24px; color:#8b95a5; flex:1 1 auto; min-width:0}
a.trener-okno-zakryt{
  flex:0 0 auto; display:inline-flex; padding:7px 10px; line-height:0;
  border:4px solid transparent; border-radius:14px; color:#f3f5f9;
}
a.trener-okno-zakryt svg{width:30px; height:30px; display:block}
a.trener-okno-zakryt:hover, a.trener-okno-zakryt:focus{
  border-color:#ffd23f; background:#2b3443; outline:none;
}
.trener-okno-telo{
  flex:1 1 auto; min-height:0; overflow-y:auto; overscroll-behavior:contain;
  padding:22px 26px; scrollbar-width:thin;
  scrollbar-color:#3a4452 transparent;
}
.trener-okno-telo::-webkit-scrollbar{width:8px}
.trener-okno-telo::-webkit-scrollbar-thumb{background:#3a4452; border-radius:4px}
.trener-okno-telo .trener-poln{font-size:24px; line-height:1.5; color:#e8edf5;
  margin:0 0 16px}
.trener-okno-telo .trener-podrobno{font-size:21px; color:#98a2b3}
.trener-okno-telo a.trener-video{font-size:21px}
@container stranica (max-width:639px){
  .trener-okno-karta{border-radius:0; border:0}
  .trener-okno-verh{padding:14px 18px}
  .trener-okno-telo{padding:16px 18px}
  .trener-okno-telo .trener-poln{font-size:19px}
  .trener-okno-telo .trener-podrobno,
  .trener-okno-telo a.trener-video{font-size:17px}
}

/* Кнопка «Работа над ошибками» — одной рукой в двух местах: на
   странице под полем, во всю его ширину, а в полном экране — в нижней
   строке поля, в один ряд со стрелками. Вид один: та же рамка, то же
   скругление и тот же рост, что у однострочной плашки ответа; фон
   не залит, как у невыбранного ответа, — это ход в сторону, а не
   главное дело. Надпись — по середине, и без числа: счёт и так стоит
   в верхней строке поля. */
.trener-oshibki-knopka{
  display:flex; align-items:center; justify-content:center;
  width:100%; box-sizing:border-box; min-height:0; padding:8px 14px;
  border:3px solid #ff6b6b; border-radius:12px;
  background:#232a35;
  color:#dbe3ee; font-size:24px; line-height:1.2; text-align:center;
  text-decoration:none;
}
.trener-oshibki-knopka:hover, .trener-oshibki-knopka:focus{
  border-color:#ff6b6b; background:#2b3440; color:#f3f5f9; outline:none;
}
.trener-oshibki-knopka.net-oshibok{
  border-color:#2a3340; background:#232a35; color:#dbe3ee;
}
.trener-oshibki-knopka.net-oshibok:hover,
.trener-oshibki-knopka.net-oshibok:focus{
  border-color:#596575; background:#2b3440; color:#f3f5f9;
}
/* Сброс — кнопка, а не активный пункт: жёлтая отметка не используется.
   Высота и кегль остаются как у активного пункта меню. */
a#trener-sbros{
  display:flex; align-items:center; justify-content:center;
  width:100%; box-sizing:border-box; min-height:0; padding:8px 14px;
  border:3px solid transparent; border-radius:12px;
  background:#232a35; color:#dbe3ee;
  font-size:21px; line-height:1.2; text-align:center;
}
a#trener-sbros:hover, a#trener-sbros:focus{
  border-color:#3ecf8e; background:#2b3440; color:#f3f5f9;
  outline:none;
}
a#trener-sbros.sbros-preduprezhdenie,
a#trener-sbros.sbros-preduprezhdenie:hover,
a#trener-sbros.sbros-preduprezhdenie:focus{
  border-color:#ff6b6b; background:#232a35; color:#f3f5f9;
}
/* Под полем: от поля — 24 px, дальше вниз — обычный отступ страницы
   (46 px у плашек «Ещё по курсу»). */
.trener-oshibki-pod{margin:24px 5% 0}
.trener-oshibki-pod:empty{display:none}
/* ---- нижняя строка поля ----
   В ней счёт ошибок (только в полном экране) и стрелки листания —
   в один ряд: кнопка слева, стрелки справа, у правого нижнего угла.
   Пока ошибок нет, в строке одни стрелки (см. oshibki_knopka).
   От ответов строку отделяет большой отступ: вплотную к вариантам она
   читалась вместе с ними. «Дальше» отдельной кнопкой нет — вперёд ведёт
   стрелка; «Завершить» тоже нет: брошенное решение ничего не теряет. */
.trener-upravlenie{
  margin-top:auto; margin-bottom:calc(-3.5% + 16px);
  display:flex; align-items:center; gap:14px;
  padding-top:34px;
}
.trener-upravlenie .trener-vremya,
.trener-upravlenie .trener-strelka{
  height:46px; box-sizing:border-box; align-items:center;
}
.trener-upravlenie .trener-oshibki-v-pole{flex:1 1 auto; min-width:0;
  display:flex}
.trener-upravlenie .trener-oshibki-v-pole:empty{display:none}
/* Полоса времени — у нижнего края поля, в одной строке со стрелками:
   длинная тонкая дорожка во всю оставшуюся ширину, и жёлтая полоса
   наполняет её ровно за минуту, а когда минута прошла — начинает
   заново (см. vremya_* в движке тренажёра). Это не счёт и не скорость:
   по полосе видно, сколько идёт нынешняя минута. */
.trener-vremya{
  flex:0 0 auto; min-width:92px; height:46px; display:flex;
  align-items:center; justify-content:center;
  background:transparent; overflow:visible;
}
.trener-vremya-podpis{
  display:block; color:#8b95a5; font-size:18px; line-height:1;
  text-align:center; white-space:nowrap;
}
/* Стрелки — у правого нижнего угла окна. */
.trener-strelki{display:flex; align-items:center; gap:10px;
  justify-content:flex-end; flex:0 0 auto; margin-left:auto}
a.knopka-malaya, span.knopka-malaya{
  display:inline-block; font-size:19px; line-height:1.2; padding:7px 13px;
  border:3px solid transparent; border-radius:12px; text-decoration:none;
  background:#232a35; color:#dbe3ee;
}
a.knopka-malaya:hover, a.knopka-malaya:focus{
  border-color:#ffd23f; background:#2b3440; outline:none;
}
a.knopka-malaya.glavnaya{border-color:#ffd23f; color:#f3f5f9}
/* Немая кнопка — не ссылка вовсе: «Работа над ошибками», пока ошибок нет,
   и «Предыдущий вопрос» на первом вопросе — обычные серые надписи. */
span.knopka-malaya.tuskly, a.knopka-malaya.tuskly{
  color:#6f7887; background:#1c222c; cursor:default;
}
a.knopka-malaya.tuskly:hover{border-color:transparent}
/* Полный экран — разворот самого поля. Делаем его своим, а не браузерным
   (`requestFullscreen`): на компьютере и телевизоре он то есть, то нет,
   а в предпросмотре и во вложенном окне его и вовсе не дают — кнопка
   не срабатывала. Здесь окно разворачивает страница: поле встаёт поверх
   всего и растягивается на весь экран. Выход — тот же значок или Esc. */
body.trener-vo-ves-ekran{overflow:hidden}
body.trener-vo-ves-ekran .pleyer-mesto{
  position:fixed; inset:0; z-index:120; margin:0;
  background:#0f141b; display:flex; align-items:flex-start;
  justify-content:center; overflow-y:auto; overscroll-behavior:contain;
}
body.trener-vo-ves-ekran .pleyer-mesto #pleyer{
  width:min(100vw, calc(100vh * 16 / 9)); min-height:100vh;
  border-radius:0;
  /* `overflow:hidden` у кадра делает его прокруткой для липких строк, и
     строки перестают липнуть: уезжают вместе с полем. В полном экране
     кадру прятать нечего — поле и есть окно, — и прокрутка у него одна,
     у всего экрана. */
  overflow:visible;
}
/* Длинный вопрос выше экрана — поле прокручивается, а верхняя и нижняя
   строки липнут к краям: счёт и значки видны сверху, «Работа над
   ошибками» — снизу, сколько бы ответов ни было. Оформлены они как
   верхнее меню страницы: та же подложка, те же скруглённые углы, тот
   же воздух по краям — иначе строка читалась серой полосой от края
   до края. */
/* Воздух по краям даём один раз — полю, а не заданию: тогда липкие
   строки доходят до самых краёв экрана и отступ у них всегда один. */
body.trener-vo-ves-ekran .pleyer-mesto{padding:12px 0}
body.trener-vo-ves-ekran .trener-karta{padding:0 5%}
body.trener-vo-ves-ekran .trener-verh{
  position:sticky; top:0; z-index:6; transform:none;
  padding:12px 18px; background:#16202b; border-radius:18px;
}
/* Под полем в полном экране ничего нет: кнопка ошибок встаёт в нижнюю
   строку поля, а подложку у этой строки не заливаем — на весь экран
   и так смотришь в одно поле, и полоса под кнопками только мешала. */
body.trener-vo-ves-ekran .trener-oshibki-pod{display:none}
body.trener-vo-ves-ekran .trener-upravlenie{
  position:sticky; bottom:0; z-index:6;
  margin-bottom:0; padding:12px 18px; background:none; border-radius:0;
}
/* Искры: короткий салют вокруг галочки, только при верном ответе.
   Награда за ответ, а не украшение страницы. */
.trener-iskry{position:relative; display:inline-block; width:0; height:0}
.trener-iskry i{
  position:absolute; left:0; top:0; width:7px; height:7px;
  border-radius:50%; background:#ffd23f; opacity:0;
  animation:trener-iskra .8s ease-out forwards;
}
@keyframes trener-iskra{
  0%{transform:translate(-4px,-4px) scale(1); opacity:1}
  100%{transform:translate(var(--x), var(--y)) scale(.3); opacity:0}
}
/* Итог захода: вместо вопроса — счёт и кнопки. Кнопки крупные: сюда
   попадают мышью, а на телевизоре — пультом. */
.trener-igra .trener-knopki{display:flex; flex-wrap:wrap; gap:14px;
  margin-top:4px}
.trener-igra .trener-knopki .knopka{font-size:24px; padding:14px 20px;
  max-width:100%; overflow-wrap:break-word}
/* Узкое поле: кегль и поля меньше — иначе вопрос с четырьмя определениями
   не влезает в кадр 16:9.
   Правила стоят ПОСЛЕ общих: при равной точности выигрывает то, что
   ниже в файле, — иначе эти строки не сработали бы вовсе. */
@container stranica (max-width:959px){
  .trener-igra{gap:10px}
  .trener-vopros{font-size:26px}
  a.trener-otvet{font-size:19px; padding:9px 12px; gap:10px}
  .trener-schet, .trener-chto{font-size:17px}
  .trener-podrobno{font-size:17px}
  a.knopka-malaya, span.knopka-malaya{font-size:17px; padding:7px 12px}
  .trener-igra .trener-knopki .knopka{font-size:21px; padding:12px 16px}
}
/* Телефон и вертикальный планшет: кегль и поля ещё меньше — вопрос и
   четыре ответа должны помещаться в кадр. Настройки над кадром мельче:
   «Даты и определения · Всеобщая история» в сорок пикселей заняли бы
   пол-экрана. Кристаллы — помельче: их пять в ряд. */
@container stranica (max-width:639px){
  /* Телефон: вопросу и ответам — кегль и поля меньше, а воздуху вокруг
     вопроса — вдвое меньше: тут каждый пиксель на счету, и высокое поле
     приходится листать. */
  .trener-karta{padding:3% 4%; gap:10px}
  .trener-vopros-blok{padding:8px 0 12px; gap:6px}
  .trener-vopros-zag{font-size:26px}
  .trener-vopros-pod{font-size:19px}
  .trener-chto{font-size:16px}
  a.trener-otvet{font-size:17px; padding:8px 11px; gap:9px;
    border-width:2px}
  a.trener-otvet .trener-nomerok{min-width:24px}
  .trener-podrobno-telo{font-size:17px; padding:12px 14px}
  .trener-podrobno{font-size:16px}
  a.knopka-malaya, span.knopka-malaya{font-size:16px; padding:7px 11px}
  .trener-schet-za{font-size:17px}
  .trener-oshibki-schet{font-size:17px; gap:6px}
  .trener-oshibki-schet .trener-krestik svg{width:18px; height:18px}
  .trener-kristally svg{width:20px; height:20px}
  .trener-chislo{font-size:18px}
  .trener-upravlenie{padding-top:22px; gap:10px}
  .trener-oshibki-pod{margin-left:4%; margin-right:4%}
  .trener-oshibki-knopka{
    min-height:0; padding:8px 14px 8px 28px; border-width:3px; font-size:24px;
  }
  a#trener-sbros{padding:8px 14px; border-width:3px; font-size:21px}
  a.trener-strelka, span.trener-strelka{width:44px; height:44px}
  a.trener-strelka svg, span.trener-strelka svg{width:22px; height:22px}
}
/* Телефон и вертикальный планшет: кегль и поля ещё меньше — вопрос и
   четыре ответа должны помещаться в кадр. Подробности — ниже, в блоке
   при самих правилах тренажёра: там они и стоят после общих, иначе при
   равной точности проигрывали бы им. */

/* Статистики под полем нет вовсе: и счёт вопросов, и счёт ошибок стоят
   в верхней строке поля, «Работа над ошибками» — в нижней. Сноска
   об учебниках уехала в панель: её читает родитель, а не ребёнок. */
/* Шапка страницы тренажёра: кнопка настроек и подпись в одной строке,
   кнопка — слева, над левым верхним углом поля. Так её ищут там же, где
   начинают читать строку, а не на другом краю экрана. */
.trener-shapka{
  flex-direction:row; align-items:center; width:100%; gap:18px;
}
/* Над кадром — не имя страницы, а сами настройки: «Даты и определения ·
   История России · до § 12». Крупно, тем же кеглем, что подпись кадра на
   видеоуроках; второй строки под ними нет — настройки и есть подпись, а
   вторая строка повторяла бы их же. Строка бывает длинной, поэтому она
   тянется и переносится, а не обрезается многоточием. */
.trener-shapka .pleyer-zag{flex:1 1 auto; min-width:0; font-size:40px;
  font-weight:600; color:#b9c1d0}
/* На телефоне та же надпись мельче: «Даты и определения · Всеобщая
   история · до § 12» в сорок пикселей заняли бы пол-экрана. Правило
   стоит после общего — иначе при равной точности общее побеждало бы. */
@container stranica (max-width:639px){
  .trener-shapka .pleyer-zag{font-size:24px}
  /* На телефоне первая строка мельче (24 px, междустрочный 1,2 —
     28,8), и подъём кнопки считается по ней. */
  a.nastr-knopka{margin-top:0}
}
/* Кнопка настроек — первая в строке, слева. Вид тот же, что у кнопки
   плейлиста на кадре: тёмная плашка с иконкой, жёлтая рамка под курсором
   и на фокусе. */
a.nastr-knopka{
  flex:0 0 auto; margin-left:auto; display:inline-flex; padding:10px;
  align-self:center; margin-top:0; border-radius:12px;
  /* Кнопка стоит по ПЕРВОЙ строке надписи, а не по её середине: надпись
     бывает в две строки, и посередине кнопка уезжала к нижней строке.
     Первая строка надписи — 48 px (кегль 40, междустрочный 1,2), её
     середина на 24 px от верха; знак кнопки — 34 px в рамке 3 и поле
     10, его середина на 30 px. Отсюда подъём на 6 px. */
  margin-top:-6px;
  line-height:0; background:rgba(10,13,18,.72); color:#f3f5f9;
  border:3px solid transparent;
}
a.nastr-knopka svg{width:34px; height:34px; display:block}
a.nastr-knopka:hover, a.nastr-knopka:focus{
  border-color:#ffd23f; background:rgba(10,13,18,.92);
}

/* ---- НАСТРОЙКИ ТРЕНАЖЁРА В ПАНЕЛИ ----
   Панель тренажёра — не список уроков, а настройки: что решаем и до
   какого параграфа. Устроены они по
   типу левого меню: та же шапка с крестиком, тот же простой список,
   та же отметка у выбранной строки (жёлтая полоса и подложка потемнее).
   Разделы размечают список надписями — как заголовки глав в плейлисте. */
.nastr-zag{
  font-size:21px; color:#8b95a5; margin:26px 0 10px; padding-left:28px;
  hyphens:manual; overflow-wrap:break-word;
}
.nastr-zag:first-child{margin-top:0}

a.nastr-stroka{
  display:flex; position:relative; align-items:baseline; gap:10px;
  text-decoration:none; color:#c9d2df; background:none;
  border:3px solid transparent; border-radius:10px;
  padding:8px 14px 8px 28px;
  hyphens:manual; overflow-wrap:break-word;
}
a.nastr-stroka:hover, a.nastr-stroka:focus, a.nastr-stroka:focus-visible{
  background-color:#1b212b; outline:none; color:#f3f5f9;
}
a.nastr-stroka:hover, a.nastr-stroka:focus-visible{border-color:#ffd23f}
/* Кольцо выбора: точка внутри загорается у выбранной строки. Так видно,
   что строки — это «или-или», а не переходы на другую страницу. */
.nastr-kolco{display:flex; align-items:center; align-self:flex-start;
  height:1.3em; color:#8b95a5}
.nastr-kolco svg{width:22px; height:22px; display:block}
.nastr-kolco .tochka{opacity:0}
a.nastr-stroka.aktiven .nastr-kolco{color:#ffd23f}
a.nastr-stroka.aktiven .nastr-kolco .tochka{opacity:1}
.nastr-tekst{flex:1 1 auto; min-width:0; font-size:24px; line-height:1.3}
.nastr-schet{flex:0 0 auto; font-size:21px; color:#8b95a5; line-height:1.3}
/* Номер параграфа — своя колонка, как у пунктов плейлиста: «§ 10–11» и
   «§ 9» начинают тему на одном месте. */
.nastr-nomer{flex:0 0 58px; width:58px; font-size:24px; color:#8b95a5;
  line-height:1.3}
/* «Ограничить до» — одно поле и список под ним. Списком все пятьдесят
   параграфов в панели не нужны: ребёнок знает, какой ему нужен, —
   набирает номер или слово, а под полем показываются совпадения.
   Отдельной строки-переключателя и подсказок здесь больше нет: поле
   стоит всегда, а выбранное ограничение видно строкой ниже, с крестиком. */
.nastr-par[hidden]{display:none}
/* Полей слева нет: поле само несёт их в себе (см. .nastr-poisk) — так
   его ширина сходится с шириной строк списка выше. */
.nastr-okno{margin:2px 0 4px; padding:0}
/* Поле и знак снятия ограничения — в одной обёртке: крестик стоит
   в самом поле, у правого его края. */
.nastr-pole{position:relative; display:block}
/* Строка «Выберите параграф» — та же строка списка, что и «Весь курс»
   с учебниками: те же ширина, рост, шрифт и подложка (см.
   a.nastr-stroka выше). Отличается только надписью в поле. */
.nastr-poisk{
  width:100%; box-sizing:border-box; color:#f3f5f9;
  border:3px solid transparent; border-radius:10px;
  background:#232c38;
  /* Рост — как у строки списка: её держит кольцо выбора (1.3em от 30 px
     шрифта панели), плюс поля строки (8+8) и её рамка (3+3). Число то же,
     что у a.nastr-stroka: 61 px. */
  height:calc(1.3 * 30px + 22px);
  /* Слева — столько же, сколько у строки до её текста: поля строки (28),
     кольцо выбора (22) и зазор перед текстом (10). Надпись в поле встаёт
     на одну линию с «Весь курс» и «История России». Справа — место под
     крестик: выбранный номер не заезжает под него. */
  padding:8px 46px 8px 60px;
  font:inherit; font-size:24px; line-height:1.3;
}
/* Выбранный параграф отмечен жёлтой полосой у левого края — как
   выделенная строка списка: полоса и значит «это выбрано». */
.nastr-poisk.vydelen{
  background-image:linear-gradient(#ffd23f, #ffd23f);
  background-repeat:no-repeat;
  background-position:left center;
  background-size:8px 100%;
}
.nastr-poisk:focus{outline:none; border-color:#ffd23f}
.nastr-poisk::placeholder{color:#6f7887}
/* Крестик снятия ограничения — в поле, у правого края. Виден, только
   когда ограничение стоит. */
.nastr-pole .nastr-krestik{
  position:absolute; right:14px; top:50%; transform:translateY(-50%);
  align-self:auto; color:#8b95a5;
}
.nastr-pole .nastr-krestik[hidden]{display:none}
.nastr-pole .nastr-krestik:hover,
.nastr-pole .nastr-krestik:focus{color:#f3f5f9; outline:none}
.nastr-naydennoe{margin-top:6px; max-height:min(34vh, 300px);
  overflow-y:auto; overscroll-behavior:contain;
  scrollbar-width:thin; scrollbar-color:#3a4452 transparent}
.nastr-naydennoe[hidden]{display:none}
.nastr-naydennoe::-webkit-scrollbar{width:8px}
.nastr-naydennoe::-webkit-scrollbar-track{background:transparent}
.nastr-naydennoe::-webkit-scrollbar-thumb{background:#3a4452; border-radius:4px}
/* Флажок настройки: квадрат с галочкой. Пустой — настройка снята,
   с галочкой — включена. Тем же знаком, что и верный ответ в тесте:
   знак один на всё приложение. Квадрат — одного роста с кружочками
   выбора (22 px): своей крупноты у него быть не должно. Стоит он
   по первой строке текста, как и кружочки: настройка длинная, и по
   середине всего текста флажок уезжал бы вниз. */
.nastr-galochka{
  flex:0 0 auto; display:flex; align-items:center; justify-content:center;
  width:22px; height:22px; align-self:flex-start; margin:3px 14px 0 0;
  border:2px solid #3a4452; border-radius:7px; color:transparent;
}
.nastr-galochka svg{width:14px; height:14px; display:block}
.nastr-stroka.aktiven .nastr-galochka{
  border-color:#ffd23f; color:#ffd23f;
}

/* Выбранное ограничение: «§ 12–13» и крестик справа — нажатие снимает
   ограничение. Строка та же, что у прочих настроек: вид один на всей
   панели. */
/* Крестик — знак снятия ограничения: стоит в самом поле поиска
   (см. .nastr-pole выше). Ростом с иконки панели. */
.nastr-krestik{display:flex; color:#8b95a5}
.nastr-krestik svg{width:20px; height:20px; display:block}
.nastr-pusto{
  padding:8px 0 8px 28px; font-size:21px; color:#6f7887; line-height:1.4;
}
/* Сноска об учебниках — здесь, в панели: её читает родитель. Под полем
   это место заняла статистика. */
.nastr-istochnik{
  margin:26px 0 0; padding-left:28px; font-size:19px; color:#6f7887;
  line-height:1.45;
}
/* Флажка «только по выбранному параграфу» больше нет: параграф в
   настройках выбирают один раз — «на каком остановились», — и он
   значит «с начала курса до него». Один и тот же вопрос решался двумя
   строками, и вторая спорила с первой. */

/* ---- Строка списка В ПАНЕЛИ ПЛЕЙЛИСТА — общий вид, своего нет ----
   У панели НЕТ своего оформления строк: пункты — тот же простой текст,
   что в боковом меню и под кадром (правило выше): в покое ни подложки,
   ни полосы, ни жёлтого номера, наведение — серая подложка. Выделяется
   только играющий пункт — как везде (.trek.aktiven).
   Было (до 8 октября): у каждой строки плашка #1b212b и жёлтая полоса
   слева — список выглядел так, будто активны все пункты разом. */

/* ---- кнопки-иконки: эталон — Tilda Icons ---- */
.pravo{margin-left:auto; display:flex; align-items:center; gap:14px}
a.tumbler.ikonka{padding:9px 13px; line-height:0}
a.tumbler.ikonka svg{width:36px; height:36px; display:block}
/* Всплывающие подписи — по эталону верхнего меню calc.html:
   белая карточка, тонкая светло-серая рамка, 12 px скругление,
   10/14 px поля, тёмный текст, мягкая тень, появляется ниже знака
   с небольшим зазором. Браузерный title не используем как оформление:
   подпись берётся из aria-label. */
.tumbler.ikonka, .panel-zakryt, .nastr-knopka,
.pleyer-knopka, .trener-znachok, .trener-strelka,
.pl-strelka, .nastr-krestik, .trener-okno-zakryt,
.trener-oshibki-schet{position:relative}
.tumbler.ikonka::after, .panel-zakryt::after, .nastr-knopka::after,
.pleyer-knopka::after, .trener-znachok::after, .trener-strelka::after,
.pl-strelka::after, .nastr-krestik::after, .trener-okno-zakryt::after,
.trener-oshibki-schet::after{
  content:attr(aria-label); position:absolute; top:calc(100% + 9px);
  right:-8px; padding:10px 14px; border-radius:12px;
  background:#fff; color:#1a1a1a; border:1px solid #e5e7eb;
  font-size:12.5px; font-weight:400; line-height:1.35;
  white-space:nowrap; opacity:0; pointer-events:none;
  transform:translateY(-4px); z-index:1000;
  box-shadow:0 8px 28px rgba(16,24,40,.16);
  transition:opacity .16s, transform .16s;
}
.tumbler.ikonka:hover::after,
.panel-zakryt:hover::after,
.nastr-knopka:hover::after,
.pleyer-knopka:hover::after,
.trener-znachok:hover::after,
.trener-strelka:hover::after,
.pl-strelka:hover::after,
.nastr-krestik:hover::after,
.trener-okno-zakryt:hover::after,
.trener-oshibki-schet:hover::after{
  opacity:1; transform:none;
}
/* У полноэкранного знака подпись не должна возвращать чёрную подложку:
   всплывает только светлая карточка подсказки. */
a#trener-vo-ves-ekran::after{right:0}

/* ---- боковое меню ----
   Выезжает справа и сдвигает страницу, а не накрывает её затемнением:
   ничего не пропадает из виду, плеер и плитки остаются на месте.
   Работает и без javascript: ссылка ведёт на #panel, а :target его
   показывает. С javascript открытием управляет shkPanel, поэтому
   лишних записей в истории браузера не появляется. */
.panel{
  position:fixed; top:0; right:0; bottom:0; z-index:50;
  width:var(--panel-shirina); padding:0; overflow:hidden;
  display:flex; flex-direction:column;
  background:#141a22; border-left:2px solid #2a3340;
  transform:translateX(100%); visibility:hidden;
  transition:transform .32s ease, visibility 0s linear .32s;
}
body.menu-otkryto .panel{transform:none; visibility:visible;
  transition:transform .32s ease, visibility 0s linear 0s}
#panel:target{transform:none; visibility:visible;
  transition:transform .32s ease, visibility 0s linear 0s}
/* Шапка панели — отдельная полоса, а не часть прокрутки: под ней
   лежит своя область со списком, и она прокручивается одна. Название
   класса (или открытого плейлиста) и крестик стоят на месте всегда:
   раньше список уезжал вместе с шапкой, и чтобы закрыть панель,
   приходилось крутить его обратно вверх. */
.panel-verh{
  flex:0 0 auto; display:flex; align-items:center; gap:12px;
  padding:18px 14px 14px; background:#141a22;
  border-bottom:2px solid #2a3340;
}
/* Заголовок панели — «где мы», а не название раздела: тот же шрифт и
   тот же приглушённый цвет, что у строки пути под шапкой («7 класс ›
   История › Видеоуроки»). Раньше он был 28 px, полужирный и белый —
   спорил с содержимым и выглядел кнопкой. Стоит всегда в одну строку
   с крестиком: длинное имя не переносится, а обрезается многоточием. */
.panel-zag{
  flex:1 1 auto; min-width:0;
  font-size:23px; font-weight:400; color:#8d97a8;
  white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
}
/* Область списка: прокручивается только она. Отступ сверху — воздух
   между разделительной линией и первым пунктом: без него верхняя
   плашка липла к линии вплотную. */
.panel-telo{
  flex:1 1 auto; min-height:0;
  overflow-y:auto; overscroll-behavior:contain;
  padding:14px 14px 22px;
}
/* Ручка ширины — у левой кромки панели, поверх страницы. Тянем влево —
   панель шире, вправо — уже. С пульта то же самое стрелками. Видна
   только у открытой панели: иначе перехватывала бы щелчки. */
.panel-tyanulka{
  display:none; position:fixed; top:0; bottom:0; z-index:60;
  right:var(--panel-shirina); width:20px; margin-right:-10px;
  cursor:col-resize; touch-action:none;
}
.panel-tyanulka::before{
  content:''; position:absolute; left:8px; top:50%; width:4px; height:96px;
  margin-top:-48px; border-radius:2px; background:#2a3340;
  transition:background .15s;
}
.panel-tyanulka:hover::before, .panel-tyanulka.tyanem::before{background:#7b8494}
.panel-tyanulka:focus{outline:3px solid #f3f5f9; outline-offset:-3px}
body.menu-otkryto .panel-tyanulka.menyu,
body.pleylist-otkryto .panel-tyanulka.pleylista{display:block}
/* Сколько места у страницы забирает открытая панель: на десктопах и
   горизонтальном планшете — своя ширина справа, с вертикального
   планшета и на телефонах — во весь экран. Собрано в
   Инструменты/разметка.py (menyu_css). */
/* МЕНЮ-ПАНЕЛЬ */
a.panel-zakryt{
  flex:0 0 auto; display:inline-flex; padding:8px; border-radius:10px;
  border:3px solid transparent; color:#f3f5f9;
}
a.panel-zakryt svg{width:32px; height:32px; display:block}
a.panel-zakryt:focus, a.panel-zakryt:hover{border-color:#ffd23f; background:#202836}
/* Пункты меню — тот же стандарт, что и пункты плейлиста: строка это
   простой текст, при наведении серая подложка, а страница, на которой
   мы сейчас, отмечена подложкой и жёлтой чёрточкой слева. Место под
   чёрточку оставлено у всех строк, поэтому отметка ничего не сдвигает. */
a.panel-plitka{
  display:block; position:relative; background:none;
  border:3px solid transparent; border-radius:10px;
  padding:8px 14px 8px 28px; margin-bottom:2px;
  color:#c9d2df; text-decoration:none; font-size:24px;
  overflow-wrap:break-word;
}
a.panel-plitka:focus, a.panel-plitka:hover, a.panel-plitka:focus-visible{
  background-color:#1b212b; outline:none; color:#f3f5f9;
}
/* Жёлтая рамка — только под курсором и на клавиатурном фокусе; при
   обычном фокусе (клик мышью) хватает серой подложки. Рамка одинарная:
   у плашек при наведении их две — жёлтая и мягкое свечение вокруг,
   у строк списка свечения нет. */
a.panel-plitka:hover, a.panel-plitka:focus-visible{border-color:#ffd23f}
a.panel-plitka.tuskly{font-size:22px; color:#98a2b3}
/* Текущая страница: подложка темнее, жёлтая рамка и жёлтый флажок —
   короткая чёрточка у левого края (см. общее правило флажка ниже). */
a.panel-plitka.tekushchiy{
  background-color:#232c38; border-color:#ffd23f; color:#f3f5f9;
}
/* Активная вкладка плейлиста под видеокадром — как активный пункт
   списка плейлиста, а не как выбранная страница: никакой рамки в покое,
   только общая подложка и цветная полоса слева. */
a.pl-plitka.tekushchiy{border-color:transparent}
a.pl-plitka.tekushchiy:hover, a.pl-plitka.tekushchiy:focus-visible{
  border-color:#ffd23f;
}

/* ---- название класса в шапке меню ----
   Просто текст: списка классов здесь больше нет. Класс выбирают
   плитками на его странице, а раскрывающийся список в меню повторял
   эти же плитки — и звал не туда. Вид у строки прежний: приглушённое
   название в шапке панели, слева от крестика. */
.klass-imya{
  flex:1 1 auto; min-width:0; padding:6px 0 6px 28px; color:#8d97a8;
  font-size:23px; hyphens:manual; overflow-wrap:break-word;
}
/* Стрелка у раскрывающихся строк учебника (см. .kniga-stroka): тот же
   шеврон, что был у списка классов. */
.strela{flex:0 0 auto; display:flex; color:inherit; transition:transform .15s}
.strela svg{width:24px; height:24px; display:block}
details.kniga-stroka[open] .strela{transform:rotate(180deg)}


/* ---- баннер лекций: полоса во всю ширину страницы предмета ----
   Один автор, один курс, две подборки. Стоит выше всех плиток и
   отделён от них воздухом больше, чем плитки друг от друга (24 px):
   баннер — не ещё одна плитка, а вход в лекции. Ничего своего в нём
   нет: тот же фон, что у плиток, то же скругление, тот же жёлтый. */
.banner{
  margin:30px 0 0; padding:26px 30px 28px;
  border:2px solid #2a3340; border-radius:26px;
  background:linear-gradient(120deg,#232c39 0%,#171d26 62%);
}
.banner-nazv{
  display:block; font-size:36px; font-weight:600; color:#f3f5f9;
  line-height:1.15;
}
.banner-podpis{display:block; margin-top:8px; font-size:24px; color:#8b95a5}
.banner-knopki{
  display:flex; align-items:center; gap:12px; flex-wrap:wrap;
  margin-top:22px;
}
a.banner-knopka, a.banner-igrat{
  display:inline-block; text-decoration:none; font-size:24px;
  white-space:nowrap; padding:10px 22px; border-radius:999px;
  border:2px solid #2a3340; background:#1b222c; color:#c9d2df;
}
a.banner-knopka.aktiven{
  background:#ffd23f; border-color:#ffd23f; color:#171d26; font-weight:600;
}
a.banner-knopka:focus, a.banner-knopka:hover,
a.banner-igrat:focus, a.banner-igrat:hover{
  outline:none; border-color:#ffd23f; color:#f3f5f9;
}
a.banner-knopka.aktiven:focus, a.banner-knopka.aktiven:hover{color:#171d26}
a.banner-igrat{margin-left:auto; color:#ffd23f; border-color:#ffd23f}
/* Кадр живёт здесь. Пока лекцию не выбрали, места он не занимает:
   страница ничего не тянет из сети и не показывает чёрный экран. */
.banner-mesto:not(:empty){margin-top:22px}
.banner-mesto iframe{
  display:block; width:100%; aspect-ratio:16 / 9; border:0; background:#000;
  border-radius:16px;
}
.banner-spiski{margin-top:22px}
.banner-nabor{
  /* minmax(0, 1fr), а не 1fr: у колонки с длинной строкой своя
     наименьшая ширина, и «1fr» её не отменяет — на узком экране
     сетка вылезала за кадр. */
  display:grid; grid-template-columns:repeat(2, minmax(0, 1fr));
  gap:2px 34px; margin:0; padding:0; list-style:none;
}
.banner-nabor[hidden]{display:none}
a.banner-trek{
  display:flex; align-items:baseline; gap:16px; padding:11px 4px;
  text-decoration:none; color:#c9d2df; font-size:25px; line-height:1.2;
}
a.banner-trek .bt-vremya{
  /* Время не переносится: «1 ч 21 мин» должно стоять в одну строку,
     иначе пункт скачет по высоте и колонки разъезжаются. */
  flex:0 0 auto; min-width:136px; color:#8b95a5; font-size:21px;
  white-space:nowrap;
}
a.banner-trek .bt-tema{flex:1 1 auto; min-width:0; hyphens:manual; overflow-wrap:break-word}
a.banner-trek:focus, a.banner-trek:hover{outline:none; color:#f3f5f9}
a.banner-trek.aktiven{color:#f3f5f9}
/* Активная лекция отличается только цветом строки — как и в списках
   под кадром. Жёлтое время было единственной подсветкой в баннере и
   спорило с их стандартом, поэтому его убрали. */

/* Узкий экран: подборки встают в один столбик — как и плашки, которые
   с горизонтального планшета идут по одной в ряд. Иначе строки лекций
   не влезают и тянут страницу вбок. Считается по рабочей ширине: с
   открытым меню она сужается, и подборки перестраиваются. */
@container stranica (max-width:959px){
  .banner{padding:20px 22px 22px; border-radius:20px}
  .banner-nazv{font-size:30px}
  .banner-podpis{font-size:21px}
  .banner-nabor{grid-template-columns:minmax(0, 1fr)}
  a.banner-trek{font-size:22px; gap:12px}
  a.banner-trek .bt-vremya{min-width:0; font-size:19px}
  /* Кнопка подборки уступает кадру так же, как кнопки в строках:
     длинное название переносится, а не вылезает за край. */
  a.banner-knopka, a.banner-igrat{font-size:21px;
                                  white-space:normal; max-width:100%}
  .banner-knopki{min-width:0}
}
/* Плитки под баннером: воздух больше, чем между самими плитками. */
.setka.posle-bannera{margin-top:64px}

/* ---- знак «Лекции»: баннер, который ведёт на страницу ----
   Стоит там же, где стоял играющий баннер (выше плиток, во всю ширину
   страницы), и одет как плитка: жёлтая полоса по левой кромке, то же
   скругление, та же подсветка при наведении. Отличие одно: это дверь,
   а не сцена — внутри нет ни кадра, ни списка лекций, а вся плашка
   целиком ссылка на страницу лекций. Мишень во весь баннер — не для
   красоты: на телевизоре в неё легко попасть пультом, а две ссылки
   рядом заставляют целиться. */
/* Знак — та же плашка, только во всю ширину и выше на 30 %. Текст стоит
   там же, где у плашек: внизу слева, с теми же полями и тем же шрифтом
   (классы .nazv и .poyas — общие с плашкой). Раньше текст стоял по
   центру полосы и был другого размера, поэтому знак читался как другая
   деталь, а не как плашка раздела. */
a.banner-znak{
  --fon-kart:linear-gradient(120deg,#232c39 0%,#171d26 62%);
  display:flex; flex-direction:column; justify-content:flex-end;
  align-items:stretch;
  margin:30px 0 0;
  border:4px solid transparent; border-radius:var(--radius);
  text-decoration:none; color:#f3f5f9;
  /* Второй слой — кадр или фон: у знака с рисунком в --sloi лежит
     картинка поверх градиента (см. правило плашек выше). Высоту знаку
     задают ступени раскладки: он выше плашки своей полосы на 30 %
     (Инструменты/разметка.py, ZNAK_DOLYA). */
  background-image:linear-gradient(#ffd23f, #ffd23f),
                   var(--sloi, var(--fon-kart));
  background-repeat:no-repeat, no-repeat;
  background-position:left center, left center;
  background-size:var(--polosa) 100%, 100% 100%;
  background-origin:border-box, border-box;
  background-clip:border-box, border-box;
}
/* Текст знака — те же классы, что и у плашки (.nazv, .poyas), поэтому
   и правила у них общие: шрифт названия, цвет и отступ подписи. Размеры
   задают ступени раскладки (Инструменты/разметка.py) — как у плашки. */
a.banner-znak .nazv{
  display:block; font-weight:600; line-height:1.1;
  hyphens:manual; overflow-wrap:break-word; min-width:0; max-width:100%;
}
a.banner-znak .poyas{
  display:block; margin-top:8px; color:#98a2b3; line-height:1.3;
  hyphens:manual; overflow-wrap:break-word; min-width:0; max-width:100%;
}

a.banner-znak:focus, a.banner-znak:hover, a.banner-znak:active{
  outline:none; border-color:#ffd23f;
  --fon-kart:linear-gradient(120deg,#2c3745 0%,#252d38 100%);
  box-shadow:0 0 0 6px rgba(255,210,63,.28);
}



/* ---- раздел, который ещё наполнен не весь ----
   Плашка стоит с первого дня, страница у неё тоже, а материалов пока
   нет. Пустой белый лист читался бы как поломка, поэтому на странице
   карточка: что за раздел и что здесь будет. */
.zagotovka{
  margin-top:26px; padding:32px 36px;
  border:2px solid #2a3340; border-radius:22px;
  background:linear-gradient(165deg,#1f2733 0%,#171d26 100%);
}
.zagotovka .zg-nazv{
  display:block; font-size:30px; font-weight:600; color:#ffd23f;
}
.zagotovka .zg-tekst{
  display:block; margin-top:12px; max-width:880px;
  font-size:22px; color:#98a2b3; line-height:1.35;
  hyphens:manual; overflow-wrap:break-word;
}
@container stranica (max-width:959px){
  .zagotovka{padding:24px 22px}
  .zagotovka .zg-nazv{font-size:26px}
  .zagotovka .zg-tekst{font-size:20px}
}

/* ---- кто учится и зачем ----
   Маленькая строка под путём, выше учебника: имя и цель с главного
   экрана. Она не заголовок страницы — тот большой, — а напоминание:
   видно на каждой странице, в том числе когда смотришь видео. Ничего
   не выдумываем: имя и цель человек написал сам, пусто — строки нет. */
.imya-stroka{
  margin:2px 0 0; padding:0 4px;
  font-size:24px; color:#8b95a5;
  hyphens:manual; overflow-wrap:break-word;
}
.imya-stroka b{font-weight:600; color:#c9d2df}

h1{font-size:50px; margin:0 0 8px; letter-spacing:-.01em;
   hyphens:manual; overflow-wrap:break-word}
.pod{color:#98a2b3; font-size:26px; margin:0 0 10px}
.podskazka{
  background:#16202b; border-left:8px solid #ffd23f; color:#dbe3ee;
  font-size:25px; padding:16px 24px; border-radius:0 14px 14px 0; margin:14px 0 30px;
}
h2{
  font-size:31px; color:#ffd23f; margin:40px 0 16px; padding-bottom:10px;
  border-bottom:2px solid #2a3340;
}
h3{
  font-size:27px; color:#dbe3ee; margin:30px 0 12px;
}

/* ---- плитки: горизонтальные, как на телевизоре ----
   Сколько плашек в ряд и какого они размера — записано в одном месте:
   Инструменты/разметка.py; оттуда этот блок собирается при сборке
   (см. ниже, `setka_css`). Модели экрана — в РАЗМЕТКА.md. */
a.plitka{
  /* --fon-kart — нижний слой фона; подсветка меняет только его, поэтому
     обложка учебника и жёлтая полоса остаются на месте. */
  --fon-kart:linear-gradient(165deg,#1f2733 0%,#171d26 100%);
  position:relative; aspect-ratio:16 / 9; min-height:150px;
  border:4px solid transparent; border-radius:var(--radius);
  padding:24px 26px 24px calc(var(--polosa) + 28px);
  text-decoration:none; color:#f3f5f9;
  display:flex; flex-direction:column; justify-content:flex-end;
  /* Жёлтая полоса — часть фона, а не рамка и не отдельный слой.
     Фон обрезается скруглением самого блока, поэтому полоса идёт
     до конца дуги угла. Рамка только с одной стороны на скруглении
     обрывается, слой-псевдоэлемент — срезается по своей дуге. */
  background-image:
    linear-gradient(#ffd23f, #ffd23f),
    var(--sloi, var(--fon-kart));
  background-repeat:no-repeat, no-repeat;
  background-position:left center, left center;
  background-size:var(--polosa) 100%, 100% 100%;
  /* origin:border-box — полоса начинается от самой кромки плитки, а не
     из-под рамки, и в обычном виде, и в подсветке выглядит одинаково:
     скругление срезает её ровно по дуге угла. */
  background-origin:border-box, border-box;
  background-clip:border-box, border-box;
}
/* aspect-ratio понимают все современные браузеры; для остальных
   остаётся min-height, плитка будет просто чуть ниже. */
@supports (aspect-ratio: 16 / 9){ a.plitka{min-height:0} }
a.plitka:focus, a.plitka:hover, a.plitka:active{
  outline:none; border-color:#ffd23f;
  --fon-kart:linear-gradient(165deg,#2c3745 0%,#252d38 100%);
  box-shadow:0 0 0 6px rgba(255,210,63,.28);
}
/* Перенос: сначала по словам, перенос по слогам — крайний случай.
   Автоматический hyphens:auto режет слово по слогам, даже когда оно
   целиком влезло бы на следующей строке («кино и документалистика»),
   поэтому он отключён: мягкие дефисы расставляет myagkie() при сборке,
   и браузер пользуется ими только если слово не влезло целиком.
   Переменные --polosa задаёт .setka. */
a.plitka .nazv, a.plitka .poyas, a.plitka .skolko,
a.plitka .zamena{
  hyphens:manual; -webkit-hyphens:manual;
  overflow-wrap:break-word; word-break:normal;
  min-width:0; max-width:100%;
}
a.plitka .nazv{font-size:36px; font-weight:600; line-height:1.1}
a.plitka .poyas{font-size:20px; color:#98a2b3; margin-top:8px; line-height:1.3}
a.plitka .skolko{font-size:20px; color:#ffd23f; margin-top:8px}
a.plitka .zamena{font-size:19px; color:#8b95a5; margin-top:8px; line-height:1.25}

/* Цифра в названии класса — главная: набрана крупнее слова, само слово
   идёт с заглавной буквы. Размер один на всех плашках, поэтому «5 Класс»
   и «География» читаются одинаково. */
a.plitka .nazv .chislo{font-size:1.3em; line-height:.9; margin-right:.2em}

/* ---- плашка класса ----
   Класс узнают по цифре, слово «Класс» и так понятно. Поэтому цифра
   большая и жёлтая — во всю высоту плашки, — а слово стоит рядом
   приглушённой подписью по общей строке. */
a.plitka.klass{justify-content:center}
a.plitka.klass .nazv{display:flex; align-items:baseline; gap:.13em}
/* Зазор до слова считается от контура цифры, а не от знакоместа.
   Знакоместо у всех цифр одинаковое, а контур — нет: у «7» справа
   пусто 0,113 знакоместа (диагональ не доходит до края), у «8» — 0,087,
   поэтому «8 класс» выглядел приклеенным, а «7 класс» — нормально.
   Цифра ставится в жёсткую рамку .72em и центрируется в ней: пустота
   слева и справа от контура становится одинаковой, и зазор до слова
   перестаёт зависеть от того, какая это цифра. Отрицательный
   letter-spacing убран — он тоже отнимал воздух. */
a.plitka.klass .nazv .chislo{
  display:inline-block; width:.72em; text-align:center;
  font-size:clamp(110px, 12vw, 186px); font-weight:800; color:#ffd23f;
  line-height:.78; letter-spacing:0; margin:0;
}
a.plitka.klass .nazv .slovo{
  font-size:34px; font-weight:600; color:#98a2b3; letter-spacing:.02em;
}
/* Классные плашки — та же общая сетка: у плашек одного размера нет
   причин задавать свой шаг. */

/* СЕТКА-ПЛАШЕК */
/* Собранный CSS стоит последним в разделе плашек: базовые правила
   (a.plitka .nazv и прочие) идут выше, поэтому ступени размеров их
   перебивают — иначе размер оставался бы десктопным на телефоне. */

/* ЗАПАСНОЙ-ПУТЬ-РАСКЛАДКИ */

/* ---- строки со ссылками на самих страницах материалов ---- */
.stroka{
  display:flex; align-items:center; gap:22px;
  background:#1b212b; border:4px solid transparent; border-radius:18px;
  padding:20px 26px; margin-bottom:14px;
}
.nomer{flex:0 0 auto; min-width:110px; text-align:center; font-size:32px; font-weight:700; color:#ffd23f; line-height:1.1}
.tema{flex:1 1 auto; min-width:0}
.tema .chto{display:block; font-size:29px}
.tema .primech{display:block; font-size:22px; color:#98a2b3; font-style:italic; margin-top:4px}
.knopki{flex:0 0 auto; display:flex; gap:12px; flex-wrap:wrap; justify-content:flex-end}
/* Кнопка не бывает шире своего места. Надпись у неё может быть длинной
   («Образец проверочной работы для школ с углублённым изучением
   математики…»): с запретом переноса такая кнопка растягивала страницу
   вбок. Поэтому длинная надпись переносится по словам (короткая от этого
   не меняется — ей переносить нечего), а слово без пробелов (адрес сайта)
   ломается по буквам. */
a.knopka{
  display:inline-block; background:#2b3543; color:#f3f5f9; text-decoration:none;
  border:4px solid transparent; border-radius:16px; padding:16px 22px;
  font-size:27px; white-space:normal;
  flex:0 1 auto; max-width:100%; min-width:0; overflow-wrap:break-word;
}
a.knopka .vremya{color:#ffd23f; font-weight:600}
a.knopka:focus, a.knopka:hover, a.knopka:active{
  outline:none; border-color:#ffd23f; background:#3d4c5f;
}
.stroka.net .tema .chto{color:#7d8695}
/* Строка кнопок умеет ужиматься: без этого длинная кнопка не отдаёт
   место и ряд уезжает вбок (считается по рабочей ширине, как и всё
   остальное на странице). */
.knopki{min-width:0; max-width:100%}

.niz{margin-top:44px; color:#6f7887; font-size:22px; line-height:1.5}
/* Планшет вертикальный и уже: та же контрольная точка 960, что
   у Тильды, — новых порогов не заводим (РАЗМЕТКА.md). Размер текста
   и строки считаются по рабочей ширине: с открытым меню она сужается,
   и страница перестраивается, как если бы окно было такой ширины. */
@container stranica (max-width:959px){
  .wrap{font-size:26px}
  h1{font-size:40px}
  a.tumbler.ikonka svg{width:28px; height:28px}
  .stroka{flex-wrap:wrap; gap:14px}
  .nomer{flex:0 0 auto; min-width:88px; font-size:28px}
  .tema{flex:1 1 100%}
  .knopki{flex:1 1 100%; justify-content:flex-start}
}
"""

# Раскладка плашек — из общей таблицы моделей экрана
# (Инструменты/разметка.py): собирается один раз при импорте.
import разметка as _razmetka
CSS = CSS.replace('/* СЕТКА-ПЛАШЕК */', _razmetka.setka_css())
CSS = CSS.replace('/* ПОЛЯ-СТРАНИЦЫ */', _razmetka.polya_css())
CSS = CSS.replace('/* ЗАПАСНОЙ-ПУТЬ-РАСКЛАДКИ */', _razmetka.zona_css())
CSS = CSS.replace('/* МЕНЮ-ПАНЕЛЬ */', _razmetka.menyu_css())
# Имя контейнера рабочей ширины: одно на CSS и на разметку страницы.
CSS = CSS.replace('SHIRINA-STRANICY', str(_razmetka.SHIRINA_STRANICY))
CSS = CSS.replace('KONTEYNER-IMYA', _razmetka.KONTEYNER)
CSS = CSS.replace('ZONA-KLASS', _razmetka.ZONA_KLASS)
assert 'KONTEYNER-IMYA' not in CSS and 'ZONA-KLASS' not in CSS, \
    'в CSS осталось неподставленное имя контейнера рабочей ширины'
for _marker in ('СЕТКА-ПЛАШЕК', 'ПОЛЯ-СТРАНИЦЫ', 'МЕНЮ-ПАНЕЛЬ',
                'ЗАПАСНОЙ-ПУТЬ-РАСКЛАДКИ'):
    assert _marker not in CSS, \
        f'в CSS остался неподставленный блок разметки: {_marker}'
# Иконки шапки. Эталон — Tilda Icons и The Noun Project (в Тильде
# как раз эти две библиотеки встроены): штриховые, геометричные,
# толщина линии 2, круглые окончания, без заливки.
SVG = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
       'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
       'aria-hidden="true">{}</svg>')

IKONY = {
    'назад': '<path d="M14.5 5 8 12l6.5 7"/>',
    'вперёд': '<path d="M9.5 5 16 12l-6.5 7"/>',
    'домой': ('<path d="M3.5 10.6 12 3.8l8.5 6.8"/>'
              '<path d="M5.8 9.4V20h12.4V9.4"/>'
              '<path d="M10 20v-5.2h4V20"/>'),
    # «Закрепить» — канцелярская кнопка, как знак закреплённого
    # в соцсетях: скрепка обозначает вложение, а не закрепление.
    'скрепка': ('<path d="M12 17v5"/>'
                '<path d="M9 10.76a2 2 0 0 1-1.11 1.79l-1.78.9A2 2 0 0 0 5 15.24'
                'V16a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-.76a2 2 0 0 0-1.11-1.79'
                'l-1.78-.9A2 2 0 0 1 15 10.76V7a1 1 0 0 1 1-1 2 2 0 0 0 0-4H8'
                'a2 2 0 0 0 0 4 1 1 0 0 1 1 1z"/>'),
    'меню': '<path d="M4 7h16"/><path d="M4 12h16"/><path d="M4 17h16"/>',
    # Плейлист: значок воспроизведения и список — рядом с ним.
    'плейлист': ('<path d="M4 7.6v8.8l7.4-4.4z"/>'
                 '<path d="M14.6 8.4h5.4"/><path d="M14.6 12h5.4"/>'
                 '<path d="M14.6 15.6h5.4"/>'),
    'закрыть': '<path d="M6.5 6.5l11 11"/><path d="M17.5 6.5l-11 11"/>',
    'шеврон': '<path d="M5 9l7 7 7-7"/>',
    'экран': ('<path d="M4 9V4.5h5"/><path d="M20 9V4.5h-5"/>'
              '<path d="M4 15v4.5h5"/><path d="M20 15v4.5h-5"/>'),
    # «Во весь экран» — те же уголки шире: стрелки наружу. Значок стоит
    # в строке управления тренажёра, где рядом «настройки» с ползунками,
    # и уголки читаются как «развернуть», а не как «рамка».
    'во весь экран': ('<path d="M4 9.5V4h5.5"/><path d="M14.5 4H20v5.5"/>'
                      '<path d="M20 14.5V20h-5.5"/>'
                      '<path d="M9.5 20H4v-5.5"/>'),
    # Настройки: ползунки. Шестерёнка читалась бы как «механика», а
    # ползунки — это ровно то, что делают в панели: двигают значения.
    # Рука, которой листают подборку на телефоне: ею подсказываем,
    # что полосу плашек можно сдвинуть вбок.
    'листать': ('<path d="M18 11V6a2 2 0 0 0-2-2a2 2 0 0 0-2 2"/>'
                '<path d="M14 10V4a2 2 0 0 0-2-2a2 2 0 0 0-2 2v2"/>'
                '<path d="M10 10.5V6a2 2 0 0 0-2-2a2 2 0 0 0-2 2v8"/>'
                '<path d="M18 8a2 2 0 1 1 4 0v6a8 8 0 0 1-8 8h-2c-2.8 0'
                '-4.5-.86-5.99-2.34l-3.6-3.6a2 2 0 0 1 2.83-2.82L7 15"/>'),
    # Знак вопроса: им вызывается подсказка по нынешнему вопросу.
    'вопрос': ('<circle cx="12" cy="12" r="9.2"/>'
               '<path d="M9.4 9.2a2.7 2.7 0 0 1 5.3.7c0 1.8-2.7 2.2-2.7 3.9"/>'
               '<path d="M12 17.2h.01"/>'),
    'настройки': ('<path d="M4 7.5h6"/><path d="M14 7.5h6"/>'
                  '<circle cx="12" cy="7.5" r="2.4"/>'
                  '<path d="M4 16.5h6"/><path d="M14 16.5h6"/>'
                  '<circle cx="12" cy="16.5" r="2.4"/>'),
    'галочка': '<path d="M5.5 12.5l4.6 4.6L18.8 7.4"/>',
    # Кристалл — награда за верный ответ: огранённый камень. Стоит в
    # верхней строке поля тренажёра, левее «на весь экран»: собранные
    # кристаллы. Ромб сам по себе читался бы как «плейлист»; грани
    # показывают, что это камень.
    'кристалл': ('<path d="M12 2.6 20.4 9 12 21.4 3.6 9z"/>'
                 '<path d="M3.6 9h16.8"/>'
                 '<path d="M12 2.6 8.7 9l3.3 12.4L15.3 9z"/>'),
    # Крестик-ошибка — того же роста и с тем же штрихом, что кристалл:
    # знаки стоят рядом в одной строке и читаются парой. Красным его
    # делает оформление (см. .trener-oshibki-schet).
    'ошибка': ('<circle cx="12" cy="12" r="8.7"/>'
               '<path d="M12 7.5v5.8"/>'
               '<circle cx="12" cy="16.8" r=".9" fill="currentColor" stroke="none"/>'),
}


def ikona(imya):
    """Готовая svg-иконка для шапки."""
    return SVG.format(IKONY[imya])


VERH = """<nav class="verh">
<a class="tumbler ikonka" id="dom" href="{vhod}" aria-label="Домой"
   >{domoy}</a>
<a class="tumbler ikonka" href="#" aria-label="Назад"
   onclick="history.back();return false">{nazad}</a>
<a class="tumbler ikonka" href="#" aria-label="Вперёд"
   onclick="history.forward();return false">{vpered}</a>
<span class="verh-imya" id="verh-imya" hidden></span>
<span class="pravo">{pin}{menyu}</span>
</nav>
{put}
{imya}
{kniga}
{panel}"""

# javascript шапки. YA_VHOD — признак страницы входа: именно с неё
# браузер сам переходит на закреплённую страницу при открытии.
JS = """<script>
(function(){
  var K='shkola.home';
  var HOME="%(home)s";
  /* Плеер запоминает, на каком уроке остановились, по этому же имени:
     оно не зависит от буквы диска, с которого открыта флешка. */
  window.SHK_HOME=HOME;
  var ROOT="%(root)s";
  var VHOD="%(vhod)s";
  var YA_VHOD=%(ya_vhod)s;
  function dostupno(){
    try{ localStorage.setItem('__t','1'); localStorage.removeItem('__t'); return true; }
    catch(e){ return false; }
  }
  function rd(){ try{ return localStorage.getItem(K); }catch(e){ return null; } }
  function wr(v){
    try{ if(v===null){ localStorage.removeItem(K); } else { localStorage.setItem(K,v); }
         return true; }
    catch(e){ return false; }
  }
  var dom=document.getElementById('dom'), pin=document.getElementById('pin');

  /* ---- две выезжающие панели: меню и плейлист ----
     Границы у них одни и те же, и вдвоём они не открываются: открыли
     меню — плейлист закрылся, открыли плейлист — закрылось меню.
     Плейлист есть только на страницах видеоуроков.

     Панель НЕ закрывается сама: что открыто, то и запоминается в
     браузере (ключ KP), и на следующей странице панель стоит открытой
     ровно так же. Закрыть её может только человек — крестиком или
     клавишей Escape. Раньше переход по пунктам меню закрывал панель,
     и её приходилось открывать заново на каждой странице. */
  var KP='shkola.panel-otkryt';
  function panel_pomnit(chto){
    try{ localStorage.setItem(KP, chto); }catch(e){}
  }
  window.shkPanel=function(otkryt){
    var b=document.body;
    if(otkryt){
      b.classList.add('menu-otkryto');
      b.classList.remove('pleylist-otkryto');
      panel_pomnit('menu');
      /* Фокус встаёт на первую строку списка — и в меню, и в плейлисте
         одинаково. Крестик закрытия при открытии не подсвечивается
         нигде: раньше в меню фокус шёл на название класса, а в панели
         плейлиста на первый пункт, и крестики выглядели по-разному. */
      var p=document.getElementById('panel');
      var perv=p && p.querySelector('.panel-telo a');
      if(perv) perv.focus();
    } else {
      b.classList.remove('menu-otkryto');
      panel_pomnit('');
    }
    return false;
  };
  window.shkPleylist=function(otkryt){
    var b=document.body;
    if(otkryt){
      b.classList.add('pleylist-otkryto');
      b.classList.remove('menu-otkryto');
      panel_pomnit('pleylist');
      var p=document.getElementById('pleylist-panel');
      var perv=p && p.querySelector('.panel-telo a');
      if(perv) perv.focus();
    } else {
      b.classList.remove('pleylist-otkryto');
      panel_pomnit('');
    }
    return false;
  };
  /* Возврат панели на новой странице. Ключа в памяти ещё нет — панель
     ничего не помнит: остаётся как собрана страница (на видеоуроках
     плейлист открыт сразу). Запомнено «menu» — открываем меню,
     «pleylist» — плейлист (на страницах, где он есть), пусто — панель
     закрыта. Фокус здесь никуда не ставим: страница только открылась,
     и рамка на первой строке была бы неожиданной. */
  (function(){
    var chto=null;
    try{ chto=localStorage.getItem(KP); }catch(e){ return; }
    if(chto===null){ return; }
    var b=document.body;
    /* Плейлист во всю ширину экрана сам не открываем: на телефонах и
       вертикальном планшете он занял бы весь экран вместо кадра. */
    if(window.innerWidth < MENYU-VO-VSYU && chto==='pleylist'){ chto=''; }
    if(chto==='menu'){
      b.classList.add('menu-otkryto'); b.classList.remove('pleylist-otkryto');
    } else if(chto==='pleylist' && document.getElementById('pleylist-panel')){
      b.classList.add('pleylist-otkryto'); b.classList.remove('menu-otkryto');
    } else {
      b.classList.remove('menu-otkryto'); b.classList.remove('pleylist-otkryto');
    }
  })();
  /* Значок меню открывает и закрывает меню. Плейлист вызывается своей
     кнопкой на кадре: так панель возвращается всегда, чем бы её ни
     закрыли. */
  window.shkMenu=function(){
    if(document.body.classList.contains('menu-otkryto')){
      return window.shkPanel(false);
    }
    return window.shkPanel(true);
  };
  /* Кнопка плейлиста на кадре: открыта панель — закрыть, закрыта —
     открыть. */
  window.shkPleylistTog=function(){
    return window.shkPleylist(
      !document.body.classList.contains('pleylist-otkryto'));
  };
  document.addEventListener('keydown', function(e){
    if(e.key==='Escape'){
      window.shkPanel(false); window.shkPleylist(false);
      window.shkOblozhkaZakryt();
    }
  });

  /* ---- обложка учебника во весь экран ----
     Маленькая обложка в карточке учебника нажимается — открывается
     крупно, чтобы рассмотреть подробности. Окно собирается здесь, при
     первом нажатии: страницам без учебника оно ни к чему. Закрывается
     нажатием в любое место или клавишей Esc. */
  window.shkOblozhkaZakryt=function(){
    var okno=document.getElementById('shk-oblozhka');
    if(okno){ okno.hidden=true; }
    return false;
  };
  window.shkOblozhka=function(a){
    var im=a.querySelector('img');
    if(!im){ return false; }
    var okno=document.getElementById('shk-oblozhka');
    if(!okno){
      okno=document.createElement('div');
      okno.id='shk-oblozhka';
      okno.setAttribute('role','dialog');
      okno.setAttribute('aria-label','Обложка учебника');
      okno.innerHTML='<img alt="">';
      okno.onclick=function(){ okno.hidden=true; };
      document.body.appendChild(okno);
    }
    okno.querySelector('img').src=im.getAttribute('src');
    okno.hidden=false;
    return false;
  };

  /* Домашняя страница ровно одна: в браузере лежит одна запись, поэтому
     закрепили новую — прежняя открепилась сама. Никаких надписей об этом
     нет: скрепка просто горит на той странице, которая закреплена. */
  function obnovit(){
    var h=rd();
    if(pin){ pin.className = (h===HOME) ? 'tumbler ikonka zakrep'
                                        : 'tumbler ikonka'; }
  }
  if(pin){
    pin.onclick=function(){ wr(rd()===HOME?null:HOME); obnovit(); return false; };
  }
  if(dom){
    dom.onclick=function(){
      var z=rd();
      if(z){ location.href=ROOT+encodeURI(z); return false; }
      return true;
    };
  }

  /* ---- запасной путь раскладки ----
     Модель экрана считается по ширине РАБОЧЕЙ области, а не окна:
     открытое меню забирает у страницы своё место, и плашки обязаны
     перестроиться по остатку (РАЗМЕТКА.md). Ведёт это CSS —
     контейнерными запросами к блоку .rabochaya. Телевизор или старый
     браузер таких запросов не знает: там полосу называет этот скрипт,
     кладя на блок рабочей ширины data-polosa, а правила те же самые —
     собранные из той же таблицы (Инструменты/разметка.py).
     Где контейнерные запросы есть, скрипт ничего не делает: раскладку
     ведёт CSS. */
  var est_konteynery = false;
  try{
    est_konteynery = !!(window.CSS && CSS.supports &&
                        CSS.supports('container-type', 'inline-size'));
  }catch(e){}
  if(!est_konteynery){
    var zona = document.querySelector('.rabochaya');
    if(zona){
      var POLOSY = [[1199, 'планшет горизонтальный'],
                    [959, 'планшет вертикальный'],
                    [639, 'телефоны горизонтальные'],
                    [479, 'телефоны вертикальные']];
      var zonaTaymer = null;
      window.shkZona = function(){
        var x = zona.getBoundingClientRect().width;
        var imya = 'десктопы', i;
        for(i = 0; i < POLOSY.length; i++){
          if(x <= POLOSY[i][0]){ imya = POLOSY[i][1]; break; }
        }
        zona.setAttribute('data-polosa', imya);
      };
      window.shkZona();
      window.addEventListener('resize', function(){
        window.shkZona();
        clearTimeout(zonaTaymer);
        zonaTaymer = setTimeout(window.shkZona, 400);
      });
      /* Панель выезжает плавно: ширина страницы меняется не сразу,
         поэтому пересчитываем, когда выезд закончился. */
      document.body.addEventListener('transitionend', function(e){
        if(e.propertyName === 'padding-right'){ window.shkZona(); }
      });
    }
  }

  /* ---- ширина правой панели ----
     Одна и та же у меню и у плейлиста: потянули за кромку — панель
     шире или уже, с пульта то же самое стрелками. Ширина запоминается
     в браузере, как и урок.

     Задавать ширину вручную можно только там, где панель занимает
     ЧАСТЬ экрана — на десктопах и горизонтальном планшете. С
     вертикального планшета и на телефонах (граница — в
     Инструменты/разметка.py) панель разворачивается на всю ширину
     экрана, и тянуть её не за что: ручки ширины там нет, а своя
     ширина, запомненная на широком окне, не подставляется. */
  function panel_na_vsyu(){ return window.innerWidth < MENYU-VO-VSYU; }
  function panel_min(){ return (window.innerWidth < 640) ? 240 : 300; }
  function panel_max(){
    return Math.max(panel_min() + 40,
                    Math.min(900, window.innerWidth - 320));
  }
  var panel_ruchnaya = 0;   /* ширина, выставленная ручкой; 0 — по умолчанию */
  function panel_postavit(w){
    if(panel_na_vsyu()){
      /* Во всю ширину: своя ширина тут только мешала бы. */
      document.body.style.removeProperty('--panel-shirina');
      return;
    }
    w = Math.max(panel_min(), Math.min(w, panel_max()));
    panel_ruchnaya = Math.round(w);
    document.body.style.setProperty('--panel-shirina', panel_ruchnaya + 'px');
    try{ localStorage.setItem('shkola.panel', String(panel_ruchnaya)); }
    catch(e){}
  }
  function panel_tekushchaya(){
    var w = parseFloat(getComputedStyle(document.body)
                       .getPropertyValue('--panel-shirina'));
    return (w > 0) ? w : 420;
  }
  try{
    var sh = parseFloat(localStorage.getItem('shkola.panel'));
    if(sh > 0){ panel_postavit(sh); }
  }catch(e){}
  /* Окно перетащили через границу «панель во всю ширину»: на узком
     окне снимаем свою ширину, на широком возвращаем ту, что ставили
     ручкой. Иначе панель осталась бы узкой посреди телефона. */
  window.addEventListener('resize', function(){
    if(panel_na_vsyu()){
      document.body.style.removeProperty('--panel-shirina');
    } else if(panel_ruchnaya){
      document.body.style.setProperty('--panel-shirina',
                                      panel_ruchnaya + 'px');
    }
  });

  window.shkTyan=function(e){
    var shag = e.shiftKey ? 80 : 30;
    var tek = panel_tekushchaya();
    if(e.key==='ArrowLeft'){ panel_postavit(tek + shag); return false; }
    if(e.key==='ArrowRight'){ panel_postavit(tek - shag); return false; }
    return true;
  };
  (function(){
    var ruki = document.querySelectorAll('.panel-tyanulka');
    for(var i=0;i<ruki.length;i++){
      (function(ruka){
        ruka.addEventListener('pointerdown', function(e){
          e.preventDefault();
          ruka.className = ruka.className + ' tyanem';
          if(ruka.setPointerCapture){ ruka.setPointerCapture(e.pointerId); }
          function dvizh(ev){ panel_postavit(window.innerWidth - ev.clientX); }
          function konets(ev){
            dvizh(ev);
            ruka.className = ruka.className.replace(' tyanem', '');
            ruka.removeEventListener('pointermove', dvizh);
            ruka.removeEventListener('pointerup', konets);
            ruka.removeEventListener('pointercancel', konets);
          }
          ruka.addEventListener('pointermove', dvizh);
          ruka.addEventListener('pointerup', konets);
          ruka.addEventListener('pointercancel', konets);
        });
      })(ruki[i]);
    }
  })();

  /* Имя и цель с главного экрана: живут в памяти браузера, ничего
     никуда не отправляется. Пустая строка — обычная подстановка,
     поэтому стёр написанное, и подсказка вернулась сама. */
  /* Ширина строки цели — по её тексту: тогда «Цель:» и написанное
     стоят по центру вместе. Мерка невидима и набрана тем же шрифтом. */
  var poleCeli=document.getElementById('tsel');
  var merkaCeli=document.getElementById('tsel-merka');
  function shirinaCeli(){
    if(!poleCeli || !merkaCeli){ return; }
    merkaCeli.textContent = poleCeli.value || poleCeli.placeholder || '';
    var w = merkaCeli.getBoundingClientRect().width;
    poleCeli.style.width = Math.ceil(w + 8) + 'px';
  }
  if(poleCeli){
    shirinaCeli();
    poleCeli.addEventListener('input', shirinaCeli);
    window.addEventListener('resize', shirinaCeli);
  }

  /* ---- кто учится и зачем ----
     Строка под путём на каждой странице. Имя и цель человек написал сам
     на главном экране, здесь мы их только читаем из памяти браузера:
     ничего не выдумываем и ничего не дописываем. Ни того, ни другого
     нет — строки на странице тоже нет. */
  function imya_stroka(){
    var stroka=document.getElementById('imya-stroka');
    if(!stroka){ return; }
    /* На главном экране эти же имя и цель стоят полями — там строка
       была бы повторением. */
    if(document.getElementById('imya')){ stroka.hidden=true; return; }
    var imya='', cel='';
    try{
      imya=(localStorage.getItem('shkola.imya')||'').trim();
      cel=(localStorage.getItem('shkola.tsel')||'').trim();
    }catch(e){}
    if(!imya && !cel){ stroka.hidden=true; return; }
    /* Цель читается как «Хочу …»: если так уже написано — не повторяем. */
    if(cel && !/^хочу/i.test(cel)){ cel='Хочу '+cel; }
    var kuski=[];
    if(imya){ kuski.push('<b>'+imya+'</b>'); }
    if(cel){ kuski.push(cel); }
    stroka.innerHTML=kuski.join(' · ');
    stroka.hidden=false;
  }
  imya_stroka();

  /* Имя в самой шапке — по её середине, где у сайтов стоит логотип:
     то же имя, что написано на главном экране. Пока имени нет, строки
     тоже нет. Обновляется и когда имя набирают: см. обработчик ввода. */
  function verh_imya(){
    var mesto=document.getElementById('verh-imya');
    if(!mesto){ return; }
    var imya='';
    try{ imya=(localStorage.getItem('shkola.imya')||'').trim(); }catch(e){}
    if(!imya){ mesto.hidden=true; mesto.textContent=''; return; }
    mesto.textContent=imya;
    mesto.hidden=false;
  }
  verh_imya();

  var polya=[['imya', 'shkola.imya'], ['tsel', 'shkola.tsel']];
  for(var p=0; p<polya.length; p++){
    var po=document.getElementById(polya[p][0]);
    if(!po || !dostupno()){ continue; }
    try{
      var bylo=localStorage.getItem(polya[p][1]);
      if(bylo){ po.value=bylo; }
      if(typeof shirinaCeli==='function'){ shirinaCeli(); }
    }catch(e){}
    (function(pole, klyuch){
      pole.addEventListener('input', function(){
        try{ localStorage.setItem(klyuch, pole.value); }catch(e){}
        /* Имя сменили — в шапке оно тоже меняется, не дожидаясь
           перехода на другую страницу. */
        if(klyuch==='shkola.imya'){ verh_imya(); }
      });
    })(po, polya[p][1]);
  }

  if(!dostupno()){
    // Запоминать негде: скрепку прячем, «Домой» ведёт на выбор класса.
    if(pin) pin.style.display='none';
  } else {
    obnovit();
    if(YA_VHOD){
      var z=rd();
      if(z && z!==VHOD && location.hash!=='#vybor'){
        location.replace(ROOT+encodeURI(z));
      }
    }
  }
})();
</script>"""


def _slovari():
    """Подключить pyphen — свою копию из «Инструменты/внешнее».

    Окружение между запусками не сохраняется: поставил пакет сегодня —
    завтра его нет. Поэтому копия лежит рядом с генератором; установленный
    пакет тоже подойдёт.
    """
    try:
        import pyphen
        return pyphen.Pyphen(lang='ru')
    except Exception:
        pass
    svojo = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'внешнее')
    if svojo not in sys.path:
        sys.path.insert(0, svojo)
    try:
        import pyphen
        return pyphen.Pyphen(lang='ru')
    except Exception as e:
        # Без переносов длинные слова в узкой панели рвутся посередине
        # («Географичес / кие»), и это видно только глазом.
        sys.stderr.write(f'ВНИМАНИЕ: переносы по слогам отключены ({e})\n')
        return None


_SLOGI = _slovari()

SHY = '\u00ad'
"""Мягкий дефис: браузер переносит по нему слово, только если оно целиком
не влезло в строку."""


TIR = re.compile(r'(?<=[\wА-Яа-яЁё])[—–](?=[\wА-Яа-яЁё])')
"""Знак промежутка — тире, вплотную зажатое между знаками.

Так записаны и годы («1533—1584»), и номера параграфов («§ 6–7»), и века
(«XVI—XVII»), и уровни («A2—B1»), и месяцы («Апрель—май»), и строки
оглавления («А—3»). Полосой из-за этого соединялось не только число
с числом, поэтому правило берёт любую пару знаков, а не только цифры.
Дефис (-) не трогаем: «премьер-министр» и «trenazhery-7-klass» — это не
промежуток.
"""
TIR_S_PROBELAMI = re.compile(r'(?<=[IVXLC])\s+[—–]\s+(?=[IVXLC])')
"""Тот же промежуток века, но записанный с пробелами: «XVII — XIX вв.»."""


def tire(tekst):
    """Промежуток между числами — коротким тире, отделённым пробелом.

    Длинное тире в промежутке («1 607—1 610») читалось полосой, которой
    цифры и соединялись: год выглядел одним числом. Короткое тире
    с пробелами отделяет знак от цифр — видно, что это промежуток.
    Правило одно на всю сборку: и годы, и номера параграфов, и страницы,
    и века, и уровни, и месяцы.
    Тире, которое уже отделено пробелами, не трогаем: «2026 — 5
    комплектов» и «С1 — 2 балла» — это знак между словами, а не
    промежуток, и он остаётся как был.
    """
    if not tekst:
        return tekst
    tekst = TIR_S_PROBELAMI.sub(' \u2013 ', str(tekst))
    return TIR.sub(' \u2013 ', tekst)


def tire_html(html):
    """Правило тире по всей странице — и только в тексте.

    Разметку и скрипты не трогаем: в атрибутах живут номера параграфов
    (метка пункта, адреса ссылок), и от них зависит, куда ведёт нажатие.
    """
    kuski = re.split(r'(<(?:script|style)\b.*?</(?:script|style)>)', html,
                     flags=re.S | re.I)
    itog = []
    for i, kusok in enumerate(kuski):
        if i % 2:                      # внутри скрипта или оформления
            itog.append(kusok)
            continue
        dla_teksta = re.split(r'(<[^>]*>)', kusok)
        itog.append(''.join(k if k.startswith('<') else tire(k)
                            for k in dla_teksta))
    return ''.join(itog)


def myagkie(tekst, min_dlina=10):
    """Расставить мягкие дефисы в длинных словах.

    Перенос по слогам — крайний случай: слово короче `min_dlina` остаётся
    целым и переносится на следующую строку целиком («кино и» / «докумен-
    талистика» только там, где «документалистика» не влезла бы и одна).
    """
    if not tekst:
        return tekst
    tekst = tire(tekst)
    if not _SLOGI:
        return tekst
    def slovo(m):
        w = m.group(0)
        if '-' in w or SHY in w:
            return w
        try:
            return _SLOGI.inserted(w, SHY)
        except Exception:
            return w
    return re.sub(r'[^\W\d_]{%d,}' % min_dlina, slovo, tekst, flags=re.U)


def dlitelnost(sek):
    """Время ролика словами: «48 мин», «1 ч 21 мин», «3 ч 42 мин».

    Часы считаем только там, где они есть: у урока «81 мин» читается
    хуже, чем «1 ч 21 мин», а у короткого ролика часов нет вовсе.
    """
    sek = int(sek or 0)
    if sek < 60:
        return ''
    ch, m = divmod(sek // 60, 60)
    return f'{ch} ч {m} мин' if ch else f'{m} мин'


def kroshechki(put, fayl):
    """Список (подпись, путь от корня пакета) — в html строки пути.

    Последний элемент — текущая страница, он без ссылки. Строка стоит
    отдельно под шапкой и приглушена: это подпись «где мы», а не
    подсветка.
    """
    if not put:
        # На входе крошки ни к чему: это и есть начало, писать «Выбор
        # класса» над плитками с классами незачем.
        return ''
    chasti = []
    for tekst, ssylka in put:
        if ssylka:
            chasti.append(f'<a href="{otnositelno(fayl, ssylka)}">{tekst}</a>')
        else:
            chasti.append(f'<span class="zdes">{tekst}</span>')
    return ('<div class="put-stroka">'
            + '<span class="razd">›</span>'.join(chasti)
            + '</div>')


def privet(podskazka_imya, podskazka_tsel=''):
    """Две строки главного экрана — для имени и для цели.

    Заголовков над строками нет: «Введи своё имя» и «Введи свою цель» —
    это подсказки внутри самих строк. Написанное живёт в браузере,
    поэтому ребёнок видит своё имя и свою цель каждый раз, когда
    открывает пакет: строка не подсказка на один раз, а постоянная
    часть экрана. Размер задаёт CSS: имя — как прежний заголовок,
    цель — как прежняя подпись.
    """
    polya = []
    if podskazka_imya:
        polya.append(
            '<input type="text" id="imya" autocomplete="off" '
            f'placeholder="{myagkie(podskazka_imya)}" '
            f'aria-label="{myagkie(podskazka_imya)}">')
    if podskazka_tsel:
        # Слово «Цель:» стоит вне строки ввода: стереть его нельзя,
        # а написанное встаёт сразу за ним.
        polya.append(
            '<div class="privet-tsel">'
            '<span class="privet-slovo">Цель:</span>'
            '<span class="privet-merka" id="tsel-merka" aria-hidden="true">'
            '</span>'
            '<input type="text" id="tsel" autocomplete="off" '
            f'placeholder="{myagkie(podskazka_tsel)}" '
            'aria-label="Цель на ближайший год">'
            '</div>')
    return '<div class="privet">' + ''.join(polya) + '</div>'


def kniga_stroka(tekst, podrobno=''):
    """Строка учебника под путём — и что за учебник, если её раскрыть.

    Сам текст — как был: приглушённая строка прямо на фоне, без цвета,
    без подложки и без подсветки. Раскрывается она в карточку учебника:
    обложка, авторы, издательство, год. Стрелка справа — единственная
    подсказка, что это раскрывающийся список.
    """
    if not tekst:
        return ''
    if not podrobno:
        return f'<div class="kniga-stroka">{myagkie(tekst)}</div>'
    return ('<details class="kniga-stroka">'
            '<summary><span class="kn-nazv">' + myagkie(tekst) + '</span>'
            f'<span class="strela">{ikona("шеврон")}</span></summary>'
            f'<div class="kn-podrobno">{podrobno}</div></details>')


def kartochka_uchebnika(oblozhka, nazv, avtory):
    """Раскрытая карточка учебника: обложка и подписи о ней.

    `oblozhka` — путь от текущей страницы. Обложка показывается маленькой
    (её размер задан в оформлении), а нажатие открывает её во весь экран:
    подробности обложки видно, но в списке она не занимает полстраницы.
    """
    kart = (f'<a class="kn-oblozhka" href="#" aria-label="Открыть обложку" '
            f'onclick="return shkOblozhka(this)">'
            f'<img src="{oblozhka}" alt="" loading="lazy"></a>'
            if oblozhka else '')
    return (f'<div class="kn-kartochka">{kart}'
            '<div class="kn-kartotekst">'
            f'<span class="kn-knazv">{myagkie(nazv)}</span>'
            f'<span class="kn-kavt">{myagkie(avtory)}</span>'
            '</div></div>')


RUTUBE_VIDEO = re.compile(r'rutube\.ru/video/([0-9a-fA-F]{32})')
"""Видео Rutube: именно их можно встроить в плеер. Короткие числовые
адреса — это плейлисты и каналы, они встраиваются по-другому."""

VK_VIDEO = re.compile(r'vk(?:video)?\.(?:com|ru)/(?:video|video_ext\.php\?[^"\']*?)'
                      r'(-?\d+)[_&](?:id=)?(\d+)')
"""Видео VK Видео: `vk.com/video-123_456`, `vkvideo.ru/video-123_456`
и уже готовый `video_ext.php?oid=-123&id=456`."""


def id_video(href):
    """Адрес видео для кадра — Rutube или VK Видео ('' — не видео).

    Раньше возвращался код, а кадр собирался приклеиванием: теперь сразу
    готовый адрес, потому что у двух площадок он устроен по-разному.
    Встраиваем только бесплатное: Rutube и VK Видео. Всё, что требует
    подписки (Okko, Wink, ivi, Kion), в пакет не попадает.
    """
    href = href or ''
    m = RUTUBE_VIDEO.search(href)
    if m:
        return f'https://rutube.ru/play/embed/{m.group(1)}/'
    m = VK_VIDEO.search(href)
    if m:
        return ('https://vk.com/video_ext.php?oid=' + m.group(1) +
                '&id=' + m.group(2) + '&hd=2')
    return ''


JS_PLAYERA = """<script>
(function(){
  var pleerGotov=false, ozhidanie=null, tek=null, poslT=0;

  /* Панель плейлиста на вертикальном планшете и на телефонах
     разворачивается на всю ширину экрана (Инструменты/разметка.py).
     Открытая сразу, она занимала бы весь экран — при входе на страницу
     видеоуроков было бы видно список, а не кадр. Поэтому здесь она
     закрыта, а вызывается кнопкой плейлиста на кадре. */
  if(window.innerWidth < MENYU-VO-VSYU){
    document.body.classList.remove('pleylist-otkryto');
  }

  function klyuch(){
    var h=(window.SHK_HOME||'')+'';
    return 'shkola.urok.'+(h||location.pathname);
  }
  function zapis(){
    try{ localStorage.setItem(klyuch(), JSON.stringify(tek)); }catch(e){}
  }
  function chto(){
    try{ return JSON.parse(localStorage.getItem(klyuch())||'null'); }
    catch(e){ return null; }
  }
  /* Ищем кадр по имени. Класс `pleyer-ramka` ставят ВСЕ кадры страницы
     (второй может быть в баннере лекций), а id у каждого свой: `ramka`
     у большого плеера, `banner-ramka` у кадра в баннере. */
  function ramka(){
    return document.getElementById('ramka')
        || document.querySelector('.pleyer-ramka');
  }
  function poslat(obj){
    var f=ramka();
    if(f && f.contentWindow){
      f.contentWindow.postMessage(JSON.stringify(obj), '*');
    }
  }

  /* ---- кадр ----
     Пока урок не выбран, iframe не создаётся вообще: страница ничего
     не тянет из сети. Кадр появляется только тогда, когда урок выбран
     или когда мы показываем последний — тогда видео стоит на паузе,
     видно его начало, и само ничего не играет. */
  function kadr(kod, sekunda, igrat){
    /* Кадр страницы ищем по имени, а не по классу: класс `pleyer-ramka`
       носят оба кадра, какие бывают на странице, — большой и баннерный. */
    var bann=document.getElementById('banner-mesto');
    var f=bann ? document.getElementById('banner-ramka')
               : document.getElementById('ramka');
    if(bann){
      /* На странице предмета большого плеера нет: кадр один — в баннере
         лекций, и он играет то, что выбрали в любой его подборке. */
      if(!f && kod){
        f=document.createElement('iframe');
        f.id='banner-ramka'; f.className='pleyer-ramka';
        f.setAttribute('allow','autoplay; fullscreen; picture-in-picture');
        f.setAttribute('allowfullscreen','');
        f.title='Лекция';
        bann.appendChild(f);
      }
      if(!f){ return; }
      if(f.getAttribute('data-kod')!==kod){ f.src=kod; }
      f.setAttribute('data-kod', kod);
      if(sekunda>2){
        pleerGotov=false; ozhidanie={sekunda:sekunda, igrat:!!igrat};
      } else {
        ozhidanie={sekunda:0, igrat:!!igrat}; otlozhennoe();
      }
      return;
    }
    var p=document.getElementById('pleyer');
    if(!p || !kod){ return; }
    if(!f){
      f=document.createElement('iframe');
      f.id='ramka'; f.className='pleyer-ramka';
      f.setAttribute('allow','autoplay; fullscreen; picture-in-picture');
      f.setAttribute('allowfullscreen','');
      f.title='Видеоурок';
      /* `kod` — уже готовый адрес встраивания: у Rutube и у VK Видео
         он свой, и собирать его здесь нечем. */
      f.src=kod;
      p.appendChild(f);
    } else if(f.getAttribute('data-kod')!==kod){
      f.src=kod;
    }
    f.setAttribute('data-kod', kod);
    ozhidanie={sekunda:sekunda||0, igrat:!!igrat};
    otlozhennoe();
  }
  function otlozhennoe(){
    if(!ozhidanie || !pleerGotov){ return; }
    var o=ozhidanie; ozhidanie=null;
    if(o.sekunda>2){ poslat({type:'player:setCurrentTime',
                             data:{time:o.sekunda}}); }
    if(o.igrat){ poslat({type:'player:play', data:{}}); }
  }

  /* ---- что запоминаем ----
     Урок, время на нём и досмотрен ли он. Секунду берём у самого
     плеера: он присылает её сообщением, а мы держим последнюю. */
  function vremya(t){
    if(!tek || typeof t!=='number'){ return; }
    if(Math.abs(t-poslT)<3){ return; }
    poslT=t; tek.vremya=t; zapis();
  }
  function dosmotreno(){
    if(!tek){ return; }
    tek.dosmotren=true; tek.vremya=0; zapis();
  }
  if(window.addEventListener){
    window.addEventListener('message', function(e){
      var m=e && e.data;
      if(typeof m==='string'){
        try{ m=JSON.parse(m); }catch(err){ return; }
      }
      if(!m || !m.type){ return; }
      if(m.type==='player:ready'){ pleerGotov=true; otlozhennoe(); }
      else if(m.type==='player:currentTime'){ vremya(m.data && m.data.time); }
      else if(m.type==='player:playComplete'){ dosmotreno(); }
      else if(m.type==='player:changeState'){
        var s=m.data && m.data.state;
        if(s==='playing'){ poslat({type:'player:currentTime'}); }
        else if(s==='paused'){ poslat({type:'player:currentTime'}); }
        else if(s==='stopped'){ dosmotreno(); }
      }
    });
  }

  /* ---- подсветка ----
     Активный пункт один: тот, который играет или ждёт на паузе. */
  function podsvetit(kod){
    /* Списки плейлистов подсвечиваются как раньше; пункты в баннере —
       своей подсветкой (.banner-trek), иначе нажатие в баннере гасило
       бы пункт в панели, а он остался бы открытым. */
    var vse=document.querySelectorAll('.trek');
    for(var i=0;i<vse.length;i++){
      vse[i].className=(vse[i].getAttribute('data-video')===kod)
        ? 'trek aktiven' : 'trek';
    }
    var svoi=document.querySelectorAll('.banner-trek');
    for(i=0;i<svoi.length;i++){
      svoi[i].className=(svoi[i].getAttribute('data-video')===kod)
        ? 'banner-trek aktiven' : 'banner-trek';
    }
  }
  function shapka(zag, glava){
    var z=document.getElementById('pleyer-zag');
    if(z && zag){ z.textContent=zag; }
    /* Над заголовком — глава: «Глава I. Эпоха Великих географических
       открытий». Приходит из плейлиста вместе с пунктом (data-glava);
       у пункта вне глав («Введение») её нет, и строки тогда нет. */
    var p=document.getElementById('pleyer-podzag');
    if(p){
      p.textContent = glava || '';
      p.hidden = !glava;
    }
  }
  function karta(skryt){
    var v=document.getElementById('pleyer-vybor');
    if(v){ v.style.display=skryt ? 'none' : ''; }
  }
  /* «Закрыть» на уведомлении: карточка уходит, кадр остаётся на паузе —
     тот урок, на котором остановились. Вернуть карточку можно тем, что
     выбрать урок заново. */
  window.shkZakrytKartu=function(){
    karta(true);
    return false;
  };

  function vklyuchit(kod, zag, nomer, tema, igrat, sekunda, glava){
    tek={kod:kod, zag:zag, nomer:nomer, tema:tema, glava:glava||'',
         vremya:sekunda||0, dosmotren:false};
    zapis();
    poslT=0;
    kadr(kod, sekunda, igrat!==false);
    shapka(zag, glava);
    podsvetit(kod);
    karta(true);
    var p=document.getElementById('pleyer');
    if(p && p.scrollIntoView){ p.scrollIntoView({block:'nearest'}); }
  }

  /* ---- кнопка в плейлисте: играем выбранный урок с начала ---- */
  /* Урок может быть нажат и в списке под кадром, и в панели. Открываем
     в панели тот плейлист, откуда его взяли: иначе подсветки там не
     видно, а пункт будто ни при чём. */
  function nabor_sverhu(a){
    var r=a.parentNode;
    while(r && r.getAttribute){
      var n=r.getAttribute('data-nabor');
      if(n!==null && n!==''){ return n; }
      r=r.parentNode;
    }
    return null;
  }
  window.shkIgrat=function(a){
    var kod=a.getAttribute('data-video');
    if(!kod){ return false; }
    var otkuda=nabor_sverhu(a);
    if(otkuda!==null){ otkryt_nabor(otkuda); }
    vklyuchit(kod, a.getAttribute('data-zag')||'',
              a.getAttribute('data-nomer')||'',
              a.getAttribute('data-tema')||'', true, 0,
              a.getAttribute('data-glava')||'');
    return false;
  };

  /* ---- сосед по плейлисту: кнопка «следующий» ---- */
  /* Соседа ищем в том плейлисте, который сейчас открыт: у вариантов
     свои списки, и «следующий» не должен прыгать в чужой. */
  function otkrytyy(){
    return document.querySelector('.pleylist.aktiven') || document;
  }
  /* Пункт из баннера лекций: у него своя среда — ни панели, ни номеров,
     только порядок сверху вниз. Поэтому соседа ищем там, где он сам. */
  function sosed_v_bannere(na){
    var otkryt=document.querySelector('.banner-nabor.aktiven')
            || document.querySelector('.banner-nabor');
    if(!otkryt || !tek){ return null; }
    var vse=otkryt.querySelectorAll('.banner-trek');
    for(var k=0;k<vse.length;k++){
      if(vse[k].getAttribute('data-video')===tek.kod){
        return vse[k+na] || null;
      }
    }
    return null;
  }
  function sosed(na){
    if(tek && document.querySelector('.banner-trek') &&
       !document.querySelector('.trek[data-video="'+(tek.kod||'')+'"]')){
      return sosed_v_bannere(na);
    }
    var vse=otkrytyy().querySelectorAll('.trek'), i=-1;
    for(var k=0;k<vse.length;k++){
      if(tek && vse[k].getAttribute('data-video')===tek.kod){ i=k; }
    }
    if(i<0){ return null; }
    return vse[i+na] || null;
  }
  function sleduyushchiy(){
    var a=sosed(1);
    if(!a){ return false; }
    return window.shkIgrat(a);
  }

  /* ---- карточка поверх кадра ----
     Текст и кнопки зависят от того, что было в прошлый раз: урок бросили
     на середине — предлагаем продолжить или взять следующий; урок
     досмотрели — предлагаем следующий или повтор. */
  function knopka(id, nadpis, dejstvie){
    var a=document.getElementById(id);
    if(!a){ return; }
    if(!nadpis){ a.style.display='none'; return; }
    a.style.display='';
    a.textContent=nadpis;
    a.onclick=function(){ dejstvie(); return false; };
  }
  function pokazat_kartu(h){
    var t=document.getElementById('vybor-tekst');
    var tret=document.getElementById('vybor-zakryt');
    if(tret){ tret.style.display=''; }
    var nomer=(h.nomer||'').trim();
    var tema=(h.tema||'').trim();
    /* Фильм, лекция или урок? У уроков подпись пункта — «§ 12», у фильмов
       и лекций на месте номера стоит время («1 ч 20 мин»). Фильм от
       лекции по подписи уже не отличить, поэтому страница называет себя
       сама: атрибут на body со словом «лекции». Разные у них только два
       слова — вопрос в шапке и кнопка «Следующая лекция»; всё остальное
       («посмотрели», «Посмотреть снова») годится обоим. */
    var kino=!!nomer && nomer.indexOf('§')!==0;
    var lekcii=kino && document.body.getAttribute('data-rezhim')==='лекции';
    var sled=sosed(1);
    if(h.dosmotren){
      if(t){ t.textContent=(kino ? '«'+tema+'» посмотрели'
                                 : (nomer ? nomer+' закончен'
                                          : 'Урок закончен')); }
      if(sled){
        knopka('vybor-glavnaya',
               lekcii ? 'Следующая лекция'
                      : (kino ? 'Следующий фильм'
                              : (nomer ? 'Начать '+
                                         (sled.getAttribute('data-nomer')
                                          || 'следующий')
                                       : 'Следующий параграф')), sleduyushchiy);
        knopka('vybor-vtoraya',
               kino ? 'Посмотреть снова'
                    : (nomer?'Повторить '+nomer:'Повторить'),
               function(){ vklyuchit(tek.kod, tek.zag, tek.nomer,
                                     tek.tema, true, 0, tek.glava); });
      } else {
        knopka('vybor-glavnaya',
               kino ? 'Посмотреть снова'
                    : (nomer?'Повторить '+nomer:'Повторить'),
               function(){ vklyuchit(tek.kod, tek.zag, tek.nomer,
                                     tek.tema, true, 0); });
        knopka('vybor-vtoraya', '', null);
      }
    } else {
      if(t){ t.textContent = kino
             ? 'Вы остановились на «'+tema+'»'+(nomer?', '+nomer:'')
             : 'Вы остановились на '+(nomer?nomer+' ':'')
               +(tema ? '«'+tema+'»' : ''); }
      knopka('vybor-glavnaya', 'Продолжить', function(){
        kadr(tek.kod, tek.vremya, true); karta(true);
      });
      knopka('vybor-vtoraya',
             sled ? (lekcii ? 'Следующая лекция'
                            : (kino ? 'Следующий фильм'
                                    : 'Следующий параграф')) : null,
             sleduyushchiy);
    }
    karta(false);
  }

  /* ---- какой плейлист открыт ----
     У одного и того же курса бывают разные записи: уроки по параграфам,
     короткие пересказы, разборы домашних заданий. Открыт всегда один:
     его список стоит в панели, его название — в шапке панели, и он же
     подсвечен в списке под кадром. Кадр эта функция не трогает: она
     только показывает список. */
  function imya_nabora(n){
    var vse=document.querySelectorAll('.pleylist');
    for(var i=0;i<vse.length;i++){
      if(vse[i].getAttribute('data-nabor')===String(n)){
        return vse[i].getAttribute('data-imya')||'';
      }
    }
    return '';
  }
  function otkryt_nabor(n){
    var vse=document.querySelectorAll('.pleylist'), i;
    for(i=0;i<vse.length;i++){
      var eto=(vse[i].getAttribute('data-nabor')===String(n));
      vse[i].style.display = eto ? '' : 'none';
      vse[i].className = eto ? 'pleylist aktiven' : 'pleylist';
    }
    var bl=document.querySelectorAll('.pl-plitka');
    for(i=0;i<bl.length;i++){
      var nash=(bl[i].getAttribute('data-nabor')===String(n));
      bl[i].className = nash ? 'panel-plitka pl-plitka tekushchiy'
                             : 'panel-plitka pl-plitka';
    }
    var zag=document.getElementById('pl-zag'), imya=imya_nabora(n);
    if(zag && imya){ zag.textContent=imya; }
  }

  /* Название плейлиста под кадром: открыть этот плейлист в панели.
     Кадр не трогаем — человек ещё выбирает, что смотреть: как только
     он нажмёт пункт в панели, урок включится. Так же ведёт себя и
     пункт бокового меню: он показывает раздел, а не открывает урок. */
  window.shkNabor=function(n){
    otkryt_nabor(n);
    window.shkPleylist(true);
    return false;
  };

  /* ---- при открытии страницы ----
     Смотрели раньше — показываем тот урок на паузе и спрашиваем,
     продолжать или взять следующий. Не смотрели — кадр остаётся
     пустым, а в шапке стоит вопрос «С какого параграфа начнём?». */
  function snachala(){
    if(document.getElementById('ramka')){ return; }
    var h=chto();
    if(!h || !h.kod){ return; }
    tek=h;
    tek.zag=h.zag||'';
    tek.nomer=h.nomer||'';
    tek.tema=h.tema||'';
    tek.glava=h.glava||'';
    /* Лекцию могли слушать из второй подборки баннера: открываем ту,
       где она лежит, — иначе подсветки не видно. */
    if(window.shkBannerGde){ window.shkBannerGde(h.kod); }
    // Урок мог быть из другого варианта плейлиста (например, смотрели
    // короткие пересказы, а открыт по умолчанию полный курс): открываем
    // тот вариант, где он лежит, иначе подсветку не было бы видно.
    var vse=document.querySelectorAll('.trek'), i;
    for(i=0;i<vse.length;i++){
      if(vse[i].getAttribute('data-video')!==h.kod){ continue; }
      var rod=vse[i].parentNode;
      while(rod && !rod.getAttribute){
        rod = rod.parentNode;
      }
      while(rod && !rod.getAttribute('data-nabor')){
        rod = rod.parentNode;
      }
      if(rod && rod.getAttribute('data-nabor')){
        otkryt_nabor(rod.getAttribute('data-nabor'));
      }
      /* Глава — из самого пункта: в записи её может не быть (урок
         запоминали до того, как у пунктов появилась глава). */
      if(!tek.glava){ tek.glava=vse[i].getAttribute('data-glava')||''; }
      break;
    }
    kadr(h.kod, null, false);   // пауза: видно начало урока, не чёрный экран
    shapka(tek.zag, tek.glava);
    podsvetit(h.kod);
    pokazat_kartu(tek);
  }
  /* ---- переход по метке: «смотреть видео по § 23» ----
     Из тренажёра на урок ведёт ссылка «видеоуроки.html#par-23»: метка
     стоит у пункта плейлиста. Запускаем этот пункт тем же путём, что
     и по клику, — с открытием своего плейлиста и подсветкой. */
  function po_metke(){
    var h=location.hash || '';
    if(h.indexOf('#par-')!==0){ return false; }
    var a=document.getElementById(h.slice(1));
    if(!a || !a.className || a.className.indexOf('trek')<0){ return false; }
    return window.shkIgrat(a);
  }
  if(document.readyState==='complete'){ snachala(); po_metke(); }
  else { window.addEventListener('load', function(){ snachala(); po_metke(); }); }
})();
</script>"""


def sklonenie(chislo, odin, dva, mnogo):
    """«1 лекция», «2 лекции», «10 лекций» — по-русски.

    Нужно там, где числительное с существительным считается по данным,
    а не пишется руками: если подборок станет больше, «10 лекций» в знаке
    должно пересчитаться само. Исключение 11—14 помним: «11 лекций»,
    а не «11 лекция».
    """
    ostatok = abs(int(chislo)) % 100
    if 11 <= ostatok <= 14:
        slovo = mnogo
    elif ostatok % 10 == 1:
        slovo = odin
    elif 2 <= ostatok % 10 <= 4:
        slovo = dva
    else:
        slovo = mnogo
    return f'{chislo} {slovo}'


def banner_ukazatel(zagolovok, podpis, ssylka, fon=None):
    """Баннер-знак над плитками: вход на страницу лекций.

    От `banner_lekciy` отличается тем, что ничего не играет и плеера
    с собой не приносит: это дверь. Заголовок («Лекции») и подпись
    («Мединский · лекции по курсу истории за седьмой класс») — и вся
    плашка целиком ссылка на страницу лекций. Отдельной кнопки нет:
    кнопка внутри ссылки только сбивает — с пульта её видно как вторую
    цель, а мишень и так во весь знак. Счёта разделов и лекций тоже нет:
    списком их видно на самой странице.

    Рисунок (`fon`, путь от корня пакета) ложится на знак так же, как
    на плашку предмета, — см. `a.plitka.s-kartinkoy`. Путь пересчитывает
    `put_kartinki`: он считается от файла оформления, а не от страницы.
    """
    cls = 'banner-znak' + (' s-kartinkoy' if fon else '')
    stil = f' style="--kartinka:url(\'{put_kartinki(fon)}\')"' if fon else ''
    # Текст — теми же классами, что у плашки (.nazv и .poyas): шрифт,
    # отступы и переносы не могут разойтись с плашками, потому что
    # правило у них одно.
    return (f'<a class="{cls}" href="{ssylka}"{stil}>'
            f'<span class="nazv">{myagkie(zagolovok)}</span>'
            f'<span class="poyas">{myagkie(podpis)}</span>'
            f'</a>')


def razdel_gotovitsya(nazvanie='Раздел готовится', tekst=''):
    """Карточка для раздела, который ещё не наполнен.

    Плашка раздела стоит с первого дня, и страница у неё должна быть
    с первого дня тоже: ссылка в никуда — ошибка, а пустой белый лист
    читается как поломка.

    Кроме самой карточки на такой странице ничего нет: ни заголовка,
    ни подписи, ни подсказки. Заголовок повторял бы плашку, из которой
    сюда пришли, подсказка про кнопку «Назад» — то же самое, а обещание
    «материалы подбираются» сказано самими словами карточки. Пустые
    поля карточки в разметку не попадают.
    """
    tek = (f'<span class="zg-tekst">{myagkie(tekst)}</span>'
           if tekst else '')
    return (f'<div class="zagotovka">'
            f'<span class="zg-nazv">{myagkie(nazvanie)}</span>{tek}</div>')


def banner_lekciy(nazvanie, podpis, nabor):
    """Баннер над плитками страницы предмета: лекции одного автора.

    `nabor` — [(имя подборки, [(подпись времени, тема, адрес), …]), …].
    Первая подборка стоит открытой, вторая — рядом кнопкой; кадр
    появляется только после нажатия, как и на страницах видеоуроков:
    сама страница ничего не запускает.

    Кадр у баннера один и свой (`banner-ramka`) — большого плеера на
    странице предмета нет. Играет всё тот же `shkIgrat`: он отдаёт
    ссылку в кадр, а кадр он найдёт сам (см. `ramka()` и `kadr()`).
    """
    knopki = ''.join(
        f'<a class="banner-knopka{" aktiven" if i == 0 else ""}" href="#" '
        f'onclick="return shkBanner({i})">'
        f'{myagkie(imya)} · {len(ryady)}</a>'
        for i, (imya, ryady) in enumerate(nabor))
    spiski = ''
    for i, (imya, ryady) in enumerate(nabor):
        punkty = ''
        for vremya, tema, href in ryady:
            adres = id_video(href)
            if not adres:
                continue
            punkty += (f'<li><a class="banner-trek" href="{href}" '
                       f'data-video="{adres}" '
                       f'data-zag="{myagkie(tema)}" data-nomer="{vremya}" '
                       f'data-tema="{myagkie(tema)}" '
                       f'onclick="return shkIgrat(this)">'
                       f'<span class="bt-vremya">{vremya}</span>'
                       f'<span class="bt-tema">{myagkie(tema)}</span></a></li>')
        otkryto = '' if i == 0 else ' hidden'
        spiski += f'<ol class="banner-nabor" data-nabor="{i}"{otkryto}>{punkty}</ol>'
    telo = (f'<section class="banner" id="banner">'
            f'<span class="banner-nazv">{myagkie(nazvanie)}</span>'
            f'<span class="banner-podpis">{myagkie(podpis)}</span>'
            f'<div class="banner-knopki">{knopki}'
            f'<a class="banner-igrat" href="#" '
            f'onclick="return shkBannerIgrat()">Смотреть</a></div>'
            f'<div class="banner-mesto" id="banner-mesto"></div>'
            f'<div class="banner-spiski">{spiski}</div></section>')
    # Скрипт плеера баннер приносит с собой: на странице предмета
    # никакого плеера больше нет, и взять его неоткуда.
    return telo + BANNER_JS + JS_PLAYERA


BANNER_JS = """<script>
(function(){
  /* Баннер живёт своей жизнью: у него свои кнопки подборок и своя
     подсветка пунктов (.banner-trek). Иначе нажатие в баннере гасило
     бы пункт в панели плейлиста, а он остался бы открытым. */
  function spiski(){ return document.querySelectorAll('.banner-nabor'); }
  function knopki(){ return document.querySelectorAll('.banner-knopka'); }
  function otkrytaya(){
    return document.querySelector('.banner-nabor:not([hidden])')
        || document.querySelector('.banner-nabor');
  }
  window.shkBanner=function(n){
    var s=spiski(), k=knopki(), i;
    for(i=0;i<s.length;i++){
      if(i===n){ s[i].removeAttribute('hidden'); }
      else { s[i].setAttribute('hidden',''); }
    }
    for(i=0;i<k.length;i++){
      k[i].className=(i===n) ? 'banner-knopka aktiven' : 'banner-knopka';
    }
    return false;
  };
  /* «Смотреть» — первая лекция открытой подборки: то же самое, что
     нажать на неё. Дальше кадр и словарь страницы работают сами. */
  window.shkBannerIgrat=function(){
    var a=otkrytaya().querySelector('.banner-trek');
    return a ? window.shkIgrat(a) : false;
  };
  /* Возврат на страницу: лекцию могли слушать из второй подборки —
     открываем ту, где она лежит, иначе подсветки не видно. */
  window.shkBannerGde=function(kod){
    var s=spiski(), i;
    for(i=0;i<s.length;i++){
      if(s[i].querySelector('.banner-trek[data-video="'+kod+'"]')){
        window.shkBanner(i);
        return true;
      }
    }
    return false;
  };

})();
</script>"""


NOMER_RYAD = re.compile(r'^§\s*(\d+)\s*[–—-]\s*(\d+)$')
"""Номер параграфа-пары: «§ 10–11». В учебнике 7 класса уроки идут парами."""


def nomer_stolbikom(nomer):
    """Номер для колонки списка: «§ 10–11» → «§ 10,» и «11» столбиком.

    Сдвоенный параграф записываем двумя строками с запятой, а не тире:
    так и единичный («§ 9»), и парный номер остаются в одной колонке —
    раньше «§ 10–11» была вдвое шире «§ 9» (93 px против 50), колонка
    разъезжалась, и темы в списке начинались на разном месте.
    """
    m = NOMER_RYAD.match((nomer or '').strip())
    if not m:
        return nomer
    return f'§ {m.group(1)},<br>{m.group(2)}'


def nomer_v_tekste(nomer):
    """Тот же номер внутри строки: «§ 10–11» → «§ 10, 11»."""
    m = NOMER_RYAD.match((nomer or '').strip())
    if not m:
        return nomer
    return f'§ {m.group(1)}, {m.group(2)}'


ZNAK_BEZ_NOMERA = ('<svg viewBox="0 0 24 24" aria-hidden="true">'
                   '<circle cx="12" cy="12" r="8.6" fill="none" '
                   'stroke="currentColor" stroke-width="2.4"/>'
                   '<circle cx="12" cy="12" r="2.9" fill="currentColor"/>'
                   '</svg>')
"""Знак пункта, у которого нет параграфа: кольцо с точкой внутри.

Стоит там, где у параграфов номер: «Введение», «Итоговое повторение»,
«Итоги главы». Размером с цифру — колонка номеров от него не съезжает.
"""


def metka_paragrafa(nomer):
    """Номер параграфа — в метку пункта: «§ 10–11» → «10-11».

    Метка нужна ссылке «смотреть видео по параграфу» из тренажёра: она
    ставится пункту плейлиста, и по ней урок открывается сразу. Одна
    и та же метка — и у длинного тире, и у короткого, и у пары: иначе
    у половины параграфов ссылка вела бы в пустоту.
    """
    return (str(nomer).replace('§', '').strip()
            .replace('–', '-').replace('—', '-').replace(' ', ''))


def blok_playera(nabor, vopros=None, kak_v_dannyh=False, zag_spiska='',
                 niz=''):
    """Плеер, кнопки вариантов под ним и плейлист — в панели справа.

    `nabor` — [(название, ryady)]: один или несколько вариантов одного
    и того же курса. Варианты бывают, когда по учебнику есть разные
    записи: уроки по параграфам, короткие пересказы, разборы домашних
    заданий, повторение. Под плеером стоят кнопки вариантов — нажали,
    и в панели справа встаёт выбранный плейлист, а в кадре (на паузе)
    его первое видео. Пока вариант один, кнопок нет.

    `ryady` — [(номер, тема, ссылка на видео Rutube)]. Пока страница
    открыта, пункты меняют видео по нажатию, ничего не перезагружая.

    `kak_v_dannyh` — оставить порядок пунктов таким, каким он записан
    в данных. Нужно странице лекций: лекции пронумерованы сериями
    (1-я, 2-я, 3-я…), а на месте номера у них стоит время, по которому
    сортировать нечего — сортировка и рассыпала бы серии.

    `zag_spiska` — надпись над списком под кадром («Плейлисты»,
    «Подборки»). `niz` — готовая разметка блока «Разделы» (плашки
    материалов предмета): она идёт последней, под списками.

    Возвращает пару: разметку страницы и разметку панели плейлиста
    отдельно. Панель — выезжающая, position:fixed, и стоять она должна
    снаружи контейнера рабочей ширины (см. `sobrat`), поэтому её
    отдают наверх, а не кладут в середину страницы.
    """
    # Можно передать и просто список пунктов — тогда вариант один.
    if nabor and not (isinstance(nabor[0], tuple) and len(nabor[0]) == 2
                      and isinstance(nabor[0][1], (list, tuple))):
        nabor = [('По параграфам', nabor)]

    def spisok(ryady):
        """Пункты одного плейлиста."""
        # Порядок — по номеру параграфа, если номера есть: ребёнок идёт
        # по учебнику, а не в том порядке, в котором курс выкладывал
        # ролики. Но если курс разбит на темы (есть заголовки групп),
        # порядок автора не трогаем: сортировка рассовала бы пункты
        # одной темы по разным местам.
        def klyuch(i):
            m = re.search(r'(\d+)', ryady[i][0] or '')
            return (int(m.group(1)) if m else 10 ** 6, i)

        nomerov = sum(1 for r in ryady if r[2] and (r[0] or '').strip())
        grupp = any(not r[2] for r in ryady)
        po_nomeram = nomerov and not grupp and not kak_v_dannyh
        poryadok = (sorted(range(len(ryady)), key=klyuch) if po_nomeram
                    else list(range(len(ryady))))

        treki, glava = [], ''
        for i in poryadok:
            nomer, tema, href = ryady[i]
            if not href:
                # Заголовок главы (или темы курса): он же — подзаголовок
                # над кадром для всех своих пунктов.
                glava = tema or ''
                treki.append(f'<div class="trek-gruppa">{myagkie(tema)}</div>')
                continue
            kod = id_video(href)
            if not kod:
                continue
            if nomer:
                # Парный параграф встаёт в колонку двумя строками
                # («§ 10,» и «11») — так и единичный, и парный номер
                # занимают одну колонку (см. nomer_stolbikom).
                # Номер параграфа — в фиксированную колонку; время
                # проигрывания (кино, лекции) — своим классом: оно
                # длиннее колонки и должно стоять строкой.
                klass = ('trek-nomer' if nomer.startswith('§')
                         else 'trek-nomer trek-vremya')
                nom = (f'<span class="{klass}">'
                       f'{nomer_stolbikom(nomer)}</span>')
                # «§ 1. Мир на заре Нового времени» — как в учебнике.
                # У кино в колонке время, и точка там не нужна.
                zag = (f'{nomer_v_tekste(nomer)}. {tema}'
                       if nomer.startswith('§')
                       else f'{nomer} {tema}')
            else:
                nom = (f'<span class="trek-nomer trek-kolco">'
                       f'{ZNAK_BEZ_NOMERA}</span>')
                zag = tema
            zag = zag.strip().replace('"', '').replace("'", '')
            # Метка пункта — по номеру параграфа: на неё ведёт ссылка
            # «смотреть видео по параграфу» из тренажёра (см.
            # metka_paragrafa). Пункты без номера («Введение») остаются
            # без метки: открывать по номеру у них нечего.
            nom_metki = metka_paragrafa(nomer)
            metka = (f' id="par-{nom_metki}"'
                     if nom_metki and nom_metki[0].isdigit() else '')
            treki.append(f'<a class="trek" href="{href}" data-video="{kod}" '
                         f'data-zag="{myagkie(zag)}" data-nomer="{nomer or ""}" '
                         f'data-tema="{myagkie(tema)}" '
                         f'data-glava="{myagkie(glava)}"{metka} '
                         f'onclick="return shkIgrat(this)">{nom}'
                         f'<span class="trek-tema">{myagkie(tema)}</span></a>')
        return treki

    spiski = [(imya, spisok(ryady)) for imya, ryady in nabor]
    spiski = [(imya, t) for imya, t in spiski
              if any('class="trek"' in x for x in t)]
    if not spiski:
        return ''
    # Плейлисты под кадром: СПИСОК ПЛЕЙЛИСТОВ, без их содержимого.
    # Строка — тот же класс, что у пунктов бокового меню, поэтому вид
    # один и тот же: обычный текст, при наведении подложка, у открытого
    # плейлиста подложка и жёлтая чёрточка слева. Нажатие открывает
    # этот плейлист в панели справа — уроки там, где им и место.
    # Под кадром: глава (её ставит скрипт вместе с пунктом), линия-
    # разделитель, надпись и сами строки плейлистов. Открытый плейлист
    # отмечен так же, как текущий пункт меню (класс tekushchiy).
    pod_video = (
        '<div class="pleyer-niz">'
        '<span class="pleyer-podzag" id="pleyer-podzag" hidden></span>'
        '<div class="pl-razd"></div>'
        f'<div class="pl-zagolovok">{myagkie(zag_spiska)}</div>'
        '<div class="pl-vse">' + ''.join(
            f'<a class="panel-plitka pl-plitka'
            f'{" tekushchiy" if n == 0 else ""}" '
            f'href="#" data-nabor="{n}" onclick="return shkNabor({n})">'
            f'{myagkie(imya)}</a>'
            for n, (imya, t) in enumerate(spiski)) + '</div>'
        f'{niz}'
        '</div>')
    # Имя плейлиста лежит и в самой панели: шапка панели показывает
    # название того плейлиста, который открыт.
    panely = ''.join(
        f'<div class="pleylist{" aktiven" if n == 0 else ""}" '
        f'data-nabor="{n}" data-imya="{myagkie(imya)}"'
        + ('' if n == 0 else ' style="display:none"') + '>'
        + ''.join(t) + '</div>'
        for n, (imya, t) in enumerate(spiski))

    # В шапке — вопрос, а не первый урок: само ничего не запускается,
    # урок выбирает человек. Как только выбрал, здесь встаёт его название.
    # Слова зависят от страницы: у уроков подпись пункта — «§ 12»,
    # у кино — время. По первой подписи и понятно, спрашивать про
    # параграф или про фильм.
    # Подписи берём из самих рядов (`nabor`), а не из готовых списков:
    # в `spiski` лежат уже строки разметки, и первый их символ — «<».
    _podpisi = [r[0] for _imya, _ryady in nabor for r in _ryady if r and r[0]]
    # Обычно вопрос выходит из подписей пунктов: у уроков это «§ 12»,
    # у кино и лекций — время. Но фильм от лекции по подписи не отличить,
    # поэтому страница лекций называет свой вопрос сама (`vopros`).
    if vopros is None:
        vopros = ('Что будем смотреть?'
                  if _podpisi and not _podpisi[0].startswith('§')
                  else 'С какого параграфа начнём?')
    # Списки под кадром: у уроков это плейлисты, у кино и лекций —
    # подборки. Слово своё у каждой страницы, поэтому его передают сюда.
    if not zag_spiska:
        zag_spiska = ('Плейлисты'
                      if _podpisi and _podpisi[0].startswith('§')
                      else 'Подборки')
    # Что играет — над плеером: под ним подпись прижималась бы
    # к плейлисту, а сверху у неё своё место и воздух до кадра.
    # Карточка поверх кадра. Показывается только при возврате: текст и
    # кнопки ставит скрипт — он один знает, досмотрели урок или бросили.
    karta = ('<div class="vybor-karta" id="vybor-karta">'
             '<a class="vybor-zakryt" id="vybor-zakryt" href="#" '
             'aria-label="Закрыть" onclick="return shkZakrytKartu()">'
             + ikona('закрыть') + '</a>'
             '<span class="vybor-tekst" id="vybor-tekst"></span>'
             '<span class="vybor-knopki">'
             '<a class="vybor-knopka" id="vybor-glavnaya" href="#"></a>'
             '<a class="vybor-knopka vtoraya" id="vybor-vtoraya" '
             'href="#"></a>'
             '</span></div>')
    zakryt = ('<a class="panel-zakryt" href="#" aria-label="Закрыть плейлист" '
              'onclick="return shkPleylist(false)">' + ikona('закрыть') + '</a>')
    # В шапке панели стоит название открытого плейлиста, а не слово
    # «Плейлист»: в подборках их бывает несколько, и видно, какой открыт.
    # Кнопка на кадре: панель закрыли крестиком — вернуть её можно
    # отсюда, значком плейлиста.
    knopka_pleylista = ('<a class="pleyer-knopka" href="#" '
                        'aria-label="Плейлист" '
                        'onclick="return shkPleylistTog()">'
                        + ikona('плейлист') + '</a>')
    panel_pleylista = (f'<aside class="panel" id="pleylist-panel">'
                       f'<div class="panel-verh">'
                       f'<span class="panel-zag" id="pl-zag">'
                       f'{myagkie(spiski[0][0])}</span>{zakryt}'
                       f'</div>'
                       f'<div class="panel-telo">{panely}</div></aside>'
                       '<div class="panel-tyanulka pleylista" tabindex="0" '
                       'role="separator" aria-orientation="vertical" '
                       'aria-label="Изменить ширину" '
                       'onkeydown="return shkTyan(event)"></div>')
    # Над заголовком — глава: пока урок не выбран, её нет (в шапке стоит
    # вопрос), при выборе она приходит из плейлиста вместе с пунктом.
    stranica = (f'<div class="pleyer-wrap">'
                f'<div class="pleyer-shapka">'
                f'<span class="pleyer-zag" id="pleyer-zag">'
                f'{myagkie(vopros)}</span>'
                f'</div>'
                f'<div class="pleyer-mesto">'
                f'<div class="pleyer" id="pleyer">{knopka_pleylista}</div>'
                f'<div class="pleyer-vybor" id="pleyer-vybor" '
                f'style="display:none">{karta}</div>'
                f'</div>'
                f'{pod_video}</div>{chr(10)}{JS_PLAYERA}')
    return stranica, panel_pleylista


def zapisat_css():
    """Записать оформление пакета отдельным файлом.

    Файл лежит внутри пакета и перезаписывается при каждой сборке: если
    он отстанет от страниц, страницы молча потеряют вид. Поэтому сборка
    зовёт это первым делом.
    """
    polny = os.path.join(PAKET, *CSS_FAYL.split('/'))
    os.makedirs(os.path.dirname(polny), exist_ok=True)
    io.open(polny, 'w', encoding='utf-8').write(CSS)
    return CSS_FAYL


def sobrat(zagolovok, podzagolovok, bloki, fayl, put=None,
           podskazka=None, primechanie=None, indeks=False,
           menyu_spisok=None, menyu_zagolovok='',
           kniga=None, klassy=None, telo_klass='', paneli='',
           rezhim=''):
    """Собрать страницу пакета и записать её в Проект/.

    `fayl` — путь от корня пакета, например
    «База данных/HTML/8 класс/Геометрия/видеоуроки.html».
    `put` — строка пути: [(подпись, путь от корня пакета)], последняя
    без пути. `put=None` означает «это вход».

    `menyu_spisok` — [(подпись, путь от корня пакета)] для бокового меню:
    предметы текущего класса. `klassy` — [(название, путь)] всех классов
    пакета: списка классов в меню больше нет (класс выбирают плитками на
    его странице), поэтому довод остался только у вызовов и не читается.

    `kniga` — готовая строка учебника (её собирает kniga_stroka). Одна
    и та же на странице предмета и на всех страницах его материалов.

    `telo_klass` — класс для тега body: на видеоуроках это
    «pleylist-otkryto», то есть плейлист стоит открытым сразу, а значок
    меню переключает меню и плейлист в одной и той же панели.

    `paneli` — разметка выезжающей панели плейлиста (её отдаёт
    blok_playera). Она ставится тем же слоем, что и меню, — снаружи
    контейнера рабочей ширины.

    `rezhim` — чем страница себя называет (`data-rezhim` на body): пока
    это нужно только странице лекций («лекции»). Плеер по подписям
    различает урок и фильм, а лекцию от фильма отличить нечем — и там,
    где слова другие, страница говорит о себе сама.
    """
    # На страницах-индексах (выбор класса, предмета, материала) ни
    # заголовка, ни подсказки не нужно: где мы, и так видно по
    # хлебным крошкам в шапке, а что делать — понятно по плиткам.
    if indeks:
        shapka = ''
    else:
        if podskazka is None:
            podskazka = ('Стрелками на пульте выберите нужный пункт и нажмите '
                         '<strong>OK</strong>. Кнопка <strong>«Назад»</strong> '
                         'вернёт к этому списку.')
        shapka = (f'<h1>{zagolovok}</h1>\n'
                  f'<p class="pod">{podzagolovok}</p>\n'
                  f'<p class="podskazka">{podskazka}</p>')
    # «Домой» ведёт на закреплённую страницу — её подставляет javascript.
    # Без javascript (и когда ничего не закреплено) это просто переход
    # на вход; #vybor — метка: с ней вход НЕ перебрасывает на закреплённую
    # страницу, то есть «Домой» всегда показывает выбор класса.
    vhod = otnositelno(fayl, VHOD) + '#vybor'

    # Значок меню один на обе панели: на видеоуроках меню и плейлист
    # стоят в одной и той же среде, и этот же значок возвращает
    # плейлист — поэтому отдельного пункта «Плейлист» в меню нет.
    menyu = ('<a class="tumbler ikonka" href="#panel" aria-label="Меню" '
             'onclick="return shkMenu()">' + ikona('меню') + '</a>')

    # Скрепка есть на каждой странице, вход не исключение: закрепить вход
    # — значит сбросить домашнюю страницу и открывать выбор класса.
    pin = ('<a class="tumbler ikonka" id="pin" href="#" '
           'aria-label="Закрепить">' + ikona('скрепка') + '</a>')

    # Меню: сверху название класса, ниже — предметы текущего класса.
    # Списка классов здесь нет: класс выбирают плитками на его странице,
    # а раскрывающийся список в меню повторял эти же плитки и звал не
    # туда. «Открепить» отдельным пунктом тоже не нужно: домашнюю
    # страницу меняет скрепка в шапке.
    zagolovok_klassa = menyu_zagolovok or 'Выберите класс'
    imya_klassa = (f'<span class="klass-imya">{myagkie(zagolovok_klassa)}'
                   f'</span>')

    # Разделитель здесь не нужен: у шапки панели своя нижняя линия, и
    # два разделителя подряд читались одной задвоенной полосой. Список
    # предметов отделён от шапки тем же воздухом, что и в панели плейлиста.
    punkte = ''
    if menyu_spisok:
        # Пункт, на котором мы сейчас, отмечается как текущий: подложка
        # и жёлтая чёрточка. По этому же признаку список классов выше
        # отмечает текущий класс.
        punkte = ''.join(
            f'<a class="panel-plitka{" tekushchiy" if kuda == fayl else ""}" '
            f'href="{otnositelno(fayl, kuda)}">'
            f'{myagkie(tekst)}</a>'
            for tekst, kuda in menyu_spisok)
    panel = (f'<aside class="panel" id="panel">'
             f'<div class="panel-verh">{imya_klassa}'
             f'<a class="panel-zakryt" href="#" aria-label="Закрыть" '
             f'onclick="return shkPanel(false)">{ikona("закрыть")}</a>'
             f'</div><div class="panel-telo">{punkte}</div></aside>'
             '<div class="panel-tyanulka menyu" tabindex="0" '
             'role="separator" aria-orientation="vertical" '
             'aria-label="Изменить ширину" '
             'onkeydown="return shkTyan(event)"></div>')

    # Строка с именем и целью стоит под путём, выше учебника: маленькая,
    # серым, как название учебника. Наполняет её скрипт из памяти браузера
    # (там же, где живут имя и цель с главного экрана). Пусто — строки нет.
    imya = ('<div class="imya-stroka" id="imya-stroka" hidden></div>')

    verh = (VERH.replace('{put}', kroshechki(put, fayl))
                .replace('{imya}', imya)
                .replace('{menyu}', menyu)
                .replace('{kniga}', kniga or '')
                .replace('{vhod}', vhod)
                .replace('{pin}', pin)
                # Панель меню стоит не в шапке, а снаружи контейнера
                # рабочей ширины: см. {paneli} в шаблоне страницы.
                .replace('{panel}', '')
                .replace('{nazad}', ikona('назад'))
                .replace('{vpered}', ikona('вперёд'))
                .replace('{domoy}', ikona('домой')))

    koren_js = otnositelno(fayl, KOREN)
    koren_js = '' if koren_js == '.' else koren_js + '/'

    js = JS % {'home': fayl,
               'root': koren_js,
               'vhod': VHOD,
               'ya_vhod': 'true' if put is None else 'false'}

    niz = f'<p class="niz">{primechanie}</p>' if primechanie else ''
    telo = f' class="{telo_klass}"' if telo_klass else ''
    # Признак страницы для скрипта: плеер один на все страницы, а слова
    # у лекций свои (см. `rezhim` в описании выше).
    telo += f' data-rezhim="{rezhim}"' if rezhim else ''
    # Выезжающие панели — меню и плейлист — стоят одним слоем СНАРУЖИ
    # контейнера рабочей ширины: внутри него их position:fixed считался
    # бы от контейнера, а не от окна, и панель уехала бы за край
    # экрана. `paneli` передаёт страница, у которой есть плейлист.
    paneli_vse = panel + (chr(10) + paneli if paneli else '')

    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{zagolovok}</title>
<link rel="stylesheet" href="{otnositelno(fayl, CSS_FAYL)}">
</head>
<body{telo}>
<div class="{_razmetka.ZONA_KLASS}">
<div class="wrap">
{verh}
{shapka}
{chr(10).join(bloki)}
{niz}
</div>
</div>
{paneli_vse}
{js}
</body>
</html>
"""
    html = perevesti_puti(html, fayl)
    # Одна напоследок: промежутки между числами — коротким тире с пробелом
    # (см. tire). Страница собрана целиком — здесь и видно все числа.
    html = tire_html(html)
    polny = os.path.join(PAKET, *fayl.split('/'))
    os.makedirs(os.path.dirname(polny), exist_ok=True)
    with open(polny, 'w', encoding='utf-8') as f:
        f.write(html)
    return polny, len(html)

# Порог «панель во всю ширину» один на всю сборку: он берётся из той же
# таблицы разметки (Инструменты/разметка.py), что и CSS.
JS = JS.replace('MENYU-VO-VSYU', str(_razmetka.MENYU_VO_VSYU))
JS_PLAYERA = JS_PLAYERA.replace('MENYU-VO-VSYU', str(_razmetka.MENYU_VO_VSYU))
for _imya, _tekst in (('JS', JS), ('JS_PLAYERA', JS_PLAYERA)):
    assert 'MENYU-VO-VSYU' not in _tekst, \
        f'в {_imya} остался неподставленный порог ширины меню'
