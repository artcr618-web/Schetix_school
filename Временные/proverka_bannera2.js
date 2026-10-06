// Карточка возврата и строка с именем на всех видах страниц.
const { chromium } = require('./плейрайт.js');
const path = require('path');
const stranicy = [
  'Проект/Начать учиться.html',
  'Проект/База данных/5 класс.html',
  'Проект/База данных/5 класс/История.html',
  'Проект/База данных/5 класс/История/видеоуроки.html',
  'Проект/База данных/7 класс/История.html',
  'Проект/База данных/8 класс/Геометрия/тренажёры.html',
];
(async () => {
  const b = await chromium.launch();
  for (const f of stranicy) {
    const p = await b.newPage({ viewport: { width: 1440, height: 950 } });
    await p.addInitScript(() => {
      try {
        localStorage.setItem('shkola.imya', 'Полина');
        localStorage.setItem('shkola.tsel', 'стать врачом');
      } catch (e) {}
    });
    await p.goto('file://' + path.resolve(f), { waitUntil: 'load' });
    await p.waitForTimeout(900);
    const t = await p.evaluate(() => {
      const s = document.getElementById('imya-stroka');
      const put = document.querySelector('.put-stroka');
      const kn = document.querySelector('.kniga-stroka');
      return {
        stroka: s ? s.textContent : 'нет',
        skryta: s ? s.hidden : null,
        mezhdu_putem_i_knigoy: (s && put && kn)
          ? (s.getBoundingClientRect().top >= put.getBoundingClientRect().bottom - 1 &&
             s.getBoundingClientRect().bottom <= kn.getBoundingClientRect().top + 2)
          : null,
        bolshoy_zag: !!document.querySelector('h1'),
      };
    });
    console.log(`${t.skryta ? 'СКРЫТА' : 'ок    '} ${f.replace('Проект/', '')}  «${t.stroka}»  между путём и учебником: ${t.mezhdu_putem_i_knigoy}`);
    await p.close();
  }
  // --- уведомление «Вы остановились на параграфе…»: оно должно быть
  // ВИДНО, а не просто лежать в разметке. Однажды карточка оказалась
  // под кадром: стиль показывал block, а на экране её не было.
  const p = await b.newPage({ viewport: { width: 1440, height: 950 } });
  await p.goto('file://' + path.resolve('Проект/База данных/5 класс/История/видеоуроки.html'), { waitUntil: 'load' });
  await p.waitForTimeout(900);
  await p.evaluate(() => document.querySelectorAll('.trek')[2].click());
  await p.waitForTimeout(1200);
  await p.reload({ waitUntil: 'load' });
  await p.waitForTimeout(2200);
  const uvidomlenie = await p.evaluate(() => {
    const v = document.getElementById('pleyer-vybor');
    const t = document.getElementById('vybor-tekst');
    const knopki = [...document.querySelectorAll('.pleyer-vybor a')].map(a => {
      const r = a.getBoundingClientRect();
      const el = document.elementFromPoint(Math.round(r.left + r.width / 2),
                                           Math.round(r.top + r.height / 2));
      return { imya: a.textContent.trim(),
               sverkhu: !!el && (el === a || a.contains(el)) };
    });
    if (!v || getComputedStyle(v).display === 'none') {
      return { est: false, tekst: '', knopki: [] };
    }
    const k = v.getBoundingClientRect();
    const el = document.elementFromPoint(Math.round(k.left + k.width / 2),
                                         Math.round(k.top + k.height / 2));
    return {
      est: !!el && !!el.closest && !!el.closest('.pleyer-vybor'),
      tekst: t ? t.textContent : '',
      knopki: knopki,
      vnutri_okna: k.top < innerHeight && k.bottom > 0,
    };
  });
  console.log('\nуведомление о продолжении: ' + (uvidomlenie.est ? 'видно — ок'
    : 'ОШИБКА: не видно') + '  «' + uvidomlenie.tekst + '»');
  console.log('  в окне без прокрутки: ' + (uvidomlenie.vnutri_okna ? 'да' : 'ОШИБКА: нет'));
  uvidomlenie.knopki.forEach(k => console.log('  кнопка «' + k.imya + '»: ' +
    (k.sverkhu ? 'наверху — ок' : 'ОШИБКА: перекрыта')));
  if (!uvidomlenie.knopki.some(k => k.imya === 'Закрыть' && k.sverkhu)) {
    console.log('  ОШИБКА: кнопки «Закрыть» не видно');
  }
  await p.screenshot({ path: 'Временные/снимки/возврат.png' });
  const do_klika = await p.evaluate(() => {
    // Прячется вся карточка целиком — обёртка #pleyer-vybor, а не
    // внутренний блок: иначе текст и кнопки остались бы висеть.
    const v = document.getElementById('pleyer-vybor');
    v.style.display = '';
    window.shkZakrytKartu();
    return getComputedStyle(v).display;
  });
  console.log('\nкарточка после «Закрыть»:', do_klika === 'none' ? 'скрыта — ок' : 'ОШИБКА: ' + do_klika);
  const kadr = await p.evaluate(() => !!document.getElementById('ramka'));
  console.log('кадр остался:', kadr ? 'да' : 'ОШИБКА: пропал');
  await b.close();
})();
