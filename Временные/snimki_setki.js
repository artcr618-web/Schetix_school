// Снимки сетки на четырёх ширинах: десктоп (три в ряд), узкий экран (две),
// сразу за порогом (одна) и горизонтальный мобильный (одна, во всю ширину).
// Запуск: node Временные/snimki_setki.js
const { chromium } = require('/home/user/Временные/плейрайт.js');
const path = require('path');

const stranicy = [
  ['главная',   'Проект/Начать учиться.html'],
  ['предметы',  'Проект/База данных/5 класс.html'],
  ['материалы', 'Проект/База данных/5 класс/История.html'],
];
const shiriny = [[1920, 'десктоп'], [1199, 'узкий'], [940, 'планшет'], [680, 'мобильный']];

(async () => {
  const b = await chromium.launch();
  for (const [imya, f] of stranicy) {
    for (const [w, kak] of shiriny) {
      const p = await b.newPage({ viewport: { width: w, height: 1200 } });
      await p.goto('file://' + path.resolve(f), { waitUntil: 'load' });
      await p.waitForTimeout(300);
      await p.screenshot({ path: `Временные/снимки/сетка-${imya}-${kak}.png`,
                           fullPage: true });
      await p.close();
    }
    console.log('снято: ' + imya);
  }
  await b.close();
})();
