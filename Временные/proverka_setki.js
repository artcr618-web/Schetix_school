// Проверка разметки плашек: вердикты, а не замеры.
//
// Числа берутся из Временные/разметка.json — того же файла, из которого
// собирается CSS (Инструменты/разметка.py). Поэтому проверка не может
// разойтись с вёрсткой: если разметку правят, правят и таблицу.
//
// Проверяется:
//   1. Плашки одного размера — в ряду и на всех страницах при одном окне.
//   2. Ряды по моделям экрана: десктопы 3, планшеты 2, телефоны 1.
//   3. Ряд заполнен целиком: плашка шире не «по содержимому», а по кадру.
//   4. Содержимое плашки влезает в неё (название и подпись не вылезают).
//   5. Ни одна страница не уезжает вбок — от 1920 до 320 px.
//
// Запуск: bash Инструменты/с_плейрайтом.sh node Временные/proverka_setki.js
const { chromium } = require('/home/user/Временные/плейрайт.js');
const path = require('path');
const fs = require('fs');

const razmetka = JSON.parse(fs.readFileSync(
  path.resolve(__dirname, 'разметка.json'), 'utf8'));

const plitoshnye = [
  ['главная',       'Проект/Начать учиться.html'],
  ['предметы 5',    'Проект/База данных/5 класс.html'],
  ['материалы 5И',  'Проект/База данных/5 класс/История.html'],
  ['материалы 7И',  'Проект/База данных/7 класс/История.html'],
];
const vse = plitoshnye.concat([
  ['видеоуроки',    'Проект/База данных/5 класс/История/видеоуроки.html'],
  ['кино',          'Проект/База данных/5 класс/История/кино.html'],
  ['тренажёры',     'Проект/База данных/7 класс/Английский/тренажёры.html'],
  ['список',        'Проект/Что не нашлось.html'],
]);

// По три ширины на каждую модель экрана.
const shiriny = [1920, 1600, 1440, 1280, 1200, 1199, 1100, 1024, 960,
                 959, 900, 800, 768, 700, 640, 639, 600, 560, 480, 400,
                 360, 320];

function polosa(w) {
  for (let i = razmetka.polosy.length - 1; i > 0; i--) {
    if (w <= razmetka.polosy[i].do) return razmetka.polosy[i];
  }
  return razmetka.polosy[0];
}

(async () => {
  const b = await chromium.launch();
  const bedy = [];
  const razmery = {};   // ширина окна -> {страница: ширина плашки}

  for (const [imya, f] of plitoshnye) {
    razmery[imya] = {};
    for (const w of shiriny) {
      const p = await b.newPage({ viewport: { width: w, height: 900 } });
      await p.goto('file://' + path.resolve(f), { waitUntil: 'load' });
      await p.waitForTimeout(200);
      const m = await p.evaluate(() => {
        const pl = [...document.querySelectorAll('.setka a.plitka')];
        const setka = document.querySelector('.setka');
        const ryady = {};
        pl.forEach(a => {
          const r = a.getBoundingClientRect();
          const k = Math.round(r.top);
          ryady[k] = (ryady[k] || 0) + 1;
        });
        const kolonki = Object.values(ryady);
        const v_ryadu = kolonki.length ? Math.max(...kolonki) : 0;
        const pervyy = kolonki.length ? kolonki[0] : 0;
        return {
          est: !!setka, plitok: pl.length, v_ryadu,
          shiriny: pl.map(a => Math.round(a.getBoundingClientRect().width)),
          kolonok: setka ? getComputedStyle(setka)
            .gridTemplateColumns.split(' ').length : 0,
          setka_shirina: setka ? setka.getBoundingClientRect().width : 0,
          zazhor: setka ? parseFloat(getComputedStyle(setka).columnGap) : 0,
          // содержимое внутри плашки
          vylezaet: pl.filter(a => {
            if (a.scrollHeight - a.clientHeight > 2) return true;
            const r = a.getBoundingClientRect();
            return [...a.children].some(ch => {
              const c = ch.getBoundingClientRect();
              return c.right > r.right + 2 || c.left < r.left - 2 ||
                     c.top < r.top - 2 || c.bottom > r.bottom + 2;
            });
          }).length,
        };
      });
      if (!m.est) { bedy.push(`${imya} ${w}: сетки нет`); await p.close(); continue; }
      if (m.shiriny[0]) razmery[imya][w] = m.shiriny[0];

      const zhdyom = Math.min(polosa(w).v_ryadu, m.plitok);
      if (m.v_ryadu !== zhdyom) {
        bedy.push(`${imya} ${w}: в ряду ${m.v_ryadu}, ждём ${zhdyom} ` +
                  `(${polosa(w).imya})`);
      }
      if (new Set(m.shiriny).size > 1) {
        bedy.push(`${imya} ${w}: плашки разного размера: ` +
                  [...new Set(m.shiriny)].join(', '));
      }
      // плашка занимает свою колонку целиком — это и есть максимальное
      // заполнение кадра
      const kolonka = (m.setka_shirina - (m.kolonok - 1) * m.zazhor) / m.kolonok;
      if (Math.abs(m.shiriny[0] - kolonka) > 1.5) {
        bedy.push(`${imya} ${w}: плашка ${m.shiriny[0]} при колонке ` +
                  `${Math.round(kolonka)} — ряд заполнен не целиком`);
      }
      if (m.vylezaet) {
        bedy.push(`${imya} ${w}: у ${m.vylezaet} плашек содержимое не влезает`);
      }
      await p.close();
    }
  }

  // один размер на всех страницах при одном окне
  for (const w of shiriny) {
    const znacheniya = Object.entries(razmery)
      .map(([imya, po]) => [imya, po[w]]).filter(x => x[1]);
    const raznica = [...new Set(znacheniya.map(([, v]) => v))];
    if (raznica.length > 1) {
      bedy.push(`на ${w} плашки разного размера: ` +
        znacheniya.map(([i, v]) => `${i} ${v}`).join(', '));
    }
  }

  // вбок не уезжает
  const bokom = [];
  for (const [imya, f] of vse) {
    for (const w of razmetka.tochki.concat([959, 639, 480])) {
      const p = await b.newPage({ viewport: { width: w, height: 900 } });
      await p.goto('file://' + path.resolve(f), { waitUntil: 'load' });
      await p.waitForTimeout(160);
      const d = await p.evaluate(() => {
        window.scrollTo(400, 0);
        const uehal = window.scrollX;
        window.scrollTo(0, 0);
        return uehal;
      });
      if (d > 1) bokom.push(`${imya} ${w}: уехал вбок на ${d}`);
      await p.close();
    }
  }

  await b.close();

  console.log('размер плашки по ширине окна:');
  for (const [imya, po] of Object.entries(razmery)) {
    console.log('  ' + imya.padEnd(14) +
      shiriny.filter(w => po[w]).map(w => `${w}:${po[w]}`).join(' '));
  }
  if (bedy.length || bokom.length) {
    console.log('\nПЛОХО:');
    [...bedy, ...bokom].forEach(b2 => console.log('  ' + b2));
    process.exit(1);
  }
  console.log('\nРазметка плашек: вердикт — хорошо ' +
              `(${plitoshnye.length} страниц × ${shiriny.length} ширин, ` +
              `${vse.length} видов страниц на боковую прокрутку).`);
})();
