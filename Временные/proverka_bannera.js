// Баннер лекций на странице предмета: меряем ширину и воздух, проверяем
// переключение подборок и то, что лекция играет внутри самой страницы.
//
//   node Временные/proverka_bannera.js "Проект/База данных/7 класс/История.html"
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const put = process.argv[2] || 'Проект/База данных/7 класс/История.html';
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
  proverka('заголовок баннера — про Мединского и седьмой класс',
           /Мединский/.test(razmery.nazvanie) && /седьмой класс/.test(razmery.nazvanie),
           razmery.nazvanie);
  proverka('подпись под заголовком', !!razmery.podpis, razmery.podpis);
  proverka('в баннере две подборки', razmery.knopok === 2, razmery.knopok);
  proverka('в подборках 4 и 6 лекций',
           razmery.punktov[0] === 4 && razmery.punktov[1] === 6, razmery.punktov);
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

  console.log('ошибки на странице:', osh.length ? osh.join(' | ') : 'нет');
  console.log('\nИтог: ошибок ' + oshibki);
  await b.close();
  process.exit(oshibki ? 1 : 0);
})();
