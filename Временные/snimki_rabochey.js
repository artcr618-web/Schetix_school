// Снимки рабочей ширины: как страница выглядит с ОТКРЫТЫМ меню.
//
// Раскладка считается по ширине области, где стоят плашки, а не по ширине
// окна (РАЗМЕТКА.md). Здесь это видно глазами: снимок при том же окне с
// открытым меню и без — плашки не должны сжиматься и вылезать.
//
// Второй довод — папка «до»: если передать путь к прежней сборке, тот же
// кадр снимается и там, и снимки кладутся в пару «до/после».
//
// Запуск:
//   bash Инструменты/с_плейрайтом.sh node Временные/snimki_rabochey.js [папка-до]
const { chromium } = require('/home/user/Временные/плейрайт.js');
const path = require('path');
const fs = require('fs');

const sverhu = process.argv[2] || '';          // прежняя сборка, если есть
const kuda = 'Временные/снимки';
const kadry = [[1600, '1-широкий'], [1280, '2-обычный'], [1100, '3-планшет-гор'],
               [900, '4-планшет-верт'], [640, '4б-планшет-верт-узко']];
const stranicy = [
  ['главная', 'Начать учиться.html'],
  ['предметы', 'База данных/5 класс.html'],
  ['география', 'База данных/5 класс/География.html'],
];

(async () => {
  const b = await chromium.launch();
  for (const [imya, f] of stranicy) {
    for (const [w, kak] of kadry) {
      for (const [kogda, papka] of [['до', sverhu], ['после', 'Проект']]) {
        if (!papka) continue;
        const p = await b.newPage({ viewport: { width: w, height: 1000 } });
        await p.goto('file://' + path.resolve(papka, f), { waitUntil: 'load' });
        await p.waitForTimeout(300);
        await p.evaluate(() => document.body.classList.add('menu-otkryto'));
        await p.waitForTimeout(600);
        const h = await p.evaluate(() => {
          const s = document.querySelector('.setka');
          return Math.min(Math.ceil(s.getBoundingClientRect().bottom) + 20, 1400);
        });
        await p.setViewportSize({ width: w, height: h });
        await p.waitForTimeout(300);
        const fayl = path.join(kuda, `рабочая-${imya}-${kak}-${kogda}.png`);
        await p.screenshot({ path: fayl });
        console.log(fayl);
        await p.close();
      }
    }
  }
  await b.close();
  if (!sverhu) {
    console.log('снимки с открытым меню сняты (папка «до» не задана)');
  }
})();
