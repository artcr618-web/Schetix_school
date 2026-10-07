// Проверяем, можно ли встроить плееры Rutube и VK Видео в нашу страницу
// (то же самое, что делает наш плеер: iframe с адресом встраивания).
// Смотрим: не запретил ли сайт показ у нас, доходит ли запрос, видно ли
// <video> внутри кадра. Открываем двумя способами: с диска (file://) и
// по сети (http://) — у нас страница лежит на флешке, но браузеры
// обращаются с file:// к сети строже.
const { chromium } = require('./плейрайт.js');
const fs = require('fs');
const path = require('path');
const http = require('http');

const kuski = [
  ['VK', 'https://vk.com/video_ext.php?oid=-60958526&id=456266846&hd=2'],
  ['RuTube', 'https://rutube.ru/play/embed/2be338b05238ef66894b9ddebbaf29e3/'],
];

const kusok = `<!doctype html><html lang="ru"><head><meta charset="utf-8">
<title>проба</title><style>body{background:#0f141b;margin:0;padding:20px}
div{width:900px;margin:0 0 24px;background:#000}
iframe{width:900px;height:506px;border:0;display:block}</style></head><body>
${kuski.map(([i, u]) => `<div><iframe src="${u}" allow="autoplay; fullscreen; picture-in-picture" allowfullscreen title="${i}"></iframe></div>`).join('\n')}
</body></html>`;

const papka = '/home/user/Временные/снимки';
const fayl = '/home/user/Временные/vk_proba.html';
fs.mkdirSync(papka, { recursive: true });
fs.writeFileSync(fayl, kusok, 'utf-8');

async function proverit(b, adres, kak) {
  const p = await b.newPage({ viewport: { width: 960, height: 1200 } });
  const soobshch = [];
  p.on('console', m => { if (m.type() === 'error') soobshch.push('лог: ' + m.text().slice(0, 120)); });
  p.on('requestfailed', r => soobshch.push('запрос не прошёл: ' + r.url().slice(0, 70) + ' — ' + (r.failure() || {}).errorText));
  await p.goto(adres, { waitUntil: 'load' }).catch(e => soobshch.push('переход: ' + String(e).slice(0, 90)));
  await p.waitForTimeout(6000);

  console.log(`\n=== ${kak} (${adres.slice(0, 26)}…)`);
  for (const kadr of p.frames().filter(f => f !== p.mainFrame())) {
    let vnutr = { video: false, dlina: 0 };
    try {
      vnutr = await kadr.evaluate(() => {
        const v = document.querySelector('video');
        return { video: !!v, dlina: v ? Math.round(v.duration || 0) : 0 };
      });
    } catch (e) { vnutr = { video: 'нет доступа (' + String(e).slice(0, 40) + ')', dlina: 0 }; }
    console.log(`   кадр ${kadr.url().slice(0, 62)} → видео: ${vnutr.video}, ${vnutr.dlina} с`);
  }
  console.log('   замечания:', soobshch.length ? soobshch.join(' | ') : 'нет');
  await p.screenshot({ path: path.join(papka, `вк-проба-${kak}.png`), fullPage: true });
  await p.close();
}

(async () => {
  const b = await chromium.launch();
  await proverit(b, 'file://' + fayl, 'с диска');

  const server = http.createServer((z, o) => {
    o.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
    o.end(kusok);
  });
  await new Promise(r => server.listen(8199, '0.0.0.0', r));
  await proverit(b, 'http://127.0.0.1:8199/', 'по сети');
  server.close();
  await b.close();
})();
