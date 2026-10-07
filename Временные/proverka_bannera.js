// Баннер лекций на странице предмета: меряем ширину и воздух, проверяем
// переключение подборок и то, что лекция играет внутри самой страницы.
//
//   node Временные/proverka_bannera.js "Проект/База данных/7 класс/История.html"
const fs = require('fs');
const path = require('path');
const { chromium } = require('./плейрайт.js');

const put = process.argv[2] || 'Проект/База данных/7 класс/История.html';
/* Ожидания берём из тех же данных, по которым собран баннер: иначе
   проверка одного баннера судит другой — слова про Мединского и
   седьмой класс ничего не говорят о баннере пятого.

     node Временные/proverka_bannera.js "<страница>" <файл данных> */
const fayl_dannyh = process.argv[3] || 'Временные/banner_istoriya_7.json';
const dannyh = JSON.parse(fs.readFileSync(fayl_dannyh, 'utf8'));
const zhdyom = {
  nazvanie: (dannyh['заголовок'] || '').trim(),
  podpis: (dannyh['подзаголовок'] || '').trim(),
  punktov: dannyh['подборки'].map(p => p['видео'].length),
};
const kuda = 'Временные/снимки';
fs.mkdirSync(kuda, { recursive: true });
const imya = path.basename(put, '.html') + '-баннер';
let oshibki = 0;
const proverka = (chto, uslovie, fakticheski) => {
  console.log((uslovie ? '  ок   ' : '  ОШИБКА ') + chto +
    (uslovie ? '' : ' → ' + JSON.stringify(fakticheski)));
  if (!uslovie) oshibki++;
};

