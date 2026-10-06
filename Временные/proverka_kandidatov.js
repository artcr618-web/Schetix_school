// Быстрая проверка списка кодов: название, длительность и — главное —
// играет ли ролик во встроенном кадре. Тем же способом, каким его
// откроет наша страница.
//
//   node Временные/proverka_kandidatov.js <код> <код> ...
const { chromium } = require('playwright');

const kody = process.argv.slice(2);
if (!kody.length) { console.error('нужны коды видео'); process.exit(2); }
const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ' +
           '(KHTML, like Gecko) Chrome/124 Safari/537.36';

async function svedeniya(kod) {
  const r = await fetch(`https://rutube.ru/api/video/${kod}/?format=json`, {
    headers: { 'User-Agent': UA, Referer: 'https://rutube.ru/',
               Accept: 'application/json' },
  }).catch(() => null);
  if (!r || !r.ok) return { nazv: '', sek: 0, kanal: '' };
  const d = await r.json();
  return { nazv: d.title || '', sek: d.duration || 0,
           kanal: (d.author || {}).name || '' };
}

(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 900, height: 560 } });
  for (const kod of kody) {
    const s = await svedeniya(kod);
    await p.goto('https://rutube.ru/play/embed/' + kod + '/',
                 { waitUntil: 'domcontentloaded' }).catch(() => {});
    await p.waitForTimeout(3500);
    const itog = await p.evaluate(() => {
      const v = document.querySelector('video');
      const t = (document.body.innerText || '').replace(/\s+/g, ' ');
      return { video: !!v, dlina: v ? Math.round(v.duration || 0) : 0,
               nedostupno: /недоступно|ограничений|не найдено|удалено/i.test(t) };
    });
    const m = Math.floor(s.sek / 60), sc = s.sek % 60;
    const verdikt = itog.nedostupno ? 'ЗАКРЫТ ПО РЕГИОНАМ'
                  : (itog.video ? 'ИГРАЕТ' : 'кадра нет');
    console.log(`${kod} ${verdikt.padEnd(19)} ` +
                `${m}:${String(sc).padStart(2, '0')} в кадре ${itog.dlina} с | ` +
                `${s.nazv.slice(0, 62)}`);
  }
  await b.close();
})();
