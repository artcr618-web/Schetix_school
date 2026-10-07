// Подбор размеров плашки для тесных полос: планшет вертикальный
// (640–959) и телефоны (ниже 640). Перебираем кандидатов и смотрим,
// у скольких плашек содержимое не влезает и не разного ли они размера.
//
// Запуск: bash Инструменты/с_плейрайтом.sh node Временные/podbor_razmerov.js
const { chromium } = require('/home/user/Временные/плейрайт.js');
const path = require('path');

const stranicy = [
  ['предметы 5',   'Проект/База данных/5 класс.html'],
  ['материалы 5И', 'Проект/База данных/5 класс/История.html'],
  ['материалы 7И', 'Проект/База данных/7 класс/История.html'],
  ['главная',      'Проект/Начать учиться.html'],
];

const tablet = {
  shiriny: [640, 700, 768, 860, 900, 959],
  varianty: [
    { imya: '16/9 · 28 · 15 · 20', kadr: '16 / 9', nazv: 28, poyas: 15, otstup: 20 },
    { imya: '16/10 · 28 · 15 · 20', kadr: '16 / 10', nazv: 28, poyas: 15, otstup: 20 },
    { imya: '16/10 · 26 · 14 · 18', kadr: '16 / 10', nazv: 26, poyas: 14, otstup: 18 },
    { imya: '4/3 · 24 · 14 · 18', kadr: '4 / 3', nazv: 24, poyas: 14, otstup: 18 },
  ],
};
const telefon = {
  shiriny: [320, 360, 400, 480, 560, 600, 639],
  varianty: [
    { imya: 'как сейчас', kadr: '16 / 9', nazv: 32, poyas: 17, otstup: 22 },
    { imya: '4/3 · 32 · 17 · 22', kadr: '4 / 3', nazv: 32, poyas: 17, otstup: 22 },
    { imya: '4/3 · 30 · 16 · 20', kadr: '4 / 3', nazv: 30, poyas: 16, otstup: 20 },
    { imya: '4/3 · 28 · 15 · 20', kadr: '4 / 3', nazv: 28, poyas: 15, otstup: 20 },
  ],
};

function css(v, do_) {
  return `@media (max-width:${do_}px){
    a.plitka{aspect-ratio:${v.kadr}; padding:${v.otstup}px 22px ${v.otstup}px calc(var(--polosa) + 24px)}
    a.plitka .nazv{font-size:${v.nazv}px}
    a.plitka .poyas{font-size:${v.poyas}px}
  }`;
}

async function proverit(b, v, do_, shiriny) {
  let nevlezaet = 0, raznogo = 0, vsego = 0;
  for (const [, f] of stranicy) {
    for (const w of shiriny) {
      const p = await b.newPage({ viewport: { width: w, height: 900 } });
      await p.goto('file://' + path.resolve(f), { waitUntil: 'load' });
      await p.addStyleTag({ content: css(v, do_) });
      await p.waitForTimeout(120);
      const m = await p.evaluate(() => {
        const pl = [...document.querySelectorAll('.setka a.plitka')];
        // Мерка та же, что в proverka_setki.js: содержимое по границам,
        // а не по scrollHeight — у колонки с justify-content:flex-end
        // scrollHeight переполнения не показывает.
        const vylez = pl.filter(a => {
          const r0 = a.getBoundingClientRect();
          const st = getComputedStyle(a);
          const vnutri = r0.height - parseFloat(st.paddingTop)
            - parseFloat(st.paddingBottom);
          let nuzhno = 0;
          [...a.children].forEach(ch => {
            const cs = getComputedStyle(ch);
            nuzhno += ch.getBoundingClientRect().height
              + parseFloat(cs.marginTop) + parseFloat(cs.marginBottom);
          });
          return nuzhno > vnutri + 1;
        }).length;
        const vysoty = [...new Set(pl.map(a =>
          Math.round(a.getBoundingClientRect().height)))];
        return { vsego: pl.length, vylez, raznyh: vysoty.length };
      });
      vsego += m.vsego;
      nevlezaet += m.vylez;
      raznogo += m.raznyh > 1 ? 1 : 0;
      await p.close();
    }
  }
  return { vsego, nevlezaet, raznogo };
}

(async () => {
  const b = await chromium.launch();
  for (const [imya, nabor, do_] of [['ПЛАНШЕТ ВЕРТИКАЛЬНЫЙ 640–959', tablet, 959],
                                    ['ТЕЛЕФОНЫ 320–639', telefon, 639]]) {
    console.log('=== ' + imya);
    for (const v of nabor.varianty) {
      const r = await proverit(b, v, do_, nabor.shiriny);
      console.log('  ' + v.imya.padEnd(22) +
        ' плашек ' + String(r.vsego).padStart(3) +
        ' | не влезает ' + String(r.nevlezaet).padStart(3) +
        ' | разной высоты ' + r.raznogo + ' проверок');
    }
  }
  await b.close();
})();
