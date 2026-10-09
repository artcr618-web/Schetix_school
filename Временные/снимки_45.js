// Снимки 45-х правок: как стало сейчас, а не «как было».
//
//   node Временные/снимки_45.js
//
// Четыре снимка в Временные/снимки/:
//   45-под-видео.png      список плейлистов под кадром (5 класс, история)
//   45-обложки.png        строка учебника и обложки на странице предмета
//   45-обложка-клик.png   увеличенная обложка по клику
//   45-номер-текст.png    строки панели: номер параграфа и текст
const path = require('path');
const { chromium } = require('./плейрайт.js');

const kuda = 'Временные/снимки';
const stranica = 'Проект/База данных/HTML/5 класс/История/видеоуроки.html';
const predmet = 'Проект/База данных/HTML/5 класс/История.html';

(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1440, height: 1000 } });

  // 1. Под кадром: строки плейлистов.
  await p.goto('file://' + path.resolve(stranica), { waitUntil: 'load' });
  await p.waitForTimeout(1200);
  // Прокрутка может быть плавной, поэтому положение списка меряем
  // ПОСЛЕ неё — иначе снимок уезжает на кадр выше.
  await p.evaluate(() => {
    const r = document.querySelector('.pl-vse').getBoundingClientRect();
    window.scrollTo(0, Math.max(0, r.top + window.scrollY - 120));
  });
  await p.waitForTimeout(600);
  const kadr = await p.evaluate(() => {
    const r = document.querySelector('.pl-vse').getBoundingClientRect();
    return { h: Math.round(r.height), top: Math.round(r.top),
             strok: document.querySelectorAll('.pl-vse a.pl-plitka').length };
  });
  await p.screenshot({ path: `${kuda}/45-под-видео.png`,
                       clip: { x: 0, y: Math.max(0, kadr.top - 20), width: 1000,
                               height: Math.min(980, kadr.h + 60) } });
  console.log('45-под-видео.png — строк:', kadr.strok, 'высота списка', kadr.h,
              'верх списка на экране', kadr.top);

  // 2. Строка учебника и обложки на странице предмета.
  // Карточка учебника живёт внутри раскрывающегося списка: у закрытой
  // обложки нулевой высоты, и снимать нечего.
  await p.goto('file://' + path.resolve(predmet), { waitUntil: 'load' });
  await p.waitForTimeout(800);
  await p.evaluate(() => {
    const d = document.querySelector('details.kniga-stroka');
    if (d && !d.open) d.querySelector('summary').click();
  });
  await p.waitForTimeout(600);
  await p.evaluate(async () => {
    await Promise.all([...document.querySelectorAll('.kn-kartochka img')]
      .map(im => im.decode().catch(() => {})));
  });
  const karty = await p.evaluate(() => {
    const k = document.querySelector('.kn-kartochka');
    const r = k.getBoundingClientRect();
    window.scrollTo(0, Math.max(0, r.top + window.scrollY - 120));
    return { imya: k.querySelector('.kn-knazv') && k.querySelector('.kn-knazv').textContent.trim(),
             oblozhka: k.querySelector('img') &&
               [Math.round(k.querySelector('img').getBoundingClientRect().width),
                Math.round(k.querySelector('img').getBoundingClientRect().height)] };
  });
  await p.waitForTimeout(300);
  await p.screenshot({ path: `${kuda}/45-обложки.png`,
                       clip: { x: 0, y: 0, width: 1000, height: 700 } });
  console.log('45-обложки.png —', karty.imya, karty.oblozhka.join('x'));

  // 3. Клик по обложке: она увеличивается.
  await p.evaluate(() => {
    const a = document.querySelector('.kn-oblozhka');
    if (a) a.click();
  });
  await p.waitForTimeout(800);
  await p.evaluate(async () => {
    const okno = document.querySelector('#shk-oblozhka');
    const im = okno && okno.querySelector('img');
    if (im) await im.decode().catch(() => {});
  });
  const klik = await p.evaluate(() => {
    const okno = document.querySelector('#shk-oblozhka');
    if (!okno) return null;
    const im = okno.querySelector('img');
    return { otkryto: !okno.hidden,
             razmer: im ? [Math.round(im.getBoundingClientRect().width),
                           Math.round(im.getBoundingClientRect().height)] : null };
  });
  await p.screenshot({ path: `${kuda}/45-обложка-клик.png`,
                       clip: { x: 0, y: 0, width: 1440, height: 900 } });
  console.log('45-обложка-клик.png — открыто:', klik && klik.otkryto,
              'размер увеличенной:', klik && klik.razmer && klik.razmer.join('x'));
  await p.keyboard.press('Escape');
  await p.waitForTimeout(200);

  // 4. Строки панели: номер параграфа и текст рядом.
  await p.goto('file://' + path.resolve(stranica), { waitUntil: 'load' });
  await p.waitForTimeout(1200);
  await p.evaluate(() => { if (window.shkNabor) window.shkNabor(1); });
  await p.waitForTimeout(700);
  const panel = await p.evaluate(() => {
    // Строка главы без номера: берём первую, у которой номер есть.
    // И только видимую: у закрытых плейлистов прямоугольники нулевые.
    const t = [...document.querySelectorAll('#pleylist-panel a.trek')]
      .find(a => a.querySelector('.trek-nomer') && a.querySelector('.trek-tema') &&
                 a.getBoundingClientRect().width > 0);
    if (!t) return null;
    const nom = t.querySelector('.trek-nomer'), tema = t.querySelector('.trek-tema');
    return { zazor: Math.round(tema.getBoundingClientRect().left -
                               nom.getBoundingClientRect().right),
             kolonka: Math.round(nom.getBoundingClientRect().width),
             strok: document.querySelectorAll('#pleylist-panel a.trek').length };
  });
  await p.waitForTimeout(500);
  await p.screenshot({ path: `${kuda}/45-номер-текст.png`,
                       clip: { x: 1440 - 480, y: 0, width: 480, height: 620 } });
  console.log('45-номер-текст.png — зазор', panel && panel.zazor,
              'колонка номера', panel && panel.kolonka,
              'строк в панели', panel && panel.strok);

  // 5. Два учебника подряд: раньше обложки втыкались друг в друга,
  // теперь между карточками воздух.
  await p.goto('file://' + path.resolve('Проект/База данных/HTML/7 класс/История.html'),
               { waitUntil: 'load' });
  await p.waitForTimeout(700);
  await p.evaluate(() => {
    const d = document.querySelector('details.kniga-stroka');
    if (d && !d.open) d.querySelector('summary').click();
  });
  await p.waitForTimeout(600);
  await p.evaluate(async () => {
    await Promise.all([...document.querySelectorAll('.kn-kartochka img')]
      .map(im => im.decode().catch(() => {})));
  });
  const dva = await p.evaluate(() => {
    const k = [...document.querySelectorAll('.kn-kartochka')];
    const r = k.map(x => x.getBoundingClientRect());
    window.scrollTo(0, Math.max(0, r[0].top + window.scrollY - 140));
    return { kartochek: k.length,
             vozduh: r.length > 1 ? Math.round(r[1].top - r[0].bottom) : null };
  });
  await p.waitForTimeout(400);
  await p.screenshot({ path: `${kuda}/45-два-учебника.png`,
                       clip: { x: 0, y: 0, width: 1000, height: 620 } });
  console.log('45-два-учебника.png — карточек:', dva.kartochek,
              'воздух между ними:', dva.vozduh, 'px');

  await b.close();
})();
