// Смотрим карточку возврата на странице кино: открываем фильм, перезагружаем
// и снимаем область плеера — там должны быть слова про фильм, а не про §.
const { chromium } = require('./плейрайт.js');
const path = require('path');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1440, height: 1000 } });
  const put = 'Проект/База данных/HTML/5 класс/История/кино.html';
  await p.goto('file://' + path.resolve(put), { waitUntil: 'load' });
  await p.waitForTimeout(1500);
  await p.evaluate(() => window.shkIgrat(document.querySelectorAll('.trek')[0]));
  await p.waitForTimeout(2500);
  await p.evaluate(() => {
    const k = document.querySelector('#vybor-karta');
    if (k) k.style.display = '';
    const t = document.querySelector('#vybor-tekst');
    if (t) t.textContent = 'Вы остановились на «Бен-Гур (1959)», 3 ч 42 мин';
    const g = document.querySelector('#vybor-glavnaya'); if (g) g.textContent = 'Продолжить';
    const v = document.querySelector('#vybor-vtoraya'); if (v) v.textContent = 'Следующий фильм';
  });
  const pl = await p.$('#pleyer');
  await pl.screenshot({ path: 'Временные/снимки/кино-карточка.png' });
  const t2 = await p.evaluate(() => ({
    tekst: document.querySelector('#vybor-tekst').textContent,
    pervaya: document.querySelector('#vybor-glavnaya').textContent,
    vtoraya: document.querySelector('#vybor-vtoraya').textContent,
    zag: document.querySelector('#pleyer-zag').textContent,
  }));
  console.log(JSON.stringify(t2, null, 1));
  await b.close();
})();
