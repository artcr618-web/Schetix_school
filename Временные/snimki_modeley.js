// Снимки для сравнения и для таблицы моделей экрана.
// Запуск: bash Инструменты/с_плейрайтом.sh node Временные/snimki_modeley.js
const { chromium } = require('/home/user/Временные/плейрайт.js');
const path = require('path');

// Как было до этой правки: одна колонка уже с 960.
const BYLO = `
@container (min-width: 560px){ .pleyer-vybor{position:absolute; inset:0; z-index:5; margin-top:0} }
@media (max-width:959px){
  .setka{grid-template-columns:minmax(0, 1fr); gap:16px; --polosa:13px; --radius:14px}
  a.plitka{aspect-ratio:16 / 9}
  a.plitka .nazv{font-size:32px}
  a.plitka .poyas{font-size:17px}
  a.plitka.klass .nazv .chislo{font-size:clamp(110px, 30vw, 186px)}
}
@media (max-width:639px){
  body{--panel-shirina:420px}
  body.menu-otkryto, body.pleylist-otkryto{padding-right:calc(var(--panel-shirina) + 10px)}
}
.wrap{padding:22px 44px}
`;

const kadry = [
  ['предметы-768', 'Проект/База данных/5 класс.html', 768, true],
  ['предметы-640', 'Проект/База данных/5 класс.html', 640, true],
  ['предметы-360', 'Проект/База данных/5 класс.html', 360, true],
  ['предметы-320', 'Проект/База данных/5 класс.html', 320, true],
];

(async () => {
  const b = await chromium.launch();
  for (const [imya, f, w, sravnit] of kadry) {
    for (const kak of ['было', 'стало']) {
      const p = await b.newPage({ viewport: { width: w, height: 1000 } });
      await p.goto('file://' + path.resolve(f), { waitUntil: 'load' });
      await p.waitForTimeout(220);
      if (kak === 'было') { await p.addStyleTag({ content: BYLO }); await p.waitForTimeout(180); }
      const vysota = await p.evaluate(() => Math.min(
        Math.ceil(document.querySelector('.setka').getBoundingClientRect().bottom) + 24, 2200));
      await p.setViewportSize({ width: w, height: vysota });
      await p.waitForTimeout(180);
      await p.screenshot({ path: `Временные/снимки/разметка-${kak}-${imya}.png` });
      await p.close();
    }
    console.log('снято: ' + imya);
  }
  await b.close();
})();
