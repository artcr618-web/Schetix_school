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
«База данных/8 класс/Геометрия/видеоуроки.html»). Относительные ссылки
для каждой страницы считаются здесь же, поэтому при переезде файлов
править html не нужно.
"""
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
"""Папка со всеми страницами. Имена папок и файлов — по-русски."""

VHOD = 'Начать учиться.html'
"""Единственный файл в корне пакета (и в корне флешки)."""

KOREN = '.'
"""Путь от корня пакета до корня пакета — для хлебных крошек."""


def otnositelno(otkuda, kuda):
    """Ссылка со страницы `otkuda` на страницу `kuda` (обе от корня)."""
    papka = posixpath.dirname(otkuda)
    put = posixpath.relpath(kuda, papka) if papka else kuda
    return put


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
    # их нельзя: «Что не нашлось.html» стоит в корне рядом с главной
    # страницей и собирается своим скриптом (Инструменты/gen_spisok.py).
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
.wrap{max-width:1500px; margin:0 auto;
  /* Поля по краям: на широком экране 44 px, на телефоне 20 px
     (см. POLYA в Инструменты/разметка.py). Плашка занимает всю
     строку, и на телефоне широкие поля съедали бы четверть кадра. */
  padding:22px clamp(20px, 4vw, 44px)}

/* ---- шапка, одинаковая на всех страницах ---- */
nav.verh{
  display:flex; align-items:center; gap:14px; flex-wrap:wrap;
  background:#16202b; border-radius:18px; padding:12px 18px; margin-bottom:26px;
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
   рядом с ней, а не картинка во весь экран: размер обложки задан
   здесь, потому что сама она приходит в натуральную величину. */
.kn-podrobno{padding:12px 0 4px}
.kn-kartochka{display:flex; align-items:flex-start; gap:26px}
.kn-kartochka img{
  flex:0 0 auto; width:180px; height:auto; display:block;
  border-radius:10px;
}
.kn-kartotekst{
  display:flex; flex-direction:column; gap:10px; min-width:0;
  padding-top:4px;
}
.kn-knazv{
  font-size:27px; font-weight:600; color:#f3f5f9; line-height:1.2;
  hyphens:manual; overflow-wrap:break-word;
}
/* На узком экране обложка встаёт над описанием: рядом они не помещаются,
   и обложка выдавливала текст в столбик шириной в пару букв. */
@media (max-width:959px){
  .kn-kartochka{flex-direction:column; gap:14px}
  .kn-kartochka img{width:150px}
}
.kn-kavt{font-size:23px; color:#98a2b3; line-height:1.3}

/* ---- обложка учебника — фон всей плашки ----
   Обложка ложится на плашку целиком (cover), а не полосой сбоку:
   плашка и есть книга. Поверх неё — затемнение по диагонали: сверху
   картинка видна, к нижнему левому углу уходит в тень, где стоит
   название. Надписи с самой обложки мы не читаем — она нужна как
   картинка, поэтому текст наш, поверх затемнения. */
a.plitka.s-kartinkoy{
  /* Рисунок сам тёмный, сюжет вверху справа, поэтому затемнение
     слабое: свет гасим только там, где стоит текст — внизу слева. */
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
  display:flex; align-items:center; gap:26px; margin-bottom:28px;
  min-height:56px;
}
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
   Названия всех собранных плейлистов стоят под видео, каждое
   раскрывается: внутри те же пункты, что и в панели справа, и нажатие
   включает урок точно так же. Плейлист, открытый сейчас в панели,
   подсвечен. Открыт всегда один — иначе страница уезжает на несколько
   экранов. */
.pl-vse{margin-top:26px}
.pl-blok{margin-bottom:6px}
.pl-vse{padding-left:14px}
/* Название плейлиста — простая строка, как название учебника: ни
   подложки, ни жёлтой полосы, ни обводки. Открытый плейлист отличается
   только цветом текста, он ярче остальных. */
summary.pl-imya{
  display:flex; align-items:center; gap:14px; cursor:pointer;
  padding:12px 4px; margin:0; background:none; border:0;
  border-radius:0; color:#8b95a5;
  font-size:27px; list-style:none;
  hyphens:manual; overflow-wrap:break-word;
}
summary.pl-imya::-webkit-details-marker{display:none}
summary.pl-imya::marker{content:''}
summary.pl-imya .pl-nazv{flex:1 1 auto; min-width:0}
/* Рамки на фокусе нет: открытый плейлист и без неё видно (название
   ярче остальных), а жёсткая белая рамка превращала строку в кнопку. */
summary.pl-imya:focus, summary.pl-imya:focus-visible{outline:none}
summary.pl-imya:hover{color:#f3f5f9}
summary.pl-imya .strela svg{width:30px; height:30px}
details.pl-blok[open] > summary.pl-imya .strela{transform:rotate(180deg)}
.pl-blok.aktiven > summary.pl-imya{color:#f3f5f9}
/* Все строки плейлиста — и заголовки глав, и пункты — стоят с отступом
   слева: список вложен в название плейлиста, и по отступу это видно. */
.pl-telo{padding:12px 0 6px 18px}
.panel-telo .pleylist{margin-left:14px}

/* Плейлист — такая же выезжающая панель, как меню, и в тех же
   границах: та же ширина, тот же выезд, тот же крестик. Открывается
   сразу при входе на страницу видеоуроков. Вдвоём они не открываются:
   открыли меню — плейлист закрылся, и наоборот. */
/* Полоса под ручку ширины: сама ручка стоит слева от панели и без
   этого запаса накрывала бы содержимое страницы — на узком окне она
   перекрывала даже кнопки уведомления над кадром. */
body.pleylist-otkryto{padding-right:calc(var(--panel-shirina) + 10px)}

/* На телефонах места на две колонки нет: панель занимает почти весь
   кадр, а страница под ней не сжимается. Иначе на 320 px от страницы
   осталась бы полоска в 40 px. Это единственная ширина, где прежнее
   правило «панель не накрывает экран» невыполнимо: справа остаётся
   полоска 40 px, за которую панель можно закрыть. */
@media (max-width:639px){
  body{--panel-shirina:min(420px, calc(100vw - 40px))}
  body.menu-otkryto, body.pleylist-otkryto{padding-right:0}
}
#pleylist-panel{transform:translateX(100%); visibility:hidden;
  transition:transform .32s ease, visibility 0s linear .32s}
body.pleylist-otkryto #pleylist-panel{transform:none; visibility:visible;
  transition:transform .32s ease, visibility 0s linear 0s}
.pleylist{margin:0; padding:0}
.panel-zag{flex:1 1 auto; font-size:30px; color:#f3f5f9; font-weight:600}

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
   Ни подложки, ни жёлтой полосы слева, ни рамки: это строка списка,
   а не кнопка. Синим не делаем никогда: цвет наш, серый.
   Место под жёлтую чёрточку оставлено у КАЖДОЙ строки (прозрачная
   полоса слева), поэтому играющий пункт встаёт на своё место и список
   от него не сдвигается ни на пиксель. */
a.trek{
  display:flex; align-items:baseline; gap:18px; text-decoration:none;
  color:#c9d2df; background:none;
  border:0; border-left:6px solid transparent; border-radius:12px;
  padding:11px 16px;
  hyphens:manual; overflow-wrap:break-word;
}
/* Наведение и фокус — серая подложка, как в прежнем проекте: строка
   заметно отзывается, но слабее играющей. */
a.trek:hover, a.trek:focus, a.trek:focus-visible{
  background:#1b212b; outline:none; color:#f3f5f9;
}
/* На пульте указателя нет: там «где я» показывает фокус. У него жёлтая
   обводка — как у плашек и кнопок. Мышью обводки не видно.
   Играющий пункт от фокуса отличается: у него жёлтая чёрточка. */
a.trek:focus-visible{outline:3px solid #ffd23f; outline-offset:0}
.trek-nomer{
  flex:0 0 auto; min-width:96px; font-size:28px; color:#8b95a5;
  line-height:1.25;
}
.trek-tema{flex:1 1 auto; min-width:0; font-size:28px; line-height:1.25}
/* ИГРАЮЩИЙ пункт — единственная строка, которая выглядит плашкой:
   серая подложка, жёлтый номер параграфа и жёлтая чёрточка слева
   (полоса 6 px, скругление 12 px — как у строки в панели плейлиста).
   Остальные строки остаются простым текстом. */
a.trek.aktiven{
  background:#232c38; border-left-color:#ffd23f; color:#f3f5f9;
}
a.trek.aktiven .trek-nomer{color:#ffd23f}
/* Заголовок группы («Глава I. Первобытное общество») — подпись к идущим
   за ним пунктам. Он серый, как название учебника: его видно, но он не
   спорит с пунктами и не сбивает с ориентировки. От текста до верхней
   плашки 24 px, до нижней — 20 px. */
.trek-gruppa{
  /* Отступ тот же, что у текста строк: 6 px прозрачной полосы + 16 px
     внутреннего поля. Заголовок главы стоит ровно над темами. */
  font-size:24px; color:#8b95a5; margin:24px 0 20px; padding-left:22px;
  hyphens:manual; overflow-wrap:break-word;
}
.trek-gruppa:first-child{margin-top:0}

/* ---- Строка списка В ПАНЕЛИ ПЛЕЙЛИСТА — прежнее оформление ----
   У панели справа свой вид, и он остаётся: у каждого пункта плашка,
   жёлтый номер параграфа и жёлтая полоса слева. Простой текст — это
   список ПОД КАДРОМ и боковое меню (правило выше), панели оно не
   касается: так и было решено. */
#pleylist-panel a.trek{
  gap:20px;
  background:#1b212b;
  border-left:6px solid #ffd23f;
  border-radius:12px;
  padding:13px 18px;
  margin:0 0 11px;
  color:#f3f5f9;
}
/* Наведение и фокус — плашка чуть светлее, текст белее. Синим не
   подсвечиваем и здесь. */
#pleylist-panel a.trek:hover, #pleylist-panel a.trek:focus,
#pleylist-panel a.trek:focus-visible{
  background:#232c38; outline:none; color:#ffffff;
}
#pleylist-panel a.trek:focus-visible{outline:3px solid #ffd23f}
/* Играющий пункт — плашка светлее остальных. */
#pleylist-panel a.trek.aktiven{background:#232c38}
/* Колонка номера — 100 px, как было: после неё тема начинается на
   одном и том же месте во всех строках, длинный номер колонку
   растягивает («45 мин» шире сотни). */
#pleylist-panel .trek-nomer{
  min-width:100px; font-size:30px; font-weight:700; line-height:1.3;
  color:#ffd23f;
}
#pleylist-panel .trek-tema{font-size:28px; line-height:1.3}
#pleylist-panel .trek-gruppa{padding-left:23px}

/* ---- кнопки-иконки: эталон — Tilda Icons ---- */
.pravo{margin-left:auto; display:flex; align-items:center; gap:14px}
a.tumbler.ikonka{padding:9px 13px; line-height:0}
a.tumbler.ikonka svg{width:36px; height:36px; display:block}

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
  flex:0 0 auto; display:flex; align-items:flex-start; gap:12px;
  padding:22px 22px 16px; background:#141a22;
  border-bottom:2px solid #2a3340;
}
/* Область списка: прокручивается только она. Отступ сверху — воздух
   между разделительной линией и первым пунктом: без него верхняя
   плашка липла к линии вплотную. */
.panel-telo{
  flex:1 1 auto; overflow-y:auto; overscroll-behavior:contain;
  padding:20px 22px 26px;
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
  display:block; background:none;
  border:0; border-left:6px solid transparent; border-radius:12px;
  padding:10px 16px; margin-bottom:2px;
  color:#c9d2df; text-decoration:none; font-size:30px;
  overflow-wrap:break-word;
}
a.panel-plitka:focus, a.panel-plitka:hover, a.panel-plitka:focus-visible{
  background:#1b212b; outline:none; color:#f3f5f9;
}
a.panel-plitka:focus-visible{outline:3px solid #ffd23f; outline-offset:0}
a.panel-plitka.tuskly{font-size:25px; color:#98a2b3}
a.panel-plitka.tekushchiy{
  background:#232c38; border-left-color:#ffd23f; color:#f3f5f9;
}

/* ---- выбор класса: раскрывающийся список в меню ----
   Обычный details/summary: работает и без javascript, на пульте
   открывается по OK. Выглядит как обычный текст: ни подложки, ни
   жёлтой полосы, ни реакции на наведение — это не кнопка-переход,
   а заголовок списка. Что список раскрывается, видно по стрелке. */
.vybor-klassa{flex:1 1 auto; min-width:0}
summary.klass-knopka{
  display:flex; align-items:center; gap:14px; cursor:pointer;
  padding:4px 2px; background:none; border:0; color:#f3f5f9;
  font-size:30px; font-weight:600;
  list-style:none; hyphens:manual; overflow-wrap:break-word;
}
summary.klass-knopka::-webkit-details-marker{display:none}
summary.klass-knopka > span:first-child{flex:1 1 auto; min-width:0}
/* Рамки на фокусе нет: при открытии меню фокус встаёт на название
   класса, и браузер рисовал вокруг него свой прямоугольник — строка
   выглядела плашкой с обводкой. При наведении название чуть ярче. */
summary.klass-knopka:focus, summary.klass-knopka:focus-visible{outline:none}
summary.klass-knopka:hover{color:#f3f5f9}
.strela{flex:0 0 auto; display:flex; color:inherit; transition:transform .15s}
.strela svg{width:34px; height:34px; display:block}
details.vybor-klassa[open] .strela{transform:rotate(180deg)}
.klass-spisok{padding:12px 0 0 16px}
/* Пункты списка классов — тоже просто текст: ни подложки, ни жёлтой
   полосы слева, ни рамки. Отличаются только цветом: текущий класс
   такой же яркий, как название сверху, остальные — приглушённые. */
.klass-spisok a.panel-plitka{
  padding:7px 2px; margin-bottom:2px; font-size:30px; color:#98a2b3;
}
.klass-spisok a.panel-plitka:hover,
.klass-spisok a.panel-plitka:focus,
.klass-spisok a.panel-plitka:focus-visible{background:#1b212b; outline:none;
                                           color:#f3f5f9}


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
   не влезают и тянут страницу вбок. */
@media (max-width:959px){
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
a.knopka{
  display:inline-block; background:#2b3543; color:#f3f5f9; text-decoration:none;
  border:4px solid transparent; border-radius:16px; padding:16px 22px;
  font-size:27px; white-space:nowrap;
}
a.knopka .vremya{color:#ffd23f; font-weight:600}
a.knopka:focus, a.knopka:hover, a.knopka:active{
  outline:none; border-color:#ffd23f; background:#3d4c5f;
}
.stroka.net .tema .chto{color:#7d8695}
/* На узком экране кнопка уступает кадру: длинная надпись переносится
   по словам, а не вылезает за край и не тянет страницу вбок. */
@media (max-width:959px){
  /* overflow-wrap: длинное слово без пробелов (адрес сайта в кнопке)
     иначе вылезает за кнопку и тянет страницу вбок. */
  a.knopka{white-space:normal; max-width:100%; flex:0 1 auto; min-width:0;
           overflow-wrap:break-word}
  .knopki{min-width:0; max-width:100%}
}

.niz{margin-top:44px; color:#6f7887; font-size:22px; line-height:1.5}
/* Планшет вертикальный и уже: та же контрольная точка 960, что
   у Тильды, — новых порогов не заводим (РАЗМЕТКА.md). */
@media (max-width:959px){
  body{font-size:26px; --panel-shirina:min(400px, 64vw)}
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
assert 'СЕТКА-ПЛАШЕК' not in CSS, \
    'в CSS остался неподставленный блок разметки'

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
     Плейлист есть только на страницах видеоуроков. */
  window.shkPanel=function(otkryt){
    var b=document.body;
    if(otkryt){
      b.classList.add('menu-otkryto');
      b.classList.remove('pleylist-otkryto');
      /* Фокус встаёт на первую строку списка — и в меню, и в плейлисте
         одинаково. Крестик закрытия при открытии не подсвечивается
         нигде: раньше в меню фокус шёл на название класса, а в панели
         плейлиста на первый пункт, и крестики выглядели по-разному. */
      var p=document.getElementById('panel');
      var perv=p && p.querySelector('.panel-telo a');
      if(perv) perv.focus();
    } else {
      b.classList.remove('menu-otkryto');
    }
    return false;
  };
  window.shkPleylist=function(otkryt){
    var b=document.body;
    if(otkryt){
      b.classList.add('pleylist-otkryto');
      b.classList.remove('menu-otkryto');
      var p=document.getElementById('pleylist-panel');
      var perv=p && p.querySelector('.panel-telo a');
      if(perv) perv.focus();
    } else {
      b.classList.remove('pleylist-otkryto');
    }
    return false;
  };
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
    }
  });

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

  /* ---- ширина правой панели ----
     Одна и та же у меню и у плейлиста: потянули за кромку — панель
     шире или уже, с пульта то же самое стрелками. Ширина запоминается
     в браузере, как и урок. */
  function panel_min(){ return (window.innerWidth < 640) ? 240 : 300; }
  function panel_max(){
    /* На телефоне панель занимает почти весь кадр: полоска 40 px
       остаётся, чтобы видеть, что закрывать. */
    if(window.innerWidth < 640){
      return Math.max(panel_min(), Math.min(420, window.innerWidth - 40));
    }
    return Math.max(panel_min() + 40,
                    Math.min(900, window.innerWidth - 320));
  }
  function panel_postavit(w){
    w = Math.max(panel_min(), Math.min(w, panel_max()));
    document.body.style.setProperty('--panel-shirina', Math.round(w) + 'px');
    try{ localStorage.setItem('shkola.panel', String(Math.round(w))); }
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


def myagkie(tekst, min_dlina=10):
    """Расставить мягкие дефисы в длинных словах.

    Перенос по слогам — крайний случай: слово короче `min_dlina` остаётся
    целым и переносится на следующую строку целиком («кино и» / «докумен-
    талистика» только там, где «документалистика» не влезла бы и одна).
    """
    if not _SLOGI or not tekst:
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

    `oblozhka` — путь от текущей страницы. Обложка показывается как есть,
    без растягивания: она маленькая, рядом с подписями.
    """
    kart = (f'<img src="{oblozhka}" alt="" loading="lazy">'
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
  function shapka(zag){
    var z=document.getElementById('pleyer-zag');
    if(z && zag){ z.textContent=zag; }
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

  function vklyuchit(kod, zag, nomer, tema, igrat, sekunda){
    tek={kod:kod, zag:zag, nomer:nomer, tema:tema,
         vremya:sekunda||0, dosmotren:false};
    zapis();
    poslT=0;
    kadr(kod, sekunda, igrat!==false);
    shapka(zag);
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
              a.getAttribute('data-tema')||'', true, 0);
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
    /* Фильм или урок? У уроков подпись пункта — «§ 12», у фильмов —
       время («1 ч 20 мин»). По этому и выбираем слова: на странице
       кино не должно быть «Следующий параграф». */
    var kino=!!nomer && nomer.indexOf('§')!==0;
    var sled=sosed(1);
    if(h.dosmotren){
      if(t){ t.textContent=(kino ? '«'+tema+'» посмотрели'
                                 : (nomer ? nomer+' закончен'
                                          : 'Урок закончен')); }
      if(sled){
        knopka('vybor-glavnaya',
               kino ? 'Следующий фильм'
                    : (nomer ? 'Начать '+
                               (sled.getAttribute('data-nomer')||'следующий')
                             : 'Следующий параграф'), sleduyushchiy);
        knopka('vybor-vtoraya',
               kino ? 'Посмотреть снова'
                    : (nomer?'Повторить '+nomer:'Повторить'),
               function(){ vklyuchit(tek.kod, tek.zag, tek.nomer,
                                     tek.tema, true, 0); });
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
             sled ? (kino?'Следующий фильм':'Следующий параграф') : null,
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
    var bl=document.querySelectorAll('.pl-blok');
    for(i=0;i<bl.length;i++){
      var nash=(bl[i].getAttribute('data-nabor')===String(n));
      bl[i].className = nash ? 'pl-blok aktiven' : 'pl-blok';
    }
    var zag=document.getElementById('pl-zag'), imya=imya_nabora(n);
    if(zag && imya){ zag.textContent=imya; }
  }

  /* Раскрытие списка под кадром. Открыт всегда один плейлист: раскрыли
     другой — прежний закрылся, иначе страница уезжает на несколько
     экранов. Кадр не трогаем: человек ещё выбирает, что смотреть, —
     урок включится нажатием на пункт. */
  window.shkRaskryt=function(sm){
    var d=sm.parentNode;
    while(d && d.getAttribute && d.getAttribute('data-nabor')===null){
      d=d.parentNode;
    }
    if(!d || !d.getAttribute){ return true; }
    if(!d.open){
      var vse=document.querySelectorAll('.pl-blok');
      for(var i=0;i<vse.length;i++){
        if(vse[i]!==d && vse[i].open){ vse[i].open=false; }
      }
      otkryt_nabor(d.getAttribute('data-nabor'));
    }
    return true;
  };

  /* Открыть плейлист и поставить его первый урок в кадр на паузу. */
  window.shkNabor=function(n){
    otkryt_nabor(n);
    var pervyi=otkrytyy().querySelector('.trek');
    if(!pervyi){ return false; }
    var kod=pervyi.getAttribute('data-video');
    var zag=pervyi.getAttribute('data-zag')||'';
    tek={kod:kod, zag:zag, nomer:pervyi.getAttribute('data-nomer')||'',
         tema:pervyi.getAttribute('data-tema')||'', vremya:0,
         dosmotren:false};
    zapis(); poslT=0;
    kadr(kod, null, false);
    shapka(zag);
    podsvetit(kod);
    karta(true);
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
      break;
    }
    kadr(h.kod, null, false);   // пауза: видно начало урока, не чёрный экран
    shapka(tek.zag);
    podsvetit(h.kod);
    pokazat_kartu(tek);
  }
  if(document.readyState==='complete'){ snachala(); }
  else { window.addEventListener('load', snachala); }
})();
</script>"""


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


def blok_playera(nabor):
    """Плеер, кнопки вариантов под ним и плейлист — в панели справа.

    `nabor` — [(название, ryady)]: один или несколько вариантов одного
    и того же курса. Варианты бывают, когда по учебнику есть разные
    записи: уроки по параграфам, короткие пересказы, разборы домашних
    заданий, повторение. Под плеером стоят кнопки вариантов — нажали,
    и в панели справа встаёт выбранный плейлист, а в кадре (на паузе)
    его первое видео. Пока вариант один, кнопок нет.

    `ryady` — [(номер, тема, ссылка на видео Rutube)]. Пока страница
    открыта, пункты меняют видео по нажатию, ничего не перезагружая.
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
        poryadok = (sorted(range(len(ryady)), key=klyuch)
                    if nomerov and not grupp else list(range(len(ryady))))

        treki = []
        for i in poryadok:
            nomer, tema, href = ryady[i]
            if not href:
                treki.append(f'<div class="trek-gruppa">{myagkie(tema)}</div>')
                continue
            kod = id_video(href)
            if not kod:
                continue
            nom = (f'<span class="trek-nomer">{nomer}</span>' if nomer else '')
            zag = f'{nomer} {tema}'.strip().replace('"', '').replace("'", '')
            treki.append(f'<a class="trek" href="{href}" data-video="{kod}" '
                         f'data-zag="{myagkie(zag)}" data-nomer="{nomer or ""}" '
                         f'data-tema="{myagkie(tema)}" '
                         f'onclick="return shkIgrat(this)">{nom}'
                         f'<span class="trek-tema">{myagkie(tema)}</span></a>')
        return treki

    spiski = [(imya, spisok(ryady)) for imya, ryady in nabor]
    spiski = [(imya, t) for imya, t in spiski
              if any('class="trek"' in x for x in t)]
    if not spiski:
        return ''
    # Плейлисты под кадром: название, а под ним — тот же список, что
    # и в панели справа. Раскрывается по нажатию, урок включается
    # нажатием на пункт, как и в панели.
    pod_video = ('<div class="pl-vse">' + ''.join(
        f'<details class="pl-blok{" aktiven" if n == 0 else ""}" '
        f'data-nabor="{n}">'
        f'<summary class="pl-imya" onclick="return shkRaskryt(this)">'
        f'<span class="pl-nazv">{myagkie(imya)}</span>'
        f'<span class="strela">{ikona("шеврон")}</span></summary>'
        f'<div class="pl-telo">{"".join(t)}</div></details>'
        for n, (imya, t) in enumerate(spiski)) + '</div>')
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
    vopros = ('Что будем смотреть?' if _podpisi and not _podpisi[0].startswith('§')
              else 'С какого параграфа начнём?')
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
    return (f'<div class="pleyer-wrap">'
            f'<div class="pleyer-shapka">'
            f'<span class="pleyer-zag" id="pleyer-zag">{myagkie(vopros)}</span>'
            f'</div>'
            f'<div class="pleyer-mesto">'
            f'<div class="pleyer" id="pleyer">{knopka_pleylista}</div>'
            f'<div class="pleyer-vybor" id="pleyer-vybor" '
            f'style="display:none">{karta}</div>'
            f'</div>'
            f'{pod_video}</div>{chr(10)}{panel_pleylista}{chr(10)}{JS_PLAYERA}')


