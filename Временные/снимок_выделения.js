// Снимки нового выделения строк: панель плейлиста (обычная строка,
// наведение, играющая) и панель меню. Крупные кропы — чтобы глазами
// сверить рамку, флажок и выравнивание.
//
// Запуск: bash Инструменты/с_плейрайтом.sh node Временные/снимок_выделения.js [метка]
// Метка пустая — снимаем «после»; метла «-до» — «до» (скрипт запускают
// из копии со старым css, см. коллаж_выделения.py).
const { chromium } = require('./плейрайт.js');
const path = require('path');

const metka = process.argv[2] || '';
const kuda = path.join(__dirname, 'снимки');

(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1600, height: 1000 } });

  // --- панель плейлиста: играющий § 2, курсор на § 5 (через главу)
  await p.goto('file://' + path.resolve(
    'Проект/База данных/HTML/5 класс/История/видеоуроки.html'),
    { waitUntil: 'domcontentloaded' });
  await p.evaluate(() => {
    const sp = document.querySelector('#pleylist-panel .pleylist.aktiven')
            || document.querySelector('#pleylist-panel .pleylist');
    const vse = sp.querySelectorAll('a.trek');
    if (vse[2]) vse[2].onclick();       // играет § 2
  });
  await p.waitForTimeout(700);

  // Рамка активного видна, курсор наведём на § 3 (следующий) — он под
  // курсором и должен показать рамку без флажка.
  const kursor = await p.evaluate(() => {
    const sp = document.querySelector('#pleylist-panel .pleylist.aktiven');
    const vse = sp.querySelectorAll('a.trek');
    const a = vse[3];                    // § 3
    a.scrollIntoView({ block: 'center' });
    const r = a.getBoundingClientRect();
    return { x: Math.round(r.left + r.width / 2), y: Math.round(r.top + r.height / 2) };
  });
  await p.mouse.move(kursor.x, kursor.y);
  await p.waitForTimeout(400);
  const panel = await p.$('#pleylist-panel .panel-telo');
  await panel.screenshot({ path: path.join(kuda, 'выделение-плейлист' + metka + '.png') });
  console.log('снимок: выделение-плейлист.png');

  // --- панель меню: текущий пункт + курсор на другом
  await p.goto('file://' + path.resolve('Проект/База данных/HTML/7 класс/История.html'),
               { waitUntil: 'domcontentloaded' });
  await p.evaluate(() => { window.shkPanel(true); document.activeElement.blur(); });
  await p.waitForTimeout(700);
  const kursor2 = await p.evaluate(() => {
    const a = [...document.querySelectorAll('#panel .panel-telo a.panel-plitka')]
      .find(x => !x.className.includes('tekushchiy'));
    if (!a) return null;
    const r = a.getBoundingClientRect();
    return { x: Math.round(r.left + r.width / 2), y: Math.round(r.top + r.height / 2) };
  });
  if (kursor2) { await p.mouse.move(kursor2.x, kursor2.y); await p.waitForTimeout(400); }
  const panel2 = await p.$('#panel .panel-telo');
  await panel2.screenshot({ path: path.join(kuda, 'выделение-меню' + metka + '.png') });
  console.log('снимок: выделение-меню.png');

  // --- список плейлистов под кадром: руслан
  await p.goto('file://' + path.resolve(
    'Проект/База данных/HTML/5 класс/История/видеоуроки.html'),
    { waitUntil: 'domcontentloaded' });
  await p.evaluate(() => { document.activeElement && document.activeElement.blur(); });
  const kursor3 = await p.evaluate(() => {
    const a = document.querySelector('.pl-vse a.pl-plitka:not(.tekushchiy)');
    if (!a) return null;
    a.scrollIntoView({ block: 'center' });
    const r = a.getBoundingClientRect();
    return { x: Math.round(r.left + r.width / 2), y: Math.round(r.top + r.height / 2) };
  });
  if (kursor3) { await p.mouse.move(kursor3.x, kursor3.y); await p.waitForTimeout(400); }
  const pl = await p.$('.pl-vse');
  await pl.screenshot({ path: path.join(kuda, 'выделение-под-кадром' + metka + '.png') });
  console.log('снимок: выделение-под-кадром.png');

  await b.close();
})();
