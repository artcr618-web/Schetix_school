// Знак «Лекции» на странице предмета и сама страница лекций.
//
// Знак — не сцена, а дверь: он ничего не играет, лекции не перечисляет
// и говорит только о разделах. Поэтому проверяем и знак (слова, ширина,
// воздух, адрес, подсветка при наведении), и то, что за дверью: страница
// лекций должна быть устроена как страница кино — кадр, подборки под
// кадром, панель справа, — но со своими словами.
//
// Ожидания берём из файла данных того же баннера: он один и для знака,
// и для страницы лекций, поэтому разойтись им нечем.
//
//   node Временные/proverka_lekciy.js
//   node Временные/proverka_lekciy.js "<страница предмета>" "<страница лекций>" <файл данных>
const fs = require('fs');
const path = require('path');
const { chromium } = require('./плейрайт.js');

// Высота знака в долях от плашки — число из той же таблицы, по которой
// собрана раскладка (Инструменты/разметка.py → Временные/разметка.json).
// 1.56 = 1.04 (прежние «выше плашки на 30 %») × 1.5 — «полторы высоты
// плашки».
const razmetka = JSON.parse(fs.readFileSync('Временные/разметка.json', 'utf8'));
const ZNAK_DOLYA = razmetka.znak_dolya || 1.56;

const stranica = process.argv[2] ||
  'Проект/База данных/HTML/7 класс/История.html';
const stranica_lekciy = process.argv[3] ||
  'Проект/База данных/HTML/7 класс/История/лекции.html';
const fayl_dannyh = process.argv[4] || 'Временные/banner_istoriya_7.json';

const dannyh = JSON.parse(fs.readFileSync(fayl_dannyh, 'utf8'));
const nazvanie = (dannyh['заголовок'] || '').trim();
const podpis = (dannyh['подзаголовок'] || '').trim();
// Рисунок знака — свой, про лекции (см. FONY_LEKCIY в gen_tv_paket.py):
// знак стоит в ряду плашек и выглядит как они, но картинка у него своя.
const kartinka = 'Фоны/История-лекции.jpg';
const razdely = dannyh['подборки'].map(p => p['имя']);
const po_razdelam = dannyh['подборки'].map(p => p['видео'].length);
const vsego = po_razdelam.reduce((s, n) => s + n, 0);
const syrye_temy = [].concat(...dannyh['подборки'].map(p =>
  p['видео'].map(v => v[0])));
const pervyy_kod = dannyh['подборки'][0]['видео'][0][1];
const vtoroy_kod = dannyh['подборки'][1]['видео'][0][1];

let oshibki = 0;
const proverka = (chto, uslovie, fakticheski) => {
  console.log((uslovie ? '  ок   ' : '  ОШИБКА ') + chto +
    (uslovie ? '' : ' → ' + JSON.stringify(fakticheski)));
  if (!uslovie) oshibki++;
};
// Мягкие дефисы в тексте глазом не видны, но сравнивать мешают.
const bez_myagkih = s => String(s || '').replace(/\u00ad/g, '');
const bez_ya = s => bez_myagkih(s).replace(/\s+/g, ' ').trim();
// Длинное тире вплотную страница переводит в короткое с пробелами
// (правило сборки, Инструменты/_tv.py): «1610—1612» → «1610 – 1612».
// Ожидания из файла данных проходят ту же замену, иначе сверка ловит
// не ошибку страницы, а само правило.
const po_tire = s => String(s)
  .replace(/(?<=[\wА-Яа-яЁё])[—–](?=[\wА-Яа-яЁё])/g, ' \u2013 ');
const temy = syrye_temy.map(po_tire);

