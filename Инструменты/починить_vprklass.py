# -*- coding: utf-8 -*-
"""Чинит ссылки на ВПР с сайта vprklass.ru.

    python3 Инструменты/починить_vprklass.py

Обнаружилось 5 октября 2026: часть ссылок на странице 7 класса имела
продублированный сегмент пути, из-за чего отдавала 404:

    /a/vpr2025-7kl-is-var2025-7kl-is-var1-1.pdf     <- так было (404)
    /a/vpr2025-7kl-is-var1-1.pdf                    <- так надо (200)

Сайт периодически переезжает по папкам: 2025 год лежит в /a/,
2023—2024 — в /vpr/, 2026 — в /vpr6/. Поэтому скрипт не угадывает путь,
а берёт каждую найденную ссылку, чинит её и тут же проверяет по http.
Не проверилось — не записываем. Дырки в файле лучше, чем мёртвая ссылка:
дырку видно сразу.

--proverit  — только показать отчёт, файлы не трогать.
"""
import io, os, re, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _пути import VSE_STRANICY, VREM

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/126.0 Safari/537.36')

# Продублированный сегмент: «...is-var» + «2025-7kl-is-var»
LOMANY = re.compile(r'(vpr\d{4}-\d+kl-is-var)\d{4}-\d+kl-is-var')

OTCHET = os.path.join(VREM, 'pochinka_vprklass.log')


def status(url):
    r = subprocess.run(['curl', '-s', '-o', '/dev/null',
                        '-w', '%{http_code} %{content_type}',
                        '-L', '--max-time', '25', '-A', UA, url],
                       capture_output=True, text=True)
    return r.stdout.strip()


def main():
    only_check = '--proverit' in sys.argv
    log, total = [], 0

    for path in VSE_STRANICY:
        if not os.path.exists(path):
            continue
        s = io.open(path, encoding='utf-8').read()
        found = LOMANY.findall(s)
        if not found:
            continue

        fixed, failed = {}, []
        for m in LOMANY.finditer(s):
            old = m.group(0)
            new = m.group(1)
            if old in fixed:
                continue
            # строим новый URL целиком
            probe = s[s.rfind('"', 0, m.start()) + 1: s.find('"', m.end())]
            new_url = probe.replace(old, new)
            st = status(new_url)
            if st.startswith('200') and 'pdf' in st:
                fixed[old] = new
                log.append(f'OK    {st:<28} {new_url}')
            else:
                failed.append(new_url)
                log.append(f'ПЛОХО {st:<28} {new_url}')
            total += 1

        print(f'{os.path.basename(path)}: найдено {len(found)}, '
              f'починено {len(fixed)}, не подтвердилось {len(failed)}')
        if failed:
            print('    ! эти не трогаем, надо разбираться вручную:')
            for u in failed:
                print(f'      {u}')

        if not only_check and fixed:
            for old, new in fixed.items():
                s = s.replace(old, new)
            io.open(path, 'w', encoding='utf-8').write(s)
            print(f'    записано: {path}')

    os.makedirs(VREM, exist_ok=True)
    io.open(OTCHET, 'w', encoding='utf-8').write('\n'.join(log) + '\n')
    print(f'\nПроверено ссылок: {total}. Лог: {OTCHET}')
    if only_check:
        print('Режим --proverit: файлы не изменялись.')


if __name__ == '__main__':
    main()
