# -*- coding: utf-8 -*-
"""Собирает список «Что не нашлось» — записи, которые свободные источники
не отдают нашему кадру.

Материал, который не находится на Rutube и в ВК Видео, но нужен странице,
не оставляет дырки в проекте: он попадает в этот список. Полина снимает
такую запись себе на канал и присылает ссылку — ссылка встаёт и в список,
и в нужное место на странице. Заполнять список руками не нужно: он
собирается вот отсюда.

    python3 Инструменты/gen_spisok.py

Данные: Временные/naiti.json
Страница: Документация/Что не нашлось.html

У каждой записи такие поля:

    название   — как запись называется
    кто        — автор, канал, год выпуска
    время      — длительность
    источник   — прямая ссылка на свободный источник (для сверки)
    куда       — куда она встанет в проекте
    состояние  — что именно не так («закрыт по регионам», «кадра нет»)
    запись     — ссылка на собственную запись Полины; пусто, пока её нет
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _пути import ROOT, VREM  # noqa: E402
import _tv  # noqa: E402

DANNYE = os.path.join(VREM, 'naiti.json')
STRANICA = os.path.join(ROOT, 'Документация', 'Что не нашлось.html')

# Оформление списка — отдельным файлом, как и у страниц пакета: в html
# остаётся только разметка. Файл лежит рядом со страницей — в
# «Документации» (см. §4 правил).
CSS_FAYL = 'оформление-списка.css'
CSS_POLNY = os.path.join(ROOT, 'Документация', CSS_FAYL)

CSS = """
:root{
  --fon:#0e1116; --kart:#1b212b; --ramka:#ffd23f;
  --tekst:#f3f5f9; --tuskly:#98a2b3;
}
*{box-sizing:border-box}
body{
  margin:0; background:var(--fon); color:var(--tekst);
  font-family:system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;
  font-size:20px; line-height:1.45; padding:0 0 90px;
}
.listok{max-width:1100px; margin:0 auto; padding:0 28px}
h1{font-size:44px; line-height:1.2; font-weight:600; margin:64px 0 10px}
.podzag{font-size:24px; color:var(--tuskly); margin:0 0 22px}
.poyasnenie{color:#c9d2df; max-width:78ch; margin:0 0 8px}
.gruppa{margin-top:54px}
h2{
  font-size:22px; font-weight:600; color:var(--tuskly);
  letter-spacing:.02em; text-transform:none; margin:0 0 18px;
  padding-bottom:12px; border-bottom:1px solid #232c38;
}
.stroka{
  background:var(--kart); border-radius:16px;
  padding:22px 24px 20px; margin-bottom:14px;
}
.nazv{
  display:inline-block; font-size:25px; font-weight:600; line-height:1.25;
  color:var(--tekst); text-decoration:none;
}
.nazv:hover, .nazv:focus{color:var(--ramka)}
.meta{color:var(--tuskly); font-size:18px; margin-top:6px}
.kuda{color:#c9d2df; margin:12px 0 0; max-width:80ch}
.sost{color:#e3b04b; margin:10px 0 0; font-size:18px}
.zapis{color:var(--tuskly); margin:10px 0 0; font-size:18px}
.zapis.est{color:#8fd18f}
.podval{
  margin-top:64px; padding-top:24px; border-top:1px solid #232c38;
  color:var(--tuskly); font-size:18px; max-width:80ch;
}
.podval a{color:#c9d2df}
@media (max-width:700px){
  .listok{padding:0 18px}
  h1{font-size:32px; margin-top:40px}
  .podzag{font-size:20px}
  body{font-size:18px}
  .nazv{font-size:21px}
}
@media print{
  body{background:#fff; color:#111; padding:0}
  .nazv{color:#111}
  .stroka{background:#fff; border:1px solid #ccc}
  .poyasnenie, .kuda{color:#222}
  .sost{color:#7a5200}
  .meta, .zapis, .podval, h2{color:#444}
}
"""


def stroka_html(s):
    """Одна запись списка."""
    zapis = s.get('запись', '').strip()
    if zapis:
        hvost = (f'<p class="zapis est">Твоя запись: '
                 f'<a href="{zapis}">{zapis}</a></p>')
    else:
        hvost = '<p class="zapis">Твоя запись: пока нет</p>'
    return (f'    <article class="stroka">\n'
            f'      <a class="nazv" href="{s["источник"]}">'
            f'{_tv.myagkie(s["название"])}</a>\n'
            f'      <div class="meta">{_tv.myagkie(s.get("кто", ""))}'
            f' · {s.get("время", "")}</div>\n'
            f'      <p class="kuda">{_tv.myagkie(s.get("куда", ""))}</p>\n'
            f'      <p class="sost">{s.get("состояние", "")}</p>\n'
            f'      {hvost}\n'
            f'    </article>')


def zapisat_css():
    """Записать оформление списка отдельным файлом."""
    os.makedirs(os.path.dirname(CSS_POLNY), exist_ok=True)
    with open(CSS_POLNY, 'w', encoding='utf-8') as f:
        f.write(CSS)
    return CSS_FAYL


def sobrat(d):
    gruppy = []
    for g in d['группы']:
        stroki = '\n'.join(stroka_html(s) for s in g['строки'])
        gruppy.append(f'  <section class="gruppa">\n'
                      f'    <h2>{g["имя"]}</h2>\n'
                      f'{stroki}\n'
                      f'  </section>')
    telo = '\n'.join(gruppy)
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{d['заголовок']}</title>
<link rel="stylesheet" href="{CSS_FAYL}">
</head>
<body>
<main class="listok">
  <h1>{d['заголовок']}</h1>
  <p class="podzag">{d['подзаголовок']}</p>
  <p class="poyasnenie">{_tv.myagkie(d['пояснение'])}</p>
{telo}
  <p class="podval">Снять запись можно так: скачать ролик, загрузить его на свой
  канал и прислать ссылку — она встанет и сюда, и на нужную страницу
  («{d['проверено']}» — день проверки).</p>
</main>
</body>
</html>
"""


def main():
    with open(DANNYE, encoding='utf-8') as f:
        d = json.load(f)
    if 'подзаголовок' not in d and 'podzagolovok' in d:   # следы правки
        d['подзаголовок'] = d.pop('podzagolovok')
    print('оформление:', zapisat_css())
    html = _tv.tire_html(sobrat(d))   # правило тире: см. _tv.tire
    os.makedirs(os.path.dirname(STRANICA), exist_ok=True)
    with open(STRANICA, 'w', encoding='utf-8') as f:
        f.write(html)
    vsego = sum(len(g['строки']) for g in d['группы'])
    print(f'Собрано: {STRANICA}')
    print(f'  групп: {len(d["группы"])}, записей: {vsego}')


if __name__ == '__main__':
    main()
