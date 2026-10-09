// Снимки «до/после» для сверки вида: то же окно, меню закрыто и открыто.
// «до» — папка прежней сборки (её подкладывают рядом), «после» — Проект.
// Запуск: bash Инструменты/с_плейрайтом.sh node Временные/sravnenie_vida.js <папка-до>
const { chromium } = require('./плейрайт.js');
const path = require('path');
const fs = require('fs');

const sverhu = process.argv[2] || '';
const kuda = '/tmp/sravn';
const stranicy = [['главная', 'Начать учиться.html'],
                  ['предметы', 'База данных/HTML/5 класс.html'],
                  ['география', 'База данных/HTML/5 класс/География.html'],
                  ['материалы', 'База данных/HTML/5 класс/История.html']];
const kadry = [[1920, '1-широкий'], [1280, '2-обычный'], [1100, '3-планшет-гор'],
               [800, '4-планшет-верт'], [640, '4б-планшет-верт-узко'],
               [560, '5-телефон-гор'], [360, '6-телефон-верт']];

(async () => {
  const b = await chromium.launch();
  fs.mkdirSync(kuda, { recursive: true });
  for (const [imya, f] of stranicy)
    for (const [w, kak] of kadry)
      for (const [kogda, papka, menyu] of [
             ['do', sverhu, false], ['posle', 'Проект', false],
             ['do-m', sverhu, true], ['posle-m', 'Проект', true]]) {
        if (!papka) continue;
        const p = await b.newPage({ viewport: { width: w, height: 1000 } });
        await p.goto('file://' + path.resolve(papka, f), { waitUntil: 'load' });
        await p.waitForTimeout(300);
        if (menyu) {
          await p.evaluate(() => document.body.classList.add('menu-otkryto'));
          await p.waitForTimeout(600);
        }
        const h = await p.evaluate(() => {
          const els = [...document.querySelectorAll('.setka, .stroka')];
          const niz = els.length ? Math.max(...els.map(
            e => e.getBoundingClientRect().bottom)) : 800;
          return Math.min(Math.ceil(niz) + 20, 1500);
        });
        await p.setViewportSize({ width: w, height: h });
        await p.waitForTimeout(250);
        await p.screenshot({ path: path.join(kuda, `${imya}-${kak}-${kogda}.png`) });
        await p.close();
      }
  await b.close();
  console.log('снято в ' + kuda);
})();
