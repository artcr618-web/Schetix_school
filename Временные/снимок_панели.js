// Снимки панели плейлиста «до/после»: одно и то же окно, один и тот же
// урок. Нужны для коллажа (Временные/коллаж_панели.py).
//
// Запуск: bash Инструменты/с_плейрайтом.sh node Временные/снимок_панели.js до
// Кладёт Временные/снимки/панель-<окно>-<метка>.png
const { chromium } = require('./плейрайт.js');
const path = require('path');
const fs = require('fs');

const metka = process.argv[2] || 'снимок';
const kuda = path.join(__dirname, 'снимки');
const stranica = path.resolve('Проект/База данных/HTML/5 класс/История/видеоуроки.html');

(async () => {
  const b = await chromium.launch();
  fs.mkdirSync(kuda, { recursive: true });
  for (const [w, h] of [[1600, 1000], [800, 1000]]) {
    const p = await b.newPage({ viewport: { width: w, height: h } });
    await p.goto('file://' + stranica, { waitUntil: 'domcontentloaded' });
    await p.waitForTimeout(700);
    // Панель плейлиста открыта прямо в разметке страницы (класс в body).
    // Если бы её открывали кнопкой, shkPleylist поставил бы фокус на
    // первую строку и та получила бы жёлтую рамку клавиатурного фокуса —
    // для снимка это лишнее, поэтому фокус снимаем.
    await p.evaluate(() => {
      const telo = document.body;
      if (!telo.classList.contains('pleylist-otkryto') && window.shkPleylist) {
        window.shkPleylist(true);
      }
      if (document.activeElement) document.activeElement.blur();
    });
    await p.waitForTimeout(600);
    // Один урок «играет» — видно и обычные строки, и активную.
    await p.evaluate(() => {
      const sp = document.querySelector('#pleylist-panel .pleylist.aktiven')
              || document.querySelector('#pleylist-panel .pleylist');
      const vse = sp ? sp.querySelectorAll('a.trek') : [];
      const a = vse[2] || vse[0];
      if (a) a.click();
      if (document.activeElement) document.activeElement.blur();
    });
    await p.waitForTimeout(800);
    const fayl = path.join(kuda, `панель-${w}-${metka}.png`);
    await p.screenshot({ path: fayl });
    console.log('снимок:', path.basename(fayl));
    await p.close();
  }
  await b.close();
})();