(async () => {
  const b = await chromium.launch();

  // ---------- 1. знак на странице предмета ----------
  console.log('знак: ' + stranica);
  const p = await b.newPage({ viewport: { width: 1440, height: 1000 } });
  const osh = [];
  p.on('pageerror', e => osh.push(String(e).slice(0, 120)));
  await p.goto('file://' + path.resolve(stranica), { waitUntil: 'load' });
  await p.waitForTimeout(1000);

  const z = await p.evaluate(() => {
    const znak = document.querySelector('.banner-znak');
    const setka = document.querySelector('.setka');
    const stil = setka ? getComputedStyle(setka) : {};
    return {
      est: !!znak,
      skolko: document.querySelectorAll('.banner-znak').length,
      adres: znak ? znak.getAttribute('href') : '',
      nazvanie: znak ? (znak.querySelector('.nazv') || {}).textContent : '',
      podpis: znak ? (znak.querySelector('.poyas') || {}).textContent : '',
      stroka: znak ? (znak.querySelector('.bzn-razdely') || {}).textContent : '',
      knopka: znak ? (znak.querySelector('.bzn-knopka') || {}).textContent : '',
      // Знак — та же плашка: сравниваем шрифт и поля с плашкой рядом.
      stil_znaka: (() => {
        if (!znak) return null;
        const pl = document.querySelector('a.plitka');
        const s = getComputedStyle(znak);
        const n = getComputedStyle(znak.querySelector('.nazv'));
        const p = pl ? getComputedStyle(pl.querySelector('.nazv')) : null;
        return { otstup: s.paddingLeft, polosa: s.getPropertyValue('--polosa').trim(),
                 radius: s.getPropertyValue('--radius').trim(),
                 shrift: n.fontSize, shrift_plitki: p ? p.fontSize : '',
                 tolshchina: n.fontWeight, tolshchina_plitki: p ? p.fontWeight : '' };
      })(),
      vysota_znaka: znak ? Math.round(znak.getBoundingClientRect().height) : 0,
      vysota_plitki: (() => {
        const pl = document.querySelector('.plitka');
        return pl ? Math.round(pl.getBoundingClientRect().height) : 0;
      })(),
      kartinka: znak ? getComputedStyle(znak).getPropertyValue('--kartinka')
        .trim() : '',
      ves_tekst: znak ? znak.textContent : '',
      ramka: znak ? getComputedStyle(znak).borderTopColor : '',
      shirina_znaka: znak ? Math.round(znak.getBoundingClientRect().width) : 0,
      shirina_stranicy: setka ? Math.round(setka.getBoundingClientRect().width) : 0,
      vozduh_do_plitok: (znak && setka) ? Math.round(
        setka.getBoundingClientRect().top - znak.getBoundingClientRect().bottom) : 0,
      mezhdu_plitkami: parseInt(stil.gap || stil.columnGap || '0', 10),
      pleer: !!document.querySelector('#pleyer'),
      panelya: !!document.querySelector('#pleylist-panel'),
      kadr: !!document.querySelector('iframe'),
      kartochka: !!document.querySelector('.vybor-karta'),
    };
  });

  const adres = bez_myagkih(z.adres);
  proverka('знак есть', z.est);
  proverka('знак один', z.skolko === 1, z.skolko);
  proverka('заголовок знака — как в данных', bez_ya(z.nazvanie) === nazvanie,
           z.nazvanie);
  proverka('подпись знака — как в данных', bez_ya(z.podpis) === podpis,
           z.podpis);
  // Отдельной кнопки у знака нет: он сам — кнопка, а вторая цель внутри
  // ссылки только сбивает. Строки про разделы тоже нет — списком они
  // видны на самой странице.
  proverka('кнопки внутри знака нет', !z.knopka, z.knopka);
  proverka('строки про разделы в знаке нет', !bez_ya(z.stroka), z.stroka);
  // Высота: ровно ZNAK_DOLYA от плашки, не на глазок.
  const otnoshenie = z.vysota_plitki ? z.vysota_znaka / z.vysota_plitki : 0;
  proverka('знак выше плашки ровно на ' + Math.round((ZNAK_DOLYA - 1) * 100) + ' %',
           Math.abs(otnoshenie - ZNAK_DOLYA) < 0.01,
           { znak: z.vysota_znaka, plitka: z.vysota_plitki,
             otnoshenie: otnoshenie.toFixed(3) });
  // Знак — та же плашка, только во всю ширину и выше: поля, полоса,
  // скругление и шрифт названия у них одни и те же.
  proverka('у знака плашечные поля, полоса и скругление',
           z.stil_znaka &&
           z.stil_znaka.shrift === z.stil_znaka.shrift_plitki &&
           z.stil_znaka.tolshchina === z.stil_znaka.tolshchina_plitki &&
           /^\d+px$/.test(z.stil_znaka.otstup), z.stil_znaka);
  proverka('рисунок знака — фон предмета',
           bez_ya(z.kartinka).includes(kartinka), z.kartinka);
  proverka('знак во всю ширину страницы',
           Math.abs(z.shirina_znaka - z.shirina_stranicy) <= 4,
           { znak: z.shirina_znaka, stranica: z.shirina_stranicy });
  proverka('до плиток воздух больше, чем между плитками',
           z.vozduh_do_plitok > z.mezhdu_plitkami,
           { vozduh: z.vozduh_do_plitok, mezhdu: z.mezhdu_plitkami });

  // Слова знака — только заголовок и подпись: ни разделов, ни лекций,
  // ни их числа (всё это живёт на самой странице лекций).
  // Строки разметки склеиваются без пробела («Лекции» + «Мединский»),
  // поэтому сравниваем текст без пробелов вовсе.
  const sploshno = s => bez_ya(s).replace(/\s+/g, '');
  proverka('текст знака — заголовок и подпись, и всё',
           sploshno(z.ves_tekst) === sploshno(nazvanie + podpis),
           z.ves_tekst);

  // Куда ведёт знак: путь считаем от самой страницы, а не от корня
  // запуска, — так же, как его видит браузер.
  const kuda = path.resolve(path.dirname(stranica), adres);
  proverka('знак ведёт на страницу лекций',
           kuda === path.resolve(stranica_lekciy),
           path.relative(process.cwd(), kuda));
  proverka('по этому адресу страница есть', fs.existsSync(kuda));

  proverka('на странице предмета нет кадра', !z.kadr);
  proverka('на странице предмета нет плеера', !z.pleer);
  proverka('на странице предмета нет панели плейлиста', !z.panelya);
  proverka('на странице предмета нет карточки возврата', !z.kartochka);

  // Подсветка при наведении: у плиток и у знака она одинаковая —
  // жёлтая рамка. Без неё знак не читается как нажимаемый.
  await p.hover('.banner-znak');
  await p.waitForTimeout(250);
  const ramka_na = await p.evaluate(() =>
    getComputedStyle(document.querySelector('.banner-znak')).borderTopColor);
  proverka('наведение делает рамку знака жёлтой',
           ramka_na !== z.ramka && ramka_na.includes('255, 210, 63'), ramka_na);

  // ---------- 2. сама страница лекций ----------
  console.log('\nстраница лекций: ' + stranica_lekciy);
  const l = await b.newPage({ viewport: { width: 1440, height: 1000 } });
  const oshl = [];
  l.on('pageerror', e => oshl.push(String(e).slice(0, 120)));
  await l.goto('file://' + path.resolve(stranica_lekciy), { waitUntil: 'load' });
  await l.waitForTimeout(1200);

  const str = await l.evaluate(() => ({
    rezhim: document.body.getAttribute('data-rezhim') || '',
    vopros: (document.querySelector('#pleyer-zag') || {}).textContent || '',
    podborok: document.querySelectorAll('.pl-plitka').length,
    imena: [...document.querySelectorAll('.pl-plitka')].map(a => a.textContent),
    panel_otkryta: (document.body.className || '').includes('pleylist-otkryto'),
    pleylisty: [...document.querySelectorAll('.pleylist')].map(pl =>
      [...pl.querySelectorAll('.trek')].map(t => ({
        nomer: t.getAttribute('data-nomer'),
        tema: t.getAttribute('data-tema'),
      }))),
    kadr_do: !!document.querySelector('iframe'),
    kniga: !!document.querySelector('.kniga-stroka'),
  }));

  proverka('страница называет себя страницей лекций',
           str.rezhim === 'лекции', str.rezhim);
  proverka('вопрос в шапке — про лекцию',
           bez_ya(str.vopros) === 'Какую лекцию посмотрим?', str.vopros);
  proverka('страница ничего не запускает сама', !str.kadr_do);
  proverka('строка учебника на месте', str.kniga);
  proverka('плейлист открыт сразу', str.panel_otkryta);
  proverka('под кадром столько подборок, сколько в данных',
           str.podborok === razdely.length, str.podborok);
  proverka('имена подборок — как в данных',
           str.imena.map(bez_ya).join('|') === razdely.join('|'), str.imena);

  str.pleylisty.forEach((treki, i) => {
    const imya = razdely[i] || ('подборка ' + i);
    proverka('в «' + imya + '» столько лекций, сколько в данных',
             treki.length === po_razdelam[i], treki.length);
    proverka('в «' + imya + '» темы — как в данных',
             treki.map(t => bez_ya(t.tema)).join('|') ===
             dannyh['подборки'][i]['видео'].map(v => po_tire(v[0])).join('|'),
             treki.map(t => t.tema));
    proverka('в «' + imya + '» подписи — время, а не параграфы',
             treki.every(t => t.nomer && !t.nomer.startsWith('§')),
             treki.map(t => t.nomer));
  });

  // Нажали лекцию: кадр встаёт на её место, и это тот же ролик, что
  // записан в данных.
  await l.evaluate(() => document.querySelectorAll('.trek')[0].click());
  await l.waitForTimeout(600);
  const igraet = await l.evaluate(() => {
    const r = document.querySelector('iframe');
    return {
      kadr: !!r,
      adres: r ? r.getAttribute('src') : '',
      zag: (document.querySelector('#pleyer-zag') || {}).textContent || '',
      aktivnyh: document.querySelectorAll('.trek.aktiven').length,
    };
  });
  proverka('кадр появился', igraet.kadr);
  proverka('в кадре адрес встраивания Rutube с кодом из данных',
           igraet.adres.includes('/play/embed/' + pervyy_kod + '/'),
           igraet.adres);
  proverka('в шапке — название лекции',
           bez_ya(igraet.zag).includes(bez_ya(temy[0])), igraet.zag);
  proverka('подсвечена ровно одна лекция', igraet.aktivnyh === 1,
           igraet.aktivnyh);

  // Вторая подборка: она в панели, и её лекция тоже играет — иначе
  // «2 раздела» в знаке были бы только словами.
  await l.evaluate(() => document.querySelectorAll('.pl-plitka')[1].click());
  await l.waitForTimeout(300);
  const vtoroy = await l.evaluate(() => ({
    imya_v_shapke: (document.querySelector('#pl-zag') || {}).textContent || '',
    vidny: [...document.querySelectorAll('.pleylist')]
      .map(pl => pl.style.display !== 'none'),
  }));
  proverka('вторая подборка открылась в панели',
           bez_ya(vtoroy.imya_v_shapke) === razdely[1] &&
           vtoroy.vidny.filter(Boolean).length === 1, vtoroy);
  await l.evaluate(() => {
    const otkrytaya = document.querySelector('.pleylist:not([style])') ||
      [...document.querySelectorAll('.pleylist')]
        .find(pl => pl.style.display !== 'none');
    otkrytaya.querySelector('.trek').click();
  });
  await l.waitForTimeout(600);
  const vtoroy_kadr = await l.evaluate(() =>
    (document.querySelector('iframe') || {}).src || '');
  proverka('лекция из второй подборки встала в кадр',
           vtoroy_kadr.includes('/play/embed/' + vtoroy_kod + '/'),
           vtoroy_kadr);

  // Возврат: лекция стоит на паузе, карточка спрашивает про продолжение.
  await l.reload({ waitUntil: 'load' });
  await l.waitForTimeout(1000);
  const vozvrat = await l.evaluate(() => ({
    kartochka: !!document.querySelector('#vybor-karta'),
    vidna: (document.querySelector('#vybor-karta') || {}).offsetHeight > 0,
    tekst: (document.querySelector('#vybor-tekst') || {}).textContent || '',
    glavnaya: (document.querySelector('#vybor-glavnaya') || {}).textContent || '',
    vtoraya: (document.querySelector('#vybor-vtoraya') || {}).textContent || '',
  }));
  proverka('после перезагрузки лекция ждёт на паузе — карточка видна',
           vozvrat.kartochka && vozvrat.vidna, vozvrat);
  proverka('карточка говорит, на чём остановились',
           vozvrat.tekst.startsWith('Вы остановились на «'), vozvrat.tekst);
  proverka('главная кнопка — «Продолжить»',
           vozvrat.glavnaya === 'Продолжить', vozvrat.glavnaya);
  proverka('вторая кнопка — «Следующая лекция» (а не «фильм»)',
           vozvrat.vtoraya === 'Следующая лекция', vozvrat.vtoraya);

  // Досмотрели: плеер о конце сообщает сообщением — его и отправим.
  // Карточка в этот момент ещё старая (она меняется при следующем
  // показе), поэтому после сообщения страницу перезагружаем.
  await l.evaluate(() => document.querySelectorAll('.trek')[0].click());
  await l.waitForTimeout(500);
  await l.evaluate(() => window.postMessage(
    JSON.stringify({ type: 'player:playComplete', data: {} }), '*'));
  await l.waitForTimeout(300);
  await l.reload({ waitUntil: 'load' });
  await l.waitForTimeout(1000);
  const dosmotreno = await l.evaluate(() => ({
    tekst: (document.querySelector('#vybor-tekst') || {}).textContent || '',
    glavnaya: (document.querySelector('#vybor-glavnaya') || {}).textContent || '',
    vtoraya: (document.querySelector('#vybor-vtoraya') || {}).textContent || '',
  }));
  proverka('после просмотра карточка говорит «посмотрели»',
           dosmotreno.tekst.endsWith('посмотрели'), dosmotreno.tekst);
  proverka('после просмотра предлагают следующую лекцию',
           dosmotreno.glavnaya === 'Следующая лекция', dosmotreno.glavnaya);
  proverka('в карточке нет слова «фильм»',
           !(dosmotreno.tekst + dosmotreno.glavnaya + dosmotreno.vtoraya)
             .includes('фильм'),
           [dosmotreno.tekst, dosmotreno.glavnaya, dosmotreno.vtoraya]);

  console.log('ошибки на странице предмета:',
              osh.length ? osh.join(' | ') : 'нет');
  console.log('ошибки на странице лекций:',
              oshl.length ? oshl.join(' | ') : 'нет');
  console.log('\nИтог: ошибок ' + oshibki);
  await b.close();
  process.exit(oshibki ? 1 : 0);
})();
