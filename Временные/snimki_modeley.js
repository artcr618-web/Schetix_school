// Снимки шести моделей экрана с главной страницы: для таблицы моделей
// и для сравнения «до/после» правок вида.
// Запуск: bash Инструменты/с_плейрайтом.sh node Временные/snimki_modeley.js [папка]
const { chromium } = require('/home/user/Временные/плейрайт.js');
const path = require('path');
const kuda = process.argv[2] || 'Временные/снимки';
const kadry = [[1920, '1-широкий'], [1280, '2-обычный'], [1100, '3-планшет-гор'],
               [800, '4-планшет-верт'], [560, '5-телефон-гор'], [360, '6-телефон-верт']];
(async () => {
  const b = await chromium.launch();
  for (const [w, imya] of kadry) {
    const p = await b.newPage({ viewport: { width: w, height: 1000 } });
    await p.goto('file://' + path.resolve('Проект/Начать учиться.html'), { waitUntil: 'load' });
    await p.waitForTimeout(300);
    const h = await p.evaluate(() => Math.min(
      Math.ceil(document.querySelector('.setka').getBoundingClientRect().bottom) + 20, 1500));
    await p.setViewportSize({ width: w, height: h });
    await p.waitForTimeout(220);
    await p.screenshot({ path: path.join(kuda, `модель-${imya}.png`) });
    await p.close();
  }
  await b.close();
  console.log('снято шесть моделей в ' + kuda);
})();