def sobrat(zagolovok, podzagolovok, bloki, fayl, put=None,
           podskazka=None, primechanie=None, indeks=False,
           menyu_spisok=None, menyu_zagolovok='',
           kniga=None, klassy=None, telo_klass=''):
    """Собрать страницу пакета и записать её в Проект/.

    `fayl` — путь от корня пакета, например
    «База данных/8 класс/Геометрия/видеоуроки.html».
    `put` — строка пути: [(подпись, путь от корня пакета)], последняя
    без пути. `put=None` означает «это вход».

    `menyu_spisok` — [(подпись, путь от корня пакета)] для бокового меню:
    предметы текущего класса. `klassy` — [(название, путь)] всех классов
    пакета: они уходят в раскрывающийся список в шапке меню, поэтому новый
    класс появляется в меню сам, без правки шаблона.

    `kniga` — готовая строка учебника (её собирает kniga_stroka). Одна
    и та же на странице предмета и на всех страницах его материалов.

    `telo_klass` — класс для тега body: на видеоуроках это
    «pleylist-otkryto», то есть плейлист стоит открытым сразу, а значок
    меню переключает меню и плейлист в одной и той же панели.
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

    # Меню: сверху раскрывающийся список классов со стрелкой-маркером,
    # ниже — предметы текущего класса. Надписи «Меню» нет: это и так
    # меню, а на её месте должен стоять текущий класс — он и есть
    # раскрывающийся список. «Выбор класса» отдельным пунктом не нужно
    # (он в списке), «Открепить» — тоже: домашнюю страницу меняет
    # скрепка в шапке.
    zagolovok_klassa = menyu_zagolovok or 'Выберите класс'
    otkryto = ' open' if put is None else ''
    klassy_html = ''
    for tekst, kuda in (klassy or []):
        cls = ('panel-plitka tekushchiy' if tekst == menyu_zagolovok
               else 'panel-plitka')
        klassy_html += (f'<a class="{cls}" '
                        f'href="{otnositelno(fayl, kuda)}">'
                        f'{myagkie(tekst)}</a>')
    spisok_klassov = ''
    if klassy_html:
        spisok_klassov = (
            f'<details class="vybor-klassa"{otkryto}>'
            f'<summary class="klass-knopka">'
            f'<span>{myagkie(zagolovok_klassa)}</span>'
            f'<span class="strela">{ikona("шеврон")}</span></summary>'
            f'<div class="klass-spisok">{klassy_html}</div></details>')

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
             f'<div class="panel-verh">{spisok_klassov}'
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
                .replace('{panel}', panel)
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

    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{zagolovok}</title>
<style>{CSS}</style>
</head>
<body{telo}>
<div class="wrap">
{verh}
{shapka}
{chr(10).join(bloki)}
{niz}
</div>
{js}
</body>
</html>
"""
    html = perevesti_puti(html, fayl)
    polny = os.path.join(PAKET, *fayl.split('/'))
    os.makedirs(os.path.dirname(polny), exist_ok=True)
    with open(polny, 'w', encoding='utf-8') as f:
        f.write(html)
    return polny, len(html)
