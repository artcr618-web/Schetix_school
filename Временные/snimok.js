const path = require('path');
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  for (const [f, imya] of [['Проект/База данных/5 класс.html', 'классы'],
                           ['Проект/Начать учиться.html', 'главная']]) {
    await p.goto('file://' + path.resolve(f));
    await p.waitForTimeout(500);
    await p.screenshot({ path: `Временные/снимки/${imya}.png` });
  }
  await b.close();
})();
