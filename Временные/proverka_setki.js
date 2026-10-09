// Проверка разметки плашек: вердикты, а не замеры.
//
// Числа берутся из Временные/разметка.json — того же файла, из которого
// собирается CSS (Инструменты/разметка.py). Поэтому проверка не может
// разойтись с вёрсткой: если разметку правят, правят и таблицу.
//
// Главное, что здесь проверяется: раскладка считается по РАБОЧЕЙ ширине —
// ширине той области, где стоят плашки, а не по ширине окна. Открытое
// меню забирает у страницы своё место, и плашки обязаны перестроиться по
// остатку: иначе в ряд встают три плашки там, где помещаются две, и цифры
// вылезают наружу. Поэтому каждая страница мерится дважды — с закрытым и
// с открытым меню, а ожидаемое число плашек в ряду берётся от ширины
// контейнера рабочей ширины, а не от ширины окна.
//
// Проверяется:
//   1. Плашки одного размера — в ряду и на всех страницах при одном окне.
//   2. Ряд заполнен целиком: плашка шире не «по содержимому», а по кадру.
//   3. Содержимое плашки влезает в неё (название, цифра, подпись).
//   4. В ряд встаёт столько плашек, сколько положено рабочей ширине.
//   5. Рабочая ширина — это окно минус открытая панель (и не больше 1500).
//   6. Панели (меню и плейлист) стоят снаружи контейнера рабочей ширины:
//      внутри него position:fixed считался бы от контейнера, и панель
//      уехала бы за край экрана.
//   7. Панель во всю ширину экрана — с вертикального планшета и на
//      телефонах; на десктопах она занимает часть экрана.
//   8. Ни одна страница не уезжает вбок — ни с меню, ни без.
//
// Запуск: bash Инструменты/с_плейрайтом.sh node Временные/proverka_setki.js
const { chromium } = require('./плейрайт.js');
const path = require('path');
const fs = require('fs');

const razmetka = JSON.parse(fs.readFileSync(
  path.resolve(__dirname, 'разметка.json'), 'utf8'));
const KONTEYNER = razmetka.konteyner;   // имя контейнера в CSS
const ZONA = razmetka.zona_klass;      // класс блока рабочей ширины
const VO_VSYU = razmetka.menyu_vo_vsyu; // уже этого — панель во всю ширину

const plitoshnye = [
  ['главная',       'Проект/Начать учиться.html'],
  ['предметы 5',    'Проект/База данных/HTML/5 класс.html'],
  ['материалы 5И',  'Проект/База данных/HTML/5 класс/История.html'],
  ['материалы 7И',  'Проект/База данных/HTML/7 класс/История.html'],
];
// ...и остальные виды страниц: без плашек они тоже не должны уезжать
// вбок, а панели должны вести себя так же. У страницы списка нет ни
// меню, ни плашек — она собрана своим простым шаблоном (gen_spisok.py),
// поэтому контейнера рабочей ширины у неё нет и быть не должно.
const vse = plitoshnye.concat([
  ['видеоуроки',    'Проект/База данных/HTML/5 класс/История/видеоуроки.html', true],
  ['кино',          'Проект/База данных/HTML/5 класс/История/кино.html', true],
  ['тренажёры',     'Проект/База данных/HTML/7 класс/Английский/тренажёры.html', true],
  ['список',        'Документация/Что не нашлось.html', false],
]);

// По три ширины на каждую модель экрана.
const shiriny = [1920, 1600, 1440, 1280, 1200, 1199, 1100, 1024, 960,
                 959, 900, 800, 768, 700, 640, 639, 600, 560, 480, 400,
                 360, 320];

// Полоса раскладки для ширины — той же таблицей, что и CSS.
function polosa(w) {
  for (let i = razmetka.polosy.length - 1; i > 0; i--) {
    if (w <= razmetka.polosy[i].do) return razmetka.polosy[i];
  }
  return razmetka.polosy[0];
}

