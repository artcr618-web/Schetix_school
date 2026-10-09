// Сравнение сетки: слева прежнее оформление (восстановлено поверх страницы),
// справа нынешнее. Снимки складываются в отдельные файлы, а коллаж
// собирает python.
// Запуск: node Временные/sravnenie_setki.js
const { chromium } = require('./плейрайт.js');
const path = require('path');

// Прежние правила сетки — как было до правки.
const BYLO = `
.setka{display:grid; grid-template-columns:repeat(auto-fit, minmax(320px, 520px));
       justify-content:start; gap:24px; margin-top:26px; --polosa:18px; --radius:22px}
.setka.klassy{grid-template-columns:repeat(auto-fit, minmax(380px, 1fr))}
@media (max-width:1100px){
  .setka{grid-template-columns:repeat(auto-fit, minmax(240px, 380px));
         gap:18px; --polosa:13px; --radius:14px}
  a.plitka{min-height:120px}
  a.plitka .nazv{font-size:28px}
  a.plitka .poyas{font-size:17px}
}
h1{overflow-wrap:normal}
a.knopka{white-space:nowrap; max-width:none; overflow-wrap:normal}
`;

const kadry = [
  ['предметы-1440', 'Проект/База данных/HTML/5 класс.html', 1440, false],
  ['предметы-1100', 'Проект/База данных/HTML/5 класс.html', 1100, false],
  ['классы-940',    'Проект/Начать учиться.html',       940, true],
  ['предметы-640',  'Проект/База данных/HTML/5 класс.html',  640, false],
];

(async () => {
  const b = await chromium.launch();
  for (const [imya, f, w, klassy] of kadry) {
    for (const kak of ['было', 'стало']) {
      const p = await b.newPage({ viewport: { width: w, height: 1000 } });
      await p.goto('file://' + path.resolve(f), { waitUntil: 'load' });
      await p.waitForTimeout(250);
      if (kak === 'было') {
        await p.addStyleTag({ content: BYLO });
        if (klassy) await p.evaluate(() =>
          document.querySelector('.setka').classList.add('klassy'));
      }
      await p.waitForTimeout(200);
      const vysota = await p.evaluate(() => {
        const pl = document.querySelector('.setka');
        return Math.min(Math.ceil(pl.getBoundingClientRect().bottom) + 30, 2100);
      });
      await p.setViewportSize({ width: w, height: vysota });
      await p.waitForTimeout(200);
      await p.screenshot({ path: `Временные/снимки/сетка-${kak}-${imya}.png` });
      await p.close();
    }
    console.log('снято: ' + imya);
  }
  await b.close();
})();
