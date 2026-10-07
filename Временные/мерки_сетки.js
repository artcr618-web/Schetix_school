// Замер сетки плашек: сколько в ряду, какого размера, где вылезает за экран.
// Запуск: node Временные/мерки_сетки.js
const { chromium } = require('/home/user/Временные/плейрайт.js');
const path = require('path');

const stranicy = [
  ['классы (главная)',    'Проект/Начать учиться.html'],
  ['предметы 5 класс',    'Проект/База данных/5 класс.html'],
  ['материалы 5И (4 шт)', 'Проект/База данных/5 класс/История.html'],
  ['материалы 7И (5 шт)', 'Проект/База данных/7 класс/История.html'],
  ['видеоуроки 5И',       'Проект/База данных/5 класс/История/видеоуроки.html'],
  ['кино 5И',             'Проект/База данных/5 класс/История/кино.html'],
  ['тренажёры 7Англ',     'Проект/База данных/7 класс/Английский/тренажёры.html'],
  ['список ненайденного', 'Проект/Что не нашлось.html'],
];
const shiriny = [1920, 1440, 1200, 1199, 1100, 1024, 960, 959, 768, 640, 480, 360, 320];

(async () => {
  const b = await chromium.launch();
  for (const [imya, f] of stranicy) {
    console.log('=== ' + imya + ' ===');
    for (const w of shiriny) {
      const p = await b.newPage({ viewport: { width: w, height: 900 } });
      await p.goto('file://' + path.resolve(f), { waitUntil: 'load' });
      await p.waitForTimeout(250);
      const m = await p.evaluate(() => {
        const setka = document.querySelector('.setka');
        const pl = [...document.querySelectorAll('.setka a.plitka')];
        const po_ryadu = {};
        pl.forEach(a => {
          const r = a.getBoundingClientRect();
          const k = Math.round(r.top);
          po_ryadu[k] = (po_ryadu[k] || 0) + 1;
        });
        const shiriny_plitok = [...new Set(pl.map(a =>
          Math.round(a.getBoundingClientRect().width)))];
        const vysoty_plitok = [...new Set(pl.map(a =>
          Math.round(a.getBoundingClientRect().height)))];
        // кто именно шире экрана
        const vynovniki = [];
        document.querySelectorAll('body *').forEach(el => {
          const r = el.getBoundingClientRect();
          if (r.width > 0 && r.right > innerWidth + 1) {
            const imya = el.tagName.toLowerCase() +
              (el.className && typeof el.className === 'string'
                ? '.' + el.className.trim().split(/\s+/).join('.') : '');
            vynovniki.push(imya + ' ↔' + Math.round(r.right) +
                           ' (' + Math.round(r.width) + ')');
          }
        });
        const unikal = [...new Set(vynovniki)].slice(0, 4);
        return {
          ryady: Object.values(po_ryadu).join('+'),
          shirina: shiriny_plitok.join(','),
          vysota: vysoty_plitok.join(','),
          kont: setka ? Math.round(setka.getBoundingClientRect().width) : 0,
          skroll: document.documentElement.scrollWidth - innerWidth,
          vynovniki: unikal,
          shrift: pl[0] && pl[0].querySelector('.nazv')
            ? getComputedStyle(pl[0].querySelector('.nazv')).fontSize : '',
        };
      });
      console.log('  ' + String(w).padStart(4) + ': в ряду ' + (m.ryady || '—').padEnd(9) +
        ' плашка ' + (m.shirina || '—').padEnd(11) + '×' + (m.vysota || '—').padEnd(5) +
        ' сетка ' + String(m.kont).padStart(4) + ' шрифт ' + m.shrift.padEnd(5) +
        (m.skroll > 1 ? '  ← ПРОКРУТКА +' + m.skroll + ' ' + m.vynovniki.join(' | ') : ''));
      await p.close();
    }
  }
  await b.close();
})();
