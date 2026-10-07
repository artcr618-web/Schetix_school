# -*- coding: utf-8 -*-
"""Проверка всех ссылок во всех страницах.

    python3 Инструменты/proverka_ssylok.py

Проверяет и внешние ссылки (по http), и внутренние — то есть что файл,
на который страница ссылается, правда лежит рядом. Внутренние ссылки
ломаются тише всего: переименовал папку — и половина страниц ведёт в никуда.

Лог пишется в Временные/proverka_ssylok.log.

Не всякий не-200 — это битая ссылка. Разделяем:

  200              — всё хорошо
  202, 403         — проверка «ты не робот». В браузере живая,
                     просто curl не пустили. (Baamboozle, Британский музей)
  401              — нужна авторизация. Ссылка рабочая для залогиненного
                     человека. (Инфурок)
  307, 301         — редирект, который curl не смог довести до конца.
                     В браузере открывается. (ЯКласс)
  000              — достучаться не удалось ВООБЩЕ: обрыв сети, или нас
                     не пускают по географии. Это НЕ значит, что ссылка
                     мертвая — это значит, что мы не узнали. Такие идут
                     в отдельную группу «проверить вручную».

  остальное (404, 410, 5xx) — вот это уже по-настоящему битая.

Сайты не любят, когда к ним бьются очередью: с одного адреса уходит по
нескольку десятков запросов подряд (у «Контрользнаний» их больше шести-
десяти), и сервер начинает отвечать 500, а потом и вовсе перестаёт
пускать. Поэтому:

  * к одному сайту запросы идут с паузой (не чаще одного в 0.7 с);
  * ответ 5xx или 000 переспрашивается — до трёх раз с растущей паузой.
    Живая ссылка на повторе отвечает 200, битая так и остаётся битой
    (404 повторять нечего — это уже ответ).
"""
import concurrent.futures as futures
import io, os, re, subprocess, sys, threading, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _пути import VSE_STRANICY, LOG_SSYLKI, VREM

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/126.0 Safari/537.36')
HOROSHO = {'200'}
SOFT = {'202', '403', '401', '307', '301'}
NEIZVESTNO = {'000'}


def collect():
    """Собирает (страница, ссылка) по всем страницам."""
    out = []
    for page in VSE_STRANICY:
        if not os.path.exists(page):
            continue
        base = os.path.dirname(page)
        s = io.open(page, encoding='utf-8').read()
        for m in re.finditer(r'href="([^"#][^"]*)"', s):
            href = m.group(1)
            if href.startswith(('http://', 'https://')):
                out.append((page, href, href))
            elif href.startswith(('mailto:', 'javascript:')):
                continue
            else:
                # ?menu=1 и #menu — метки для javascript, а не часть пути:
                # файл от этого не меняется.
                put = href.split('?')[0].split('#')[0]
                out.append((page, href,
                            os.path.normpath(os.path.join(base, put))))
    return out


def _odin_zapros(url):
    r = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}',
                        '-L', '--max-time', '20', '--connect-timeout', '8',
                        '-A', UA, url],
                       capture_output=True, text=True)
    return r.stdout.strip()


# Пауза между запросами к одному сайту. Потоки общие, поэтому очередь
# на сайт общая: кто пришёл, тот и ждёт, пока пройдёт пауза.
PAUZA_MEZHDU = 0.7          # секунд между запросами к одному сайту
_zamok = threading.Lock()
_kogda = {}


def _podozhdat(url):
    from urllib.parse import urlparse
    host = urlparse(url).netloc
    while True:
        with _zamok:
            teper = time.monotonic()
            kogda = _kogda.get(host, 0)
            if teper - kogda >= PAUZA_MEZHDU:
                _kogda[host] = teper
                return
            zhdat = PAUZA_MEZHDU - (teper - kogda)
        time.sleep(min(zhdat, 0.2))


def check_url(url):
    """Код ответа. 5xx и «не дозвонились» переспрашиваем."""
    pauzy = [0, 2, 6]
    kod = '000'
    for nomer, pauza in enumerate(pauzy):
        if pauza:
            time.sleep(pauza)
        _podozhdat(url)
        kod = _odin_zapros(url)
        if kod == '200' or (kod.isdigit() and kod < '500' and kod != '000'):
            return kod
    return kod


def main():
    pairs = collect()
    seen, bad, soft, neizv = {}, [], [], []

    # Внутренние ссылки проверяем сразу: файл либо есть, либо нет.
    vneshnie = []
    povtory = set()
    for page, href, target in pairs:
        if target in seen:
            continue
        if target.startswith('http'):
            # Один и тот же адрес стоит на многих страницах (учебники,
            # тренажёры): спрашиваем сайт один раз, а не двадцать. Это и
            # вежливее к сайту, и вчетверо быстрее: без этого адресов
            # набиралось 3912 вместо 1727.
            if target not in povtory:
                povtory.add(target)
                vneshnie.append((page, href, target))
        else:
            ok = os.path.exists(target)
            seen[target] = 'есть' if ok else 'НЕТ ФАЙЛА'
            if not ok:
                bad.append((page, href, 'нет файла'))

    # Внешние — в 12 потоков: по одной ссылке на круг это заняло бы час.
    # Ход проверки виден: раз в 200 ссылок печатаем, сколько пройдено.
    sdelano = [0]

    def s_progressom(t):
        kod = check_url(t[2])
        with _zamok:
            sdelano[0] += 1
            if sdelano[0] % 200 == 0:
                print(f'  проверено {sdelano[0]} из {len(vneshnie)}', flush=True)
        return kod

    with futures.ThreadPoolExecutor(max_workers=12) as pool:
        for (page, href, target), code in zip(
                vneshnie, pool.map(s_progressom, vneshnie)):
            seen[target] = code
            povtorov = len(pairs) - len(seen)
            if code in HOROSHO:
                pass
            elif code in SOFT:
                soft.append((page, href, code))
            elif code in NEIZVESTNO:
                neizv.append((page, href, code))
            else:
                bad.append((page, href, code))

    os.makedirs(VREM, exist_ok=True)
    with io.open(LOG_SSYLKI, 'w', encoding='utf-8') as f:
        f.write('Проверка ссылок\n')
        f.write('200 — хорошо; 202/403/401/307 — живая, но не для curl; '
                '000 — проверить не удалось\n')
        f.write('=' * 70 + '\n')
        for t, c in sorted(seen.items()):
            f.write(f'{c:<12} {t}\n')

    print(f'Проверено ссылок: {len(seen)} (уникальных адресов)')
    print(f'  рабочих:        {sum(1 for c in seen.values() if c in HOROSHO)}')
    print(f'  битых:          {len(bad)}')
    if soft:
        print(f'  с оговоркой:    {len(soft)} (в браузере живые)')
        for page, href, code in soft:
            print(f'      {code}  {href}')
    if neizv:
        print(f'  не удалось проверить: {len(neizv)} (сеть или география, не значит битая)')
        for page, href, code in neizv:
            print(f'      000  {href}')
    if bad:
        print('\nБИТЫЕ:')
        for page, href, code in bad:
            print(f'  {code}  {href}   <- {os.path.basename(page)}')
    print(f'\nЛог: {LOG_SSYLKI}')
    if bad:
        print(f'\nСсылки: вердикт — плохо, битых {len(bad)}')
    else:
        print(f'\nСсылки: вердикт — хорошо: рабочих {sum(1 for c in seen.values() if c in HOROSHO)}'
              f'{", с оговоркой " + str(len(soft)) if soft else ""}'
              f'{", переспросить " + str(len(neizv)) if neizv else ""}. '
              'Битых нет.')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
