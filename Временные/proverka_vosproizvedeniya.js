// Проверяем, что каждый отобранный ролик РЕАЛЬНО играет во встроенном
// кадре: открываем адрес встраивания и смотрим, появилось ли внутри
// <video> с длительностью и нет ли таблички «Видео недоступно…».
//
//   node Временные/proverka_vosproizvedeniya.js
//
// Берём ровно те ролики, что стоят в данных страниц кино и в баннере.
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const fayly = [
  'Временные/kino_istoriya_5.json',
  'Временные/kino_istoriya_7.json',
  'Временные/kino_geografiya_5.json',
  'Временные/banner_istoriya_7.json',
];

const vse = [];
for (const f of fayly) {
  const d = JSON.parse(fs.readFileSync(path.resolve(f), 'utf8'));
  for (const podborka of d['подборки']) {
    for (const v of podborka['видео']) {
      vse.push({ put: f.split('/').pop(), podborka: podborka['имя'],
                 nazvanie: v[0], kod: v[1] });
    }
  }
}
console.log('роликов к проверке: ' + vse.length);

(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 900, height: 560 } });
  let ploho = 0, bezVideo = 0;
  for (const v of vse) {
    const u = 'https://rutube.ru/play/embed/' + v.kod + '/';
    await p.goto(u, { waitUntil: 'domcontentloaded' }).catch(() => {});
    await p.waitForTimeout(3500);
    const sostoyanie = await p.evaluate(() => {
      const f = document.querySelector('iframe');
      const vn = f && f.contentDocument ? f.contentDocument : document;
      const t = (document.body.innerText || '').replace(/\s+/g, ' ');
      const video = (document.querySelector('video') ||
                     (vn && vn.querySelector ? vn.querySelector('video') : null));
      return {
        video: !!video,
        dlina: video ? Math.round(video.duration || 0) : 0,
        nedostupno: /недоступно|ограничений|не найдено|удалено/i.test(t),
      };
    });
    let zametka = '';
    if (sostoyanie.nedostupno) {
      zametka = 'НЕДОСТУПНО В НАШЕМ КРАЮ';
      ploho++;
    } else if (!sostoyanie.video) {
      zametka = 'кадр не создал видео';
      bezVideo++;
    }
    console.log(`${zametka ? '!!' : 'ок'} ${v.kod}  ${String(sostoyanie.dlina).padStart(5)} с  ` +
                `${v.nazvanie.slice(0, 46).padEnd(48)} [${v.podborka}] ${zametka}`);
  }
  console.log(`\nИтог: недоступно ${ploho}, без кадра ${bezVideo} из ${vse.length}`);
  await b.close();
})();