// Мерки состояния страницы: плашки, рабочая ширина, панели.
function merki(imya) {
  return `(() => {
    const pl = [...document.querySelectorAll('.setka a.plitka')];
    const setka = document.querySelector('.setka');
    const kont = document.querySelector('.${ZONA}');
    const ryady = {};
    pl.forEach(a => {
      const k = Math.round(a.getBoundingClientRect().top);
      ryady[k] = (ryady[k] || 0) + 1;
    });
    const kolonki = Object.values(ryady);
    // всё, что нарисовано внутри плашки, обязано в ней и остаться
    const vylez = pl.filter(a => {
      const r = a.getBoundingClientRect();
      if (a.scrollWidth - a.clientWidth > 2) return true;
      if (a.scrollHeight - a.clientHeight > 2) return true;
      return [...a.querySelectorAll('*')].some(ch => {
        const c = ch.getBoundingClientRect();
        if (!c.width && !c.height) return false;
        return c.right > r.right + 2 || c.left < r.left - 2 ||
               c.top < r.top - 2 || c.bottom > r.bottom + 2;
      });
    }).length;
    const pan = [...document.querySelectorAll('aside.panel')].map(pn => {
      const r = pn.getBoundingClientRect();
      return { id: pn.id, left: Math.round(r.left), right: Math.round(r.right),
               bottom: Math.round(r.bottom),
               w: Math.round(r.width),
               v_zone: !!pn.closest('.${ZONA}') };
    });
    return {
      est: !!setka, plitok: pl.length,
      v_ryadu: kolonki.length ? Math.max(...kolonki) : 0,
      shiriny: pl.map(a => Math.round(a.getBoundingClientRect().width)),
      kolonok: setka ? getComputedStyle(setka)
        .gridTemplateColumns.split(' ').length : 0,
      setka_shirina: setka ? setka.getBoundingClientRect().width : 0,
      zazhor: setka ? parseFloat(getComputedStyle(setka).columnGap) : 0,
      vylez: vylez,
      zona: kont ? Math.round(kont.getBoundingClientRect().width) : -1,
      zona_est: !!kont,
      pan: pan, cx: Math.round(window.innerWidth),
      bokom: (() => { window.scrollTo(400, 0);
                      const u = window.scrollX; window.scrollTo(0, 0);
                      return Math.round(u); })(),
    };
  })()`;
}

