const path = require('path');
const { chromium } = require('./плейрайт.js');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  await p.goto('file://' + path.resolve('Проект/Начать учиться.html'));
  await p.waitForTimeout(400);
  const mery = async (podpis) => {
    const d = await p.evaluate(() => {
      const im = document.getElementById('imya'), ce = document.getElementById('tsel');
      const sl = document.querySelector('.privet-slovo');
      const centr = x => Math.round(x.left + x.width / 2);
      return {
        imya: { centr: centr(im.getBoundingClientRect()), shirina: Math.round(im.getBoundingClientRect().width) },
        cel: { centr: centr(document.querySelector('.privet-tsel').getBoundingClientRect()),
               shirina: Math.round(document.querySelector('.privet-tsel').getBoundingClientRect().width),
               pole: Math.round(ce.getBoundingClientRect().width),
               slovo: Math.round(sl.getBoundingClientRect().width) },
        okno: Math.round(window.innerWidth / 2),
      };
    });
    console.log(podpis, '| центр имени', d.imya.centr, '| центр цели', d.cel.centr, '| середина окна', d.okno,
                '| поле цели', d.cel.pole);
    return d;
  };
  await mery('пустые   ');
  await p.fill('#imya', 'Аня');
  await p.fill('#tsel', 'Закончить восьмой класс на отлично');
  await p.waitForTimeout(200);
  await mery('с текстом');
  await p.screenshot({ path: 'Временные/снимки/главная-центр.png' });
  await b.close();
})();
