# -*- coding: utf-8 -*-
"""Живой предпросмотр «Проекта» — точь-в-точь как на флешке.

Поднимает локальный сервер над папкой «Проект»: на корне открывается
главная страница, а не список файлов. Нужен, чтобы смотреть страницы
в браузере с настоящими стилями и рабочими кнопками: просмотрщик
файлов показывает один файл и к соседним не ходит (см. §5 правил).

    python3 Временные/предпросмотр.py [порт]

Ничего в проекте не меняет: только читает файлы и отвечает в браузер.
"""
import http.server
import os
import sys
import urllib.parse

KOREN = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     'Проект')
VHOD = 'Начать учиться.html'


class Otvet(http.server.SimpleHTTPRequestHandler):
    """Отдаёт файлы «Проекта»; на корне — переход на главную страницу."""

    def __init__(self, *a, **k):
        super().__init__(*a, directory=KOREN, **k)

    def do_GET(self):
        if self.path in ('/', ''):
            self.send_response(302)
            self.send_header('Location', '/' + urllib.parse.quote(VHOD))
            self.end_headers()
            return
        super().do_GET()


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    srv = http.server.ThreadingHTTPServer(('0.0.0.0', port), Otvet)
    print('«Проект» открыт на порту %d — сразу главная страница' % port,
          flush=True)
    srv.serve_forever()
