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
"""
import concurrent.futures as futures
import io, os, re, subprocess, sys

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


def check_url(url):
    r = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}',
                        '-L', '--max-time', '30', '-A', UA, url],
                       capture_output=True, text=True)
    return r.stdout.strip()


def main():
    pairs = collect()
    seen, bad, soft, neizv = {}, [], [], []

    # Внутренние ссылки проверяем сразу: файл либо есть, либо нет.
    vneshnie = []
    for page, href, target in pairs:
        if target in seen:
            continue
        if target.startswith('http'):
            vneshnie.append((page, href, target))
        else:
            ok = os.path.exists(target)
            seen[target] = 'есть' if ok else 'НЕТ ФАЙЛА'
            if not ok:
                bad.append((page, href, 'нет файла'))

    # Внешние — в 12 потоков: по одной ссылке на круг это заняло бы час.
    with futures.ThreadPoolExecutor(max_workers=12) as pool:
        for (page, href, target), code in zip(
                vneshnie, pool.map(lambda t: check_url(t[2]), vneshnie)):
            seen[target] = code
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

    print(f'Проверено ссылок: {len(seen)}')
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
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
