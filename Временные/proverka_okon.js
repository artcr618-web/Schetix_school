// Ошибки в настоящем браузере: консоль и необработанные исключения.
//   node Временные/proverka_okon.js
const fs = require('fs'), path = require('path');
const { chromium } = require('playwright');
const stranicy = [];
(function obhod(d) {
  for (const f of fs.readdirSync(d)) {
    const p = path.join(d, f);
    if (fs.statSync(p).isDirectory()) obhod(p);
    else if (f.endsWith('.html')) stranicy.push(p);
  }
})('Проект');
(async () => {
  const b = await chromium.launch();
  let vsego = 0;
  for (const f of stranicy) {
    const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
    const osh = [];
    p.on('console', m => { if (m.type() === 'error') osh.push(m.text().slice(0, 120)); });
    p.on('pageerror', e => osh.push('ИСКЛЮЧЕНИЕ: ' + String(e).slice(0, 120)));
    await p.goto('file://' + path.resolve(f));
    await p.waitForTimeout(250);
    // походим по странице: меню, плейлист, первый урок
    await p.evaluate(() => {
      try { window.shkPanel(true); window.shkPanel(false); } catch (e) {}
      try { window.shkPleylistTog(); window.shkPleylistTog(); } catch (e) {}
      const t = document.querySelector('.trek');
      if (t) { t.click(); }
    });
    await p.waitForTimeout(350);
    if (osh.length) { vsego += osh.length; console.log('ОШИБКИ ' + f); osh.forEach(x => console.log('   ', x)); }
    await p.close();
  }
  console.log('страниц проверено: ' + stranicy.length + ', ошибок: ' + vsego);
  await b.close();
  process.exit(vsego ? 1 : 0);
})();
