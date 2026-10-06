const path = require('path');
const { chromium } = require('playwright');
const put = process.argv[2] || 'Проект/База данных/5 класс/География/видеоуроки.html';
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  await p.goto('file://' + path.resolve(put));
  await p.waitForTimeout(500);
  // раскроем первый плейлист, чтобы было видно и заголовки глав, и отступы
  await p.evaluate(() => {
    const d = document.querySelector('.pl-vse .pl-blok');
    if (d && !d.open) d.querySelector('summary').click();
    const vtoroy = document.querySelectorAll('.pl-vse .pl-blok')[1];
    if (vtoroy && !vtoroy.open) vtoroy.querySelector('summary').click();
  });
  await p.waitForTimeout(300);
  const ramka = await p.evaluate(() => {
    const r = document.querySelector('.pl-vse').getBoundingClientRect();
    return { y: Math.max(0, Math.round(r.top + window.scrollY) - 10),
             h: Math.round(r.height) + 20 };
  });
  await p.evaluate(y => window.scrollTo(0, y), ramka.y);
  await p.waitForTimeout(300);
  await p.screenshot({ path: 'Временные/снимки/плейлисты-под-кадром.png',
                       clip: { x: 0, y: 0, width: 1480, height: Math.min(1000, ramka.h) } });
  const otstupy = await p.evaluate(() => {
    const g = document.querySelector('.pl-vse .trek-gruppa');
    const t = document.querySelector('.pl-vse .trek');
    const im = document.querySelector('.pl-vse .pl-imya');
    return { zagolovok: g && { c: getComputedStyle(g).color, x: Math.round(g.getBoundingClientRect().left) },
             punkt: t && { x: Math.round(t.getBoundingClientRect().left) },
             imya: im && { x: Math.round(im.getBoundingClientRect().left), c: getComputedStyle(im).color } };
  });
  console.log('под кадром:', JSON.stringify(otstupy, null, 1));
  await b.close();
})();
