// Разбираемся с кадром VK Видео: что он показывает, появляется ли <video>
// после нажатия «играть», идёт ли время. RuTube для сравнения.
const { chromium } = require('./плейрайт.js');
const http = require('http');

const kadry = [
  ['VK-муром', 'https://vk.com/video_ext.php?oid=-165903&id=456240391'],
  ['VK-остров', 'https://vk.com/video_ext.php?oid=-60958526&id=456266846'],
];
const str = `<!doctype html><html lang="ru"><head><meta charset="utf-8">
<style>body{background:#0f141b;margin:0;padding:16px}iframe{width:880px;height:495px;border:0}</style>
</head><body>${kadry.map(([i, u]) =>
  `<iframe src="${u}" allow="autoplay; fullscreen" allowfullscreen title="${i}"></iframe>`).join('')}</body></html>`;

async function smotrim(p, imya) {
  const f = p.frames().find(x => x !== p.mainFrame() && /vk\.com|rutube\.ru/.test(x.url()));
  if (!f) { console.log(`   ${imya}: кадра нет`); return; }
  const vnutri = async () => f.evaluate(() => {
    const v = document.querySelector('video');
    return {
      video: !!v,
      pauza: v ? v.paused : null,
      dlina: v ? Math.round(v.duration || 0) : 0,
      vremya: v ? Math.round(v.currentTime || 0) : 0,
      gotovnost: v ? v.readyState : -1,
      tekst: (document.body.innerText || '').replace(/\s+/g, ' ').slice(0, 160),
    };
  });
  console.log(`   ${imya} до нажатия:`, JSON.stringify(await vnutri()));

  // нажимаем в середину кадра — там у обоих плееров кнопка «играть»
  const ram = await f.frameElement();
  const korobka = await ram.boundingBox();
  if (korobka) {
    await p.mouse.click(korobka.x + korobka.width / 2, korobka.y + korobka.height / 2);
    await p.waitForTimeout(6000);
  }
  console.log(`   ${imya} после нажатия:`, JSON.stringify(await vnutri()));
}

(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 960, height: 1100 } });
  const server = http.createServer((z, o) => { o.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' }); o.end(str); });
  await new Promise(r => server.listen(8199, '0.0.0.0', r));
  await p.goto('http://127.0.0.1:8199/', { waitUntil: 'load' });
  await p.waitForTimeout(5000);
  for (const [imya] of kadry) await smotrim(p, imya);
  await p.screenshot({ path: '/home/user/Временные/снимки/вк-проба-вторая.png', fullPage: true });
  console.log('\nкадров всего:', p.frames().length, '|',
    p.frames().map(x => x.url().slice(0, 52)).join(' ; '));
  server.close();
  await b.close();
})();