(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1440, height: 1000 } });
  const osh = [];
  p.on('pageerror', e => osh.push(String(e).slice(0, 120)));
  await p.goto('file://' + path.resolve(put), { waitUntil: 'load' });
  await p.waitForTimeout(1200);

  const razmery = await p.evaluate(() => {
    const bann = document.querySelector('.banner');
    const setka = document.querySelector('.setka');
    const plitka = document.querySelector('a.plitka');
    const kniga = document.querySelector('.kniga-stroka');
    const wrap = document.querySelector('.wrap');
    const st = getComputedStyle(setka);
    return {
      est: !!bann,
      shirina_bannera: bann ? Math.round(bann.getBoundingClientRect().width) : 0,
      shirina_stranicy: Math.round(setka.getBoundingClientRect().width),
      shirina_okna: Math.round(wrap.getBoundingClientRect().width),
      mezhdu_plitkami: st.gap || st.columnGap,
      ot_bannera_do_plitok: Math.round(
        setka.getBoundingClientRect().top - bann.getBoundingClientRect().bottom),
      ot_knigi_do_bannera: Math.round(
        bann.getBoundingClientRect().top - kniga.getBoundingClientRect().bottom),
      vysok_pl_: Math.round(plitka.getBoundingClientRect().height),
      nazvanie: (document.querySelector('.banner-nazv') || {}).textContent || '',
      podpis: (document.querySelector('.banner-podpis') || {}).textContent || '',
      knopok: document.querySelectorAll('.banner-knopka').length,
      punktov: [...document.querySelectorAll('.banner-nabor')].map(o => o.children.length),
      kadr_do: !!document.querySelector('#banner-mesto iframe'),
      vopros: (document.querySelector('#pleyer-zag') || {}).textContent || '',
      kartochka: !!document.querySelector('.vybor-karta'),
      panel: !!document.querySelector('#pleylist-panel'),
      knopka_pleylista: !!document.querySelector('.pleyer-knopka'),
    };
  });

  console.log('страница: ' + put);
  proverka('баннер есть', razmery.est);
  proverka('баннер во всю ширину страницы',
           razmery.shirina_bannera === razmery.shirina_stranicy,
           [razmery.shirina_bannera, razmery.shirina_stranicy]);
  proverka('заголовок баннера — как в данных',
           razmery.nazvanie.trim() === zhdyom.nazvanie,
           [razmery.nazvanie.trim(), zhdyom.nazvanie]);
  proverka('подпись под заголовком — как в данных',
           razmery.podpis.trim() === zhdyom.podpis,
           [razmery.podpis.trim(), zhdyom.podpis]);
  proverka('в баннере столько подборок, сколько в данных',
           razmery.knopok === zhdyom.punktov.length,
           [razmery.knopok, zhdyom.punktov.length]);
  proverka('в подборках столько лекций, сколько в данных',
           JSON.stringify(razmery.punktov) === JSON.stringify(zhdyom.punktov),
           [razmery.punktov, zhdyom.punktov]);
  proverka('баннер выше плиток и ниже учебника',
           razmery.ot_knigi_do_bannera > 0, razmery.ot_knigi_do_bannera);
  proverka('до плиток воздух больше, чем между плитками',
           razmery.ot_bannera_do_plitok > parseFloat(razmery.mezhdu_plitkami),
           [razmery.ot_bannera_do_plitok, razmery.mezhdu_plitkami]);
  proverka('пока не нажали — кадра нет',
           razmery.kadr_do === false, razmery.kadr_do);
  proverka('на странице предмета нет большого плеера и панели плейлиста',
           !razmery.panel && !razmery.knopka_pleylista,
           [razmery.panel, razmery.knopka_pleylista]);

  await p.screenshot({ path: path.join(kuda, imya + '.png'), fullPage: false });

  // --- нажимаем лекцию во ВТОРОЙ подборке: должна играть здесь же
  await p.evaluate(() => window.shkBanner(1));
  await p.waitForTimeout(300);
  const vtoraya = await p.evaluate(() => {
    const o = document.querySelectorAll('.banner-nabor');
    return {
      skryt_pervyy: o[0].hasAttribute('hidden'),
      otkryt_vtoroy: !o[1].hasAttribute('hidden'),
      aktivnyy: (document.querySelector('.banner-knopka.aktiven') || {}).textContent,
    };
  });
  proverka('первая подборка спряталась, вторая открылась',
           vtoraya.skryt_pervyy && vtoraya.otkryt_vtoroy, vtoraya);

  await p.evaluate(() => {
    const a = document.querySelectorAll('.banner-nabor')[1].querySelector('.banner-trek');
    window.shkIgrat(a);
  });
  await p.waitForTimeout(2500);
  const igraet = await p.evaluate(() => {
    const ram = document.querySelector('#banner-mesto iframe');
    const telo = document.body;
    return {
      kadr: !!ram,
      adres: ram ? ram.getAttribute('src') : '',
      vnutri: ram ? ram.parentNode.id : '',
      klassy: ram ? ram.className : '',
      nakladka: !!document.querySelector('.vybor-karta') &&
                getComputedStyle(document.querySelector('.vybor-karta')).display,
      aktivnyh: document.querySelectorAll('.banner-trek.aktiven').length,
      kadr_shirina: ram ? Math.round(ram.getBoundingClientRect().width) : 0,
      kadr_vysota: ram ? Math.round(ram.getBoundingClientRect().height) : 0,
      mesto_shirina: Math.round(document.querySelector('.banner-mesto')
        .getBoundingClientRect().width),
      zashchita: document.querySelectorAll('#pleyer').length,
      body_klass: telo.className,
    };
  });
  proverka('кадр появился в самом баннере',
           igraet.kadr && igraet.vnutri === 'banner-mesto', igraet);
  proverka('в кадре адрес встраивания Rutube',
           /^https:\/\/rutube\.ru\/play\/embed\/[0-9a-f]{32}\/$/.test(igraet.adres),
           igraet.adres);
  proverka('подсвечена одна лекция', igraet.aktivnyh === 1, igraet.aktivnyh);
  // Абсолютный кадр в баннере когда-то накрывал собой всю страницу:
  // сверху чернел экран, а нажатия по списку лекций доставались кадру.
  proverka('кадр в баннере занимает своё место, а не всю страницу',
           Math.abs(igraet.kadr_shirina - igraet.mesto_shirina) <= 2 &&
           Math.abs(igraet.kadr_vysota - igraet.mesto_shirina * 9 / 16) <= 3,
           igraet);
  proverka('карточки возврата на странице предмета нет',
           !igraet.nakladka || igraet.nakladka === 'none', igraet.nakladka);
  proverka('большого плеера на странице не появилось',
           igraet.zashchita === 0, igraet.zashchita);

  await p.screenshot({ path: path.join(kuda, imya + '-играет.png'), fullPage: false });

  // --- перезагрузка: лекция снова в кадре, но на паузе
  await p.reload({ waitUntil: 'load' });
  await p.waitForTimeout(2500);
  const posle = await p.evaluate(() => {
    const o = document.querySelectorAll('.banner-nabor');
    return {
      kadr: !!document.querySelector('#banner-mesto iframe'),
      otkryta_vtoraya: !o[1].hasAttribute('hidden'),
      aktivnyh: document.querySelectorAll('.banner-trek.aktiven').length,
    };
  });
  proverka('после возврата лекция снова в кадре', posle.kadr, posle);
  proverka('открылась та подборка, где лежит лекция', posle.otkryta_vtoraya, posle);
  proverka('она же подсвечена', posle.aktivnyh === 1, posle.aktivnyh);

  // --- строки лекций: тот же стандарт, что у списков под кадром
  // Кадр в баннере появляется после возврата и меняет высоту страницы,
  // поэтому перед каждым наведением прокручиваем заново и убеждаемся,
  // что точка наведения правда внутри окна, а под курсором — строка.
  const otkr_stroka = () => p.evaluate(() => {
    document.querySelectorAll('[data-proverka-kursor]').forEach(e =>
      e.removeAttribute('data-proverka-kursor'));
    const listy = [...document.querySelectorAll('.banner-nabor')];
    const odkryt = listy.find(l => !l.hasAttribute('hidden')) || listy[0];
    const a = odkryt.querySelector('.banner-trek:not(.aktiven)') ||
              odkryt.querySelector('.banner-trek');
    a.setAttribute('data-proverka-kursor', '1');
    window.scrollTo(0, Math.round(
      a.getBoundingClientRect().top + scrollY - innerHeight / 2));
    return true;
  });
  const tochka = () => p.evaluate(() => {
    const a = document.querySelector('[data-proverka-kursor]');
    if (!a) return { vnutri: false, chto: 'строки нет' };
    const k = a.getBoundingClientRect();
    const x = Math.round(k.left + k.width / 2);
    const y = Math.round(k.top + k.height / 2);
    const el = document.elementFromPoint(x, y);
    return {
      x: x, y: y,
      vnutri: x > 0 && y > 0 && x < innerWidth && y < innerHeight,
      pod: el ? (el.className || el.tagName) : 'ничего',
      est: !!el && !!el.closest && el.closest('.banner-trek') === a,
      cvet: getComputedStyle(a).color,
      vremya_aktivnoy: [...document.querySelectorAll(
        '.banner-trek.aktiven .bt-vremya')].map(e => getComputedStyle(e).color),
    };
  });
  const rgb = t => (t.match(/\d+/g) || []).map(Number);

  let na = { est: false, chto: 'не наводили' };
  for (let popytka = 0; popytka < 4 && !na.est; popytka++) {
    await otkr_stroka();
    await p.waitForTimeout(200);
    const t = await tochka();
    if (!t.vnutri) continue;
    await p.mouse.move(t.x, t.y);
    await p.waitForTimeout(250);
    na = await tochka();
  }
  proverka('курсор действительно на строке лекции', na.est,
           na.pod + ' | ' + JSON.stringify({ x: na.x, y: na.y, vnutri: na.vnutri }));

  await p.mouse.move(4, 4);
  await p.waitForTimeout(250);
  const bez = await tochka();
  proverka('строка лекции в покое без подложки, рамки и обводки',
           await p.evaluate(() => {
             const a = document.querySelector('[data-proverka-kursor]');
             const c = getComputedStyle(a);
             return (c.backgroundColor === 'rgba(0, 0, 0, 0)' ||
                     c.backgroundColor === 'transparent') &&
                    (c.borderTopWidth === '0px' && c.borderLeftWidth === '0px') &&
                    c.outlineStyle === 'none';
           }));
  proverka('строка лекции не синяя',
           rgb(bez.cvet)[2] - rgb(bez.cvet)[0] < 40, bez.cvet);
  proverka('время активной лекции не жёлтое',
           bez.vremya_aktivnoy.every(c => rgb(c)[0] <= rgb(c)[2]),
           bez.vremya_aktivnoy);
  proverka('наведение делает строку чуть ярче', na.cvet !== bez.cvet,
           na.cvet + ' / ' + bez.cvet);
  proverka('наведение — жёлтого оттенка не появляется',
           rgb(na.cvet)[0] <= rgb(na.cvet)[2], na.cvet);
  await p.evaluate(() => {
    document.querySelectorAll('[data-proverka-kursor]').forEach(e =>
      e.removeAttribute('data-proverka-kursor'));
  });

  console.log('ошибки на странице:', osh.length ? osh.join(' | ') : 'нет');
  console.log('\nИтог: ошибок ' + oshibki);
  await b.close();
  process.exit(oshibki ? 1 : 0);
})();
