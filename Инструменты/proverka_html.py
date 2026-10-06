# -*- coding: utf-8 -*-
"""Проверка вёрстки всех страниц перед тем, как показывать их человеку.

    python3 Инструменты/proverka_html.py

Что ловит:
  1. Незакрытые и перепутанные теги — самая частая беда. Страницы
     собираются скриптом из кусков текста, и один лишний </div>
     ломает сразу несколько блоков, причём заметно это не сразу.
  2. Буквы чужих алфавитов. Один раз в русский текст пролез китайский
     иероглиф — больше не хочется. При этом эмодзи и типографские
     символы (тире, кавычки, многоточие) разрешены: они нужны.
  3. Отсутствие заголовка и кодировки.

Возвращает код 1, если что-то не так (удобно втыкать в цепочку).
"""
import io, os, re, sys, unicodedata
from html.parser import HTMLParser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _пути import VSE_STRANICY

VOID = {'br', 'hr', 'img', 'meta', 'link', 'input'}


class Proverka(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack, self.err = [], []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append((tag, self.getpos()))

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack:
            self.err.append(f'лишний </{tag}> в строке {self.getpos()[0]}')
            return
        if self.stack[-1][0] != tag:
            self.err.append(f'</{tag}> в строке {self.getpos()[0]}, '
                            f'а открыт был <{self.stack[-1][0]}> '
                            f'в строке {self.stack[-1][1][0]}')
            for i in range(len(self.stack) - 1, -1, -1):
                if self.stack[i][0] == tag:
                    del self.stack[i:]
                    return
        else:
            self.stack.pop()


def main():
    problems = 0
    for path in VSE_STRANICY:
        name = os.path.relpath(path, os.path.dirname(os.path.dirname(path)))
        if not os.path.exists(path):
            print(f'НЕТ ФАЙЛА  {name}')
            problems += 1
            continue
        s = io.open(path, encoding='utf-8').read()

        p = Proverka()
        p.feed(s)

        # Чужие БУКВЫ. Именно буквы: emoji, тире, кавычки и многоточие —
        # это символы (категория S/P/M), они нужны и тревогу не поднимают.
        # А вот «只会» — это Lo, буква, и её мы поймаем.
        wrong = sorted({c for c in s
                        if unicodedata.category(c).startswith('L')
                        and ord(c) > 0x024F
                        and not (0x0370 <= ord(c) <= 0x03FF)   # греческий
                        and not (0x0400 <= ord(c) <= 0x04FF)}) # кириллица

        notes = []
        if p.stack:
            notes.append('незакрыто: ' + ', '.join(t for t, _ in p.stack))
        if p.err:
            notes.append('ошибки: ' + '; '.join(p.err[:3]))
        if wrong:
            notes.append('чужие символы: ' + ' '.join(
                f'{c!r}(U+{ord(c):04X})' for c in wrong))
        if '<title>' not in s:
            notes.append('нет <title>')
        if 'charset="utf-8"' not in s.lower():
            notes.append('нет кодировки utf-8')

        # Класс, для которого в <style> нет ни одного правила, — это
        # почти всегда потерянное оформление: разметка на месте, а
        # выглядит она как голый текст браузера. Один раз так пропала
        # вся карточка учебника: обложка растянулась во весь экран,
        # а у названия нарисовался браузерный треугольник.
        stil = re.search(r'<style>(.*?)</style>', s, re.S)
        if stil and '<body' in s:
            telo = s[s.index('<body'):]
            bez_pravil = sorted({k for m in re.finditer(r'class="([^"]+)"', telo)
                                 for k in m.group(1).split()
                                 if ('.' + k) not in stil.group(1)})
            if bez_pravil:
                notes.append('классы без правил в оформлении: '
                             + ', '.join(bez_pravil))

        # У раскрывающихся строк (класс в меню, учебник под путём)
        # браузер рисует свой треугольник слева от названия. Он не
        # нужен: подсказка одна — наша стрелка, в одну строку с
        # названием и без ничего перед ним.
        if ('class="kniga-stroka"' in s or 'class="vybor-klassa"' in s) and (
                'list-style:none' not in s
                or '::-webkit-details-marker' not in s):
            notes.append('у раскрывающейся строки не убран браузерный '
                         'треугольник (нужны list-style:none и '
                         '::-webkit-details-marker)')

        links = len(re.findall(r'href="http', s))
        if notes:
            problems += 1
            print(f'ПЛОХО      {name}')
            for n in notes:
                print(f'             — {n}')
        else:
            print(f'OK         {name}  ({len(s):>7} символов, {links:>3} ссылок)')

    print()
    if problems:
        print(f'Проблемных файлов: {problems}. Страницы не трогаем, пока не починим.')
        return 1
    print(f'Все {len(VSE_STRANICY)} страниц чистые.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
