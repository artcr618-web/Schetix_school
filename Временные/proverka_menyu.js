// Меню боковое и панель плейлиста: ищем задвоенные линии, сравниваем
// крестик закрытия и смотрим, чем выделены пункты списков.
//
//   node Временные/proverka_menyu.js "Проект/База данных/5 класс/История/видеоуроки.html"
const fs = require('fs');
const path = require('path');
const { chromium } = require('./плейрайт.js');

const put = process.argv[2] ||
  'Проект/База данных/5 класс/История/видеоуроки.html';
const kuda = 'Временные/снимки';
fs.mkdirSync(kuda, { recursive: true });

async function razdeliteli(p, panel) {
  return p.evaluate((sel) => {
    const kor = document.querySelector(sel);
    const najdeno = [];
    kor.querySelectorAll('*').forEach(el => {
      const s = getComputedStyle(el);
      const linii = [];
      if (parseFloat(s.borderBottomWidth) > 0 && s.borderBottomStyle !== 'none')
        linii.push('низ ' + s.borderBottomWidth + ' ' + s.borderBottomColor);
      if (parseFloat(s.borderTopWidth) > 0 && s.borderTopStyle !== 'none')
        linii.push('верх ' + s.borderTopWidth + ' ' + s.borderTopColor);
      if (s.backgroundColor && s.backgroundColor !== 'rgba(0, 0, 0, 0)' &&
          !/o[kl]/.test(s.backgroundColor.replace(/[^a-z()]/g, '')))
        linii.push('фон ' + s.backgroundColor);
      if (linii.length)
        najdeno.push({ klass: el.className || el.tagName,
                       ot: Math.round(el.getBoundingClientRect().top),
                       linii: linii.join(' | ') });
    });
    return najdeno.slice(0, 14);
  }, panel);
}

async function krestik(p, panel, krest) {
  return p.evaluate(([sel, kr]) => {
    const a = document.querySelector(sel + ' ' + kr);
    const s = getComputedStyle(a);
    return { razmer: a.getBoundingClientRect().width + '×' +
                     a.getBoundingClientRect().height,
             ramka: s.borderTopWidth + ' ' + s.borderTopColor,
             fon: s.backgroundColor, kraska: s.color };
  }, [panel, krest]);
}

(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1440, height: 1000 } });
  // Имя и цель как с главного экрана: их пишет он же, в ту же память.
  await p.addInitScript(() => {
    try {
      localStorage.setItem('shkola.imya', 'Полина');
      localStorage.setItem('shkola.tsel', 'стать врачом');
    } catch (e) {}
  });
  await p.goto('file://' + path.resolve(put), { waitUntil: 'load' });
  await p.waitForTimeout(900);

  const stroka = await p.evaluate(() => {
    const s = document.getElementById('imya-stroka');
    const t = document.querySelector('.kniga-stroka');
    return { est: !!s, tekst: s ? s.textContent : '', skryta: s ? s.hidden : null,
             nad_knigoy: s && t ? s.getBoundingClientRect().bottom <=
                                  t.getBoundingClientRect().top + 2 : null,
             razmer: s ? getComputedStyle(s).fontSize : '' };
  });
  console.log('=== строка с именем и целью');
  console.log('  ' + JSON.stringify(stroka));

  // --- меню боковое
  await p.evaluate(() => window.shkMenu());
  await p.waitForTimeout(700);
  console.log('=== боковое меню');
  console.log('  крестик (обычный):', JSON.stringify(await krestik(p, '#panel', '.panel-zakryt')));
  await p.hover('#panel .panel-zakryt');
  await p.waitForTimeout(250);
  console.log('  крестик (наведён):', JSON.stringify(await krestik(p, '#panel', '.panel-zakryt')));
  console.log('  линии и фоны:');
  for (const l of await razdeliteli(p, '#panel')) console.log('    ', JSON.stringify(l));
  await p.screenshot({ path: path.join(kuda, 'меню-боковое.png') });

  // --- панель плейлиста
  await p.evaluate(() => window.shkPleylistTog());
  await p.waitForTimeout(700);
  console.log('=== панель плейлиста');
  console.log('  крестик (обычный):', JSON.stringify(await krestik(p, '#pleylist-panel', '.panel-zakryt')));
  await p.hover('#pleylist-panel .panel-zakryt');
  await p.waitForTimeout(250);
  console.log('  крестик (наведён):', JSON.stringify(await krestik(p, '#pleylist-panel', '.panel-zakryt')));
  console.log('  линии и фоны:');
  for (const l of await razdeliteli(p, '#pleylist-panel')) console.log('    ', JSON.stringify(l));
  await p.screenshot({ path: path.join(kuda, 'меню-плейлист.png') });

  // --- пункты под кадром: чем выделены
  console.log('=== пункты под кадром');
  await p.evaluate(() => window.shkPleylist(false));
  await p.waitForTimeout(500);
  const karta3 = await p.evaluate(() => {
    window.shkBannerGde && window.shkBannerGde('');
    return { tretiya: !!document.getElementById('vybor-tretiya') };
  });
  console.log('=== кнопка «Закрыть» на уведомлении');
  console.log('  есть в разметке:', karta3.tretiya);

  const punkty = await p.evaluate(() => {
    const a = document.querySelector('.pl-telo a.trek');
    const sum = document.querySelector('summary.pl-imya');
    const aktiv = document.querySelector('.pl-blok.aktiven > summary.pl-imya');
    const chitat = el => {
      const s = getComputedStyle(el);
      return { fon: s.backgroundColor, ramka: s.borderLeftWidth + ' ' +
               s.borderLeftColor, kraska: s.color,
               kontur: s.outlineWidth + ' ' + s.outlineColor };
    };
    return { punkt: chitat(a), imya: chitat(sum),
             imya_aktiv: aktiv ? chitat(aktiv) : null,
             nomer: chitat(document.querySelector('.trek-nomer')) };
  });
  console.log('  ' + JSON.stringify(punkty, null, 1).replace(/\n/g, '\n  '));
  await p.screenshot({ path: path.join(kuda, 'меню-под-кадром.png'), fullPage: true });
  await b.close();
})();
