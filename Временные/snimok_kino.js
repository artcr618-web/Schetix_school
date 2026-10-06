const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1440, height: 1000 } });
  for (const [f, imya] of [
    ['Проект/База данных/5 класс/История/кино.html', 'кино-5-история'],
    ['Проект/База данных/5 класс/География/кино.html', 'кино-5-география'],
  ]) {
    await p.goto('file://' + path.resolve(f), { waitUntil: 'load' });
    await p.waitForTimeout(1500);
    await p.evaluate(() => window.shkIgrat(document.querySelectorAll('.trek')[1]));
    await p.waitForTimeout(3000);
    await p.screenshot({ path: `Временные/снимки/${imya}.png`, fullPage: false });
    const itog = await p.evaluate(() => ({
      zag: document.querySelector('#pleyer-zag').textContent,
      podborki: [...document.querySelectorAll('.pl-nazv')].map(x => x.textContent),
      vopros: document.querySelector('#pl-zag') ? document.querySelector('#pl-zag').textContent : '',
    }));
    console.log(imya, JSON.stringify(itog, null, 0).slice(0, 300));
  }
  await b.close();
})();