(async () => {
  const b = await chromium.launch();
  const bedy = [];
  const razmery = {};   // ширина окна -> {страница: ширина плашки}

  // Панель занимает столько, сколько ей отведено: во всю ширину экрана
  // на вертикальном планшете и телефонах, 420 px на широком окне.
  function zhdyom_panel(w) {
    return (w < VO_VSYU) ? w : 420;
  }
  // Рабочая ширина — это остаток окна после открытой панели. Панель во
  // всю ширину страницу не сжимает: она её накрывает, и раскладка за ней
  // остаётся по ширине окна. Шире 1500 страница не растягивается —
  // но это уже .wrap внутри, а не рабочая ширина: там раскладка одна
  // и та же (1440+ — широкий экран).
  function zhdyom_zona(cx, menyu) {
    if (!menyu) return cx;
    const sh = zhdyom_panel(cx);
    return (sh >= cx) ? cx : cx - sh;
  }

  for (const [imya, f] of plitoshnye) {
    razmery[imya] = {};
    for (const w of shiriny) {
      const p = await b.newPage({ viewport: { width: w, height: 900 } });
      await p.goto('file://' + path.resolve(f), { waitUntil: 'load' });
      await p.waitForTimeout(200);
      // прогоняем каждую ширину дважды: меню закрыто и меню открыто —
      // страница перестраивается по рабочей ширине, а не по окну
      for (const menyu of [false, true]) {
        if (menyu) {
          await p.evaluate(() => document.body.classList.add('menu-otkryto'));
          await p.waitForTimeout(450);
        }
        const m = await p.evaluate(merki(imya));
        const gde = `${imya} ${w}${menyu ? ' с меню' : ''}`;
        if (!m.est) { bedy.push(`${gde}: сетки нет`); break; }
        if (!m.zona_est) {
          bedy.push(`${gde}: нет контейнера рабочей ширины .${KONTEYNER}`);
          break;
        }
        if (m.shiriny[0]) razmery[imya][menyu ? w + '+м' : w] = m.shiriny[0];

        // рабочая ширина = окно минус открытая панель, и не больше пола
        const zona_zhdyom = zhdyom_zona(m.cx, menyu);
        if (Math.abs(m.zona - zona_zhdyom) > 3) {
          bedy.push(`${gde}: рабочая ширина ${m.zona}, ждём ${zona_zhdyom} ` +
                    `(окно ${m.cx} минус панель)`);
        }
        // сколько плашек в ряд — по рабочей ширине, а не по окну
        const zhdyom = Math.min(polosa(m.zona).v_ryadu, m.plitok);
        if (m.v_ryadu !== zhdyom) {
          bedy.push(`${gde}: в ряду ${m.v_ryadu}, ждём ${zhdyom} ` +
                    `(${polosa(m.zona).imya}, рабочая ${m.zona})`);
        }
        if (new Set(m.shiriny).size > 1) {
          bedy.push(`${gde}: плашки разного размера: ` +
                    [...new Set(m.shiriny)].join(', '));
        }
        const kolonka = (m.setka_shirina - (m.kolonok - 1) * m.zazhor) /
                        m.kolonok;
        if (Math.abs(m.shiriny[0] - kolonka) > 1.5) {
          bedy.push(`${gde}: плашка ${m.shiriny[0]} при колонке ` +
                    `${Math.round(kolonka)} — ряд заполнен не целиком`);
        }
        if (m.vylez) {
          bedy.push(`${gde}: у ${m.vylez} плашек содержимое не влезает`);
        }
        // ни одна страница не уезжает вбок
        if (m.bokom > 1) bedy.push(`${gde}: уехал вбок на ${m.bokom}`);
        // панели: снаружи контейнера и во всю ширину, где положено
        for (const pn of m.pan) {
          if (pn.v_zone) {
            bedy.push(`${gde}: панель ${pn.id} внутри контейнера рабочей ` +
                      `ширины — position:fixed считался бы от него`);
          }
          if (!menyu || pn.id !== 'panel') continue;
          const sh_zhdyom = zhdyom_panel(w);
          if (Math.abs(pn.w - sh_zhdyom) > 3) {
            bedy.push(`${gde}: панель ${pn.w}, ждём ${sh_zhdyom}`);
          }
          if (Math.abs(pn.right - m.cx) > 2 || pn.left < -2) {
            bedy.push(`${gde}: панель не прижата к правому краю: ` +
                      JSON.stringify(pn));
          }
          // низ панели — низ экрана, а не низ страницы: это и есть
          // признак, что контейнер её не перехватил
          if (Math.abs(pn.bottom - 900) > 2) {
            bedy.push(`${gde}: низ панели ${pn.bottom} вместо 900 — ` +
                      `панель считается от контейнера`);
          }
        }
      }
      await p.close();
    }
  }

  // один размер на всех страницах при одном окне — и с меню, и без
  for (const w of shiriny) {
    for (const klyuch of [w, w + '+м']) {
      const znacheniya = Object.entries(razmery)
        .map(([imya, po]) => [imya, po[klyuch]]).filter(x => x[1]);
      if (znacheniya.length < 2) continue;
      const raznica = [...new Set(znacheniya.map(([, v]) => v))];
      if (raznica.length > 1) {
        bedy.push(`на ${klyuch} плашки разного размера: ` +
          znacheniya.map(([i, v]) => `${i} ${v}`).join(', '));
      }
    }
  }

  // ---- ВСЕ страницы с плашками, с открытым меню ----
  // Главное обещание правки: ни на одной странице с открытым меню
  // содержимое плашек не вылезает и ряд не остаётся прежним, когда
  // места стало меньше. Поэтому прогоняем не четыре страницы, а все,
  // где есть плашки, — и на каждой открываем меню.
  const s_plitkami = [];
  (function sobiraem(sp) {
    for (const imya of fs.readdirSync(sp)) {
      const polny = path.join(sp, imya);
      const st = fs.statSync(polny);
      if (st.isDirectory()) sobiraem(polny);
      else if (imya.endsWith('.html')) {
        const t = fs.readFileSync(polny, 'utf8');
        if (t.includes('class="setka')) {
          s_plitkami.push([path.relative('Проект', polny),
                           polny.replace(/\\/g, '/')]);
        }
      }
    }
  })('Проект');

  for (const [imya, f] of s_plitkami) {
    for (const w of [1600, 1280, 1024, 900, 640, 360]) {
      const p = await b.newPage({ viewport: { width: w, height: 900 } });
      await p.goto('file://' + path.resolve(f), { waitUntil: 'load' });
      await p.waitForTimeout(200);
      await p.evaluate(() => document.body.classList.add('menu-otkryto'));
      await p.waitForTimeout(400);
      const m = await p.evaluate(merki(imya));
      const gde = `${imya} ${w} с меню`;
      if (m.bokom > 1) bedy.push(`${gde}: уехал вбок на ${m.bokom}`);
      if (m.vylez) bedy.push(`${gde}: у ${m.vylez} плашек содержимое не влезает`);
      if (m.v_ryadu !== Math.min(polosa(m.zona).v_ryadu, m.plitok)) {
        bedy.push(`${gde}: в ряду ${m.v_ryadu}, ждём ` +
                  `${Math.min(polosa(m.zona).v_ryadu, m.plitok)} ` +
                  `(рабочая ${m.zona}, ${polosa(m.zona).imya})`);
      }
      for (const pn of m.pan) {
        if (pn.v_zone) bedy.push(`${gde}: панель ${pn.id} внутри контейнера`);
        if (pn.id !== 'panel') continue;
        const sh_zhdyom = (w < VO_VSYU) ? w : 420;
        if (Math.abs(pn.w - sh_zhdyom) > 3) {
          bedy.push(`${gde}: панель ${pn.w}, ждём ${sh_zhdyom}`);
        }
      }
      await p.close();
    }
  }
  console.log(`страниц с плашками: ${s_plitkami.length}, каждая на 6 ширинах ` +
              'с открытым меню');

  // остальные виды страниц: не уезжают вбок и панель ведёт себя так же
  for (const [imya, f, est_zona] of vse.slice(plitoshnye.length)) {
    for (const w of razmetka.tochki.concat([959, 639, 480, VO_VSYU])) {
      const p = await b.newPage({ viewport: { width: w, height: 900 } });
      await p.goto('file://' + path.resolve(f), { waitUntil: 'load' });
      await p.waitForTimeout(200);
      for (const menyu of [false, true]) {
        if (menyu) {
          await p.evaluate(() => document.body.classList.add('menu-otkryto'));
          await p.waitForTimeout(450);
        }
        const m = await p.evaluate(merki(imya));
        const gde = `${imya} ${w}${menyu ? ' с меню' : ''}`;
        if (m.bokom > 1) bedy.push(`${gde}: уехал вбок на ${m.bokom}`);
        if (est_zona && !m.zona_est) {
          bedy.push(`${gde}: нет контейнера рабочей ширины`);
        }
        for (const pn of m.pan) {
          if (pn.v_zone) {
            bedy.push(`${gde}: панель ${pn.id} внутри контейнера`);
          }
          if (menyu && pn.id === 'panel') {
            const sh_zhdyom = zhdyom_panel(w);
            if (Math.abs(pn.w - sh_zhdyom) > 3) {
              bedy.push(`${gde}: панель ${pn.w}, ждём ${sh_zhdyom}`);
            }
          }
        }
      }
      await p.close();
    }
  }

  await b.close();

  console.log('размер плашки по ширине (м — с открытым меню):');
  for (const [imya, po] of Object.entries(razmery)) {
    console.log('  ' + imya.padEnd(14) +
      shiriny.filter(w => po[w] || po[w + '+м'])
        .map(w => `${w}:${po[w] || '—'}/${po[w + '+м'] || '—'}`).join(' '));
  }
  if (bedy.length) {
    console.log('\nПЛОХО:');
    bedy.forEach(b2 => console.log('  ' + b2));
    process.exit(1);
  }
  console.log('\nРазметка плашек: вердикт — хорошо ' +
              `(${plitoshnye.length} страниц × ${shiriny.length} ширин, ` +
              'каждая с меню и без, рабочие ширины и панели; ' +
              'все страницы с плашками на 6 ширинах с открытым меню; ' +
              `${vse.length} видов страниц на боковую прокрутку).`);
})();
