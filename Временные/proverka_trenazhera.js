// Страница «Тренажёры» (7 класс, История).
//
// Устроена как видеоуроки: поле 16:9 слева, та же выезжающая панель
// справа. Своё у неё — содержимое: в поле карточка того, что решаем,
// в панели «Настройки» — что тренируем и до какого параграфа, под полем —
// статистика и «Работа над ошибками».
//
// Числа ожиданий берём из самой базы тренажёров, а не пишем руками:
// разойтись с файлами им нечем.
//
//   node Временные/proverka_trenazhera.js
//   node Временные/proverka_trenazhera.js "<страница тренажёров>" "<папка базы>"
const fs = require('fs');
const path = require('path');
const { chromium } = require('./плейрайт.js');

const stranica = process.argv[2] ||
  'Проект/База данных/HTML/7 класс/История/тренажёры.html';
const papka_bazy = process.argv[3] ||
  'Проект/База данных/Тренажёры/История, 7 класс';

const daty = JSON.parse(fs.readFileSync(path.join(papka_bazy, 'Даты.json'), 'utf8'));
const opred = JSON.parse(fs.readFileSync(path.join(papka_bazy,
  'Определения.json'), 'utf8'));
const paragrafy = JSON.parse(fs.readFileSync(path.join(papka_bazy,
  'параграфы.json'), 'utf8'))['параграфы'];
const chislo_d = daty['даты'].length;
const chislo_o = opred['определения'].length;
const vsego = chislo_d + chislo_o;

// Сколько событий приходится на каждый год. У годов, где событий больше
// одного, вопрос задаётся только со стороны события: «что было в 1526
// году?» имело бы два верных ответа (см. sobran_vopros в сборке).
const skolko_v_godu = {};
daty['даты'].forEach(v => {
  skolko_v_godu[v['когда']] = (skolko_v_godu[v['когда']] || 0) + 1;
});

// Место параграфа в курсе — порядок строк в «параграфы.json».
const mesto = {};
paragrafy.forEach((p, i) => { mesto[p['kod']] = i + 1; });
const ves = [...daty['даты'], ...opred['определения']];
// Выбран параграф — в работе всё с начала курса до него.
const pri_vybore = kod => !kod ? ves.length
  : ves.filter(v => v['paragraf'] && mesto[v['paragraf']] <= mesto[kod]).length;
// Выбран учебник — в работе только его вопросы.
const pri_uchebnike = uch => ves.filter(v => v['учебник'] === uch).length;
const s_daty = k => daty['даты'].filter(v => v['paragraf'] === k).length;
const s_opred = k => opred['определения'].filter(v => v['paragraf'] === k).length;
// Правило тире на всю сборку (см. _tv.tire): промежуток между числами
// — коротким тире с пробелом. В базе числа записаны как есть («12–13»,
// «1607—1610»), а на странице видно «12 – 13»: сравниваем по правилу.
const po_tire = s => String(s)
  .replace(/(?<=[\wА-Яа-яЁё])[—–](?=[\wА-Яа-яЁё])/g, ' \u2013 ');
const par_do = paragrafy[11];
// Что должен найти поиск: только точный номер — сам § («12») или
// половина сдвоенного («12» к § 12–13, но не § 1–2: у того цифры «12»
// только в сумме). Примерных попаданий нет, названия не ищем.
const naydet_tochno = (cifra, uch) => paragrafy.filter(p =>
  (!uch || p['uchebnik'] === uch) &&
  String(p['nomer']).split(/[—–-]/)
    .some(ch => ch.replace(/[^0-9]/g, '') === cifra));

let oshibki = 0;
const proverka = (chto, uslovie, fakticheski) => {
  console.log((uslovie ? '  ок   ' : '  ОШИБКА ') + chto +
    (uslovie ? '' : ' → ' + JSON.stringify(fakticheski)));
  if (!uslovie) oshibki++;
};
const bez_myagkih = s => String(s || '').replace(/\u00ad/g, '');
const bez_ya = s => bez_myagkih(s).replace(/\s+/g, ' ').trim();

(async () => {
  const b = await chromium.launch();
  const adres = 'file://' + path.resolve(stranica);

  // ---- широкое окно: панель открыта сразу, как на видеоуроках ----
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  const bedy = [];
  p.on('console', m => { if (m.type() === 'error') bedy.push(m.text()); });
  p.on('pageerror', e => bedy.push('js: ' + e.message));
  await p.goto(adres);
  await p.waitForTimeout(400);

  console.log('ШИРОКОЕ ОКНО (1920)');
  proverka('окно открылось на странице тренажёров',
    (await p.title()).includes('тренажёры'), await p.title());
  proverka('панель справа та же, что у видеоуроков (#pleylist-panel)',
    await p.locator('#pleylist-panel').count() === 1);
  proverka('панель открыта сразу (pleylist-otkryto)',
    await p.locator('body.pleylist-otkryto').count() === 1);
  proverka('панель называется «Настройки»',
    bez_ya(await p.locator('#pl-zag').innerText()) === 'Настройки',
    await p.locator('#pl-zag').innerText());
  proverka('в шапке панели есть крестик',
    await p.locator('#pleylist-panel .panel-verh a.panel-zakryt').count() === 1);
  // Заголовки панелей — тем же шрифтом, что мелкие подписи: 23px и серые.
  const kega = await p.evaluate(() => {
    const z = document.getElementById('pl-zag');
    const s = getComputedStyle(z);
    return { razmer: parseInt(s.fontSize, 10), cvet: s.color,
             tolshchina: s.fontWeight };
  });
  proverka('заголовок панели — 23px, обычного начертания, серый',
    kega.razmer === 23 && (kega.tolshchina === '400' || kega.tolshchina === 'normal'),
    kega);

  // ---- кнопка настроек: в строке подписи, у правого края ----
  console.log('ШАПКА: КНОПКА НАСТРОЕК СПРАВА');
  const knopka = await p.locator('a.nastr-knopka').boundingBox();
  // Подпись над кадром — сама строка настроек. Кнопка стоит по ПЕРВОЙ
  // её строке, а не по середине всей надписи: надпись бывает в две
  // строки, и посередине кнопка уезжала к нижней.
  const podpis = await p.locator('#pleyer-zag').boundingBox();
  const stroka_podpisi = await p.evaluate(() => {
    const z = document.getElementById('pleyer-zag');
    const st = getComputedStyle(z);
    return { vysota: parseFloat(st.lineHeight),
             verh: z.getBoundingClientRect().top };
  });
  const pole = await p.locator('#pleyer').boundingBox();
  proverka('кнопка настроек выровнена по первой строке надписи',
    Math.abs((knopka.y + knopka.height / 2) -
      (stroka_podpisi.verh + stroka_podpisi.vysota / 2)) < 4,
    { knopka: knopka.y + knopka.height / 2,
      perva: stroka_podpisi.verh + stroka_podpisi.vysota / 2 });
  proverka('подпись над кадром начинается от левого края поля',
    Math.abs(podpis.x - pole.x) < 8, { podpis, pole });
  proverka('кнопка настроек — у правого края поля, за подписью',
    knopka.x > podpis.x + podpis.width - 8 &&
    Math.abs((knopka.x + knopka.width) - (pole.x + pole.width)) < 8,
    { knopka, podpis, pole });
  // ---- над кадром: сами настройки крупно, как подпись кадра на видео ----
  console.log('НАД КАДРОМ: НАСТРОЙКИ');
  const nadpis = bez_ya(await p.locator('#pleyer-zag').innerText());
  proverka('над кадром написаны выбранные настройки',
    nadpis === 'Даты и определения · Весь курс', nadpis);
  proverka('имени страницы («Тренажёр») над кадром нет',
    !nadpis.includes('Тренажёр'), nadpis);
  proverka('подзаголовка под настройками нет',
    await p.locator('#trener-svodka, .trener-svodka').count() === 0);
  const kega_zag = await p.evaluate(() => {
    const s = getComputedStyle(document.getElementById('pleyer-zag'));
    return { razmer: parseInt(s.fontSize, 10), tolshchina: s.fontWeight };
  });
  proverka('настройки набраны тем же кеглем, что подпись кадра на видео (40px)',
    kega_zag.razmer === 40 && kega_zag.tolshchina === '600', kega_zag);
  proverka('заголовка-дубля над страницей нет — имя одно',
    await p.locator('h1').count() === 0, await p.locator('h1').count());

  // ---- «Ещё по курсу»: плашки полосой в один ряд с прокруткой ----
  console.log('ЕЩЁ ПО КУРСУ');
  proverka('надпись над плашками — «Ещё по курсу»',
    bez_ya(await p.locator('.pl-razdely .pl-zagolovok').innerText()) ===
      'Ещё по курсу',
    await p.locator('.pl-razdely .pl-zagolovok').innerText());
  const polosa = await p.evaluate(() => {
    const s = document.querySelector('.pl-razdely .setka');
    const pl = s.querySelector('a.plitka');
    const st = getComputedStyle(s);
    return { display: st.display,
             prokrutka: s.scrollWidth - s.clientWidth,
             ryadov: new Set([...s.querySelectorAll('a.plitka')]
               .map(a => Math.round(a.getBoundingClientRect().top))).size,
             vidno: s.getBoundingClientRect().width /
               (pl.getBoundingClientRect().width + parseFloat(st.gap)) };
  });
  proverka('плашки стоят полосой в один ряд и прокручиваются вбок',
    polosa.display === 'flex' && polosa.ryadov === 1 && polosa.prokrutka > 100,
    polosa);
  proverka('видно две плашки и половину третьей — как на YouTube',
    Math.abs(polosa.vidno - 2.5) < 0.25, polosa.vidno.toFixed(2));
  const str = await p.evaluate(() => {
    const pol = document.querySelector('.pl-polosa');
    const s = document.querySelector('.pl-razdely .setka');
    const r = s.getBoundingClientRect();
    const zona = document.querySelector('.rabochaya').getBoundingClientRect();
    return { left: Math.round(r.left), right: Math.round(r.right),
             zona: Math.round(zona.right),
             polosy: getComputedStyle(s).scrollbarWidth,
             nazad: getComputedStyle(pol.querySelector('.pl-strelka-nazad')).visibility,
             vpered: getComputedStyle(pol.querySelector('.pl-strelka-vpered')).visibility,
             znak: pol.querySelectorAll('a.pl-strelka svg').length };
  });
  proverka('полосы прокрутки у полосы плашек нет',
    str.polosy === 'none', str);
  proverka('полоса идёт до края рабочей зоны, а не обрывается по блоку',
    str.left === 0 && Math.abs(str.right - str.zona) < 2, str);
  proverka('стрелок две, у каждой значок',
    str.znak === 2, str.znak);
  proverka('в начале полосы видна только правая стрелка',
    str.nazad === 'hidden' && str.vpered === 'visible',
    { nazad: str.nazad, vpered: str.vpered });
  // Надпись «Ещё по курсу» — на левом краю, там же, где статистика под
  // полем и сам кадр: одно начало строки на всей странице.
  const kraya = await p.evaluate(() => {
    const l = s => {
      const e = document.querySelector(s);
      return e ? Math.round(e.getBoundingClientRect().left) : null;
    };
    return { ezhe: l('.pl-razdely .pl-zagolovok'),
             pole: l('#pleyer'), plashka: l('.pl-razdely .setka a.plitka') };
  });
  proverka('«Ещё по курсу» встало по левому краю поля',
    Math.abs(kraya.ezhe - kraya.pole) < 2 &&
    Math.abs(kraya.ezhe - kraya.plashka) < 2, kraya);
  // Отступ сверху у «Ещё по курсу» — тот же, что от строки учебника до
  // строки настроек: блок отделён от поля так же, как шапка страницы.
  const zazory = await p.evaluate(() => {
    const v = s => {
      const e = document.querySelector(s);
      return e ? e.getBoundingClientRect().top : null;
    };
    const n = s => {
      const e = document.querySelector(s);
      return e ? e.getBoundingClientRect().bottom : null;
    };
    return { polosa: Math.round(v('.pl-razdely .pl-zagolovok') -
                              n('#pleyer-mesto')),
             shapka: Math.round(v('.trener-shapka') - n('.kniga-stroka')) };
  });
  proverka('отступ «Ещё по курсу» сверху — как у шапки страницы (46 px)',
    Math.abs(zazory.polosa - zazory.shapka) < 3 && zazory.polosa > 40, zazory);
  // Подсказка о прокрутке: в разметке она есть всегда, а видно её только
  // там, где листают пальцем.
  proverka('в полосе есть подсказка «Листайте вбок» с рукой',
    await p.locator('.pl-polosa .pl-podskazka svg').count() === 1 &&
    bez_ya(await p.locator('.pl-polosa .pl-podskazka span').innerText()) ===
      'Листайте вбок');
  proverka('на мыши подсказку не видно — она для пальца',
    await p.evaluate(() => getComputedStyle(document.querySelector(
      '.pl-polosa .pl-podskazka')).display) === 'none');

  // Телефон: палец вместо мыши. Подсказка видна, стоит посреди полосы,
  // рука ходит влево-вправо, а после первого сдвига подсказка уходит.
  const tel = await b.newContext({ viewport: { width: 390, height: 780 },
    hasTouch: true, isMobile: true });
  const tm = await tel.newPage();
  const bedy_t = [];
  tm.on('console', m => { if (m.type() === 'error') bedy_t.push(m.text()); });
  tm.on('pageerror', e => bedy_t.push('js: ' + e.message));
  await tm.goto(adres);
  await tm.waitForTimeout(500);
  const podskazka = await tm.evaluate(() => {
    const k = document.querySelector('.pl-polosa .pl-podskazka');
    const r = k.getBoundingClientRect();
    const s = document.querySelector('.pl-razdely .setka').getBoundingClientRect();
    return { display: getComputedStyle(k).display,
             hodit: getComputedStyle(k.querySelector('svg')).animationName,
             vysota: Math.round(r.height),
             centr: Math.round(r.left + r.width / 2),
             centr_polosy: Math.round(s.left + s.width / 2) };
  });
  proverka('на телефоне подсказка видна, в одну строку и посреди полосы',
    podskazka.display === 'flex' && podskazka.hodit === 'pl-rukoy' &&
    podskazka.vysota <= 44 &&
    Math.abs(podskazka.centr - podskazka.centr_polosy) < 6, podskazka);
  await tm.screenshot({ path: 'Временные/снимки/тренажёры-телефон-подсказка.png' });
  await tm.evaluate(() => {
    const s = document.querySelector('.pl-razdely .setka');
    s.scrollLeft = 120;
    s.dispatchEvent(new Event('scroll'));
  });
  await tm.waitForTimeout(250);
  proverka('после первого сдвига подсказка уходит до конца страницы',
    await tm.evaluate(() => getComputedStyle(document.querySelector(
      '.pl-polosa .pl-podskazka')).display) === 'none');
  proverka('подсказка ничего не сломала: ошибок в консоли нет',
    bedy_t.length === 0, bedy_t.join(' | '));
  await tel.close();

  // ---- имя с первой страницы: по середине верхнего меню ----
  console.log('ВЕРХНЕЕ МЕНЮ: ИМЯ');
  proverka('пока имени нет, в шапке пусто',
    await p.evaluate(() => {
      const u = document.getElementById('verh-imya');
      return !!u && u.hidden && u.textContent === '';
    }));
  // Идём так, как ходит ребёнок: на первой странице пишем имя и оттуда же
  // уходим дальше — в той же вкладке (в памяти браузера имя живёт вместе
  // с вкладкой, в которой его набрали).
  await p.goto('file://' + path.resolve(path.join(path.dirname(stranica),
    '..', '..', '..', '..', 'Начать учиться.html')));
  await p.waitForTimeout(400);
  await p.locator('#imya').fill('Полина');
  await p.waitForTimeout(250);
  proverka('на первой странице имя сохранилось в памяти браузера',
    (await p.evaluate(() => localStorage.getItem('shkola.imya'))) === 'Полина');
  await p.goto(adres);
  await p.waitForTimeout(500);
  const s_imenem = await p.evaluate(() => {
    const u = document.getElementById('verh-imya');
    const nav = document.querySelector('nav.verh').getBoundingClientRect();
    const r = u.getBoundingClientRect();
    return { tekst: u.textContent.trim(), skryto: u.hidden,
             centr: Math.round(r.left + r.width / 2),
             centr_shapki: Math.round(nav.left + nav.width / 2),
             v_shapke: r.top >= nav.top - 2 && r.bottom <= nav.bottom + 2,
             krupno: parseInt(getComputedStyle(u).fontSize, 10) };
  });
  proverka('имя с первой страницы встало по середине верхнего меню',
    s_imenem.tekst === 'Полина' && !s_imenem.skryto &&
    Math.abs(s_imenem.centr - s_imenem.centr_shapki) < 6 &&
    s_imenem.v_shapke, s_imenem);
  proverka('имя набрано крупно — как логотип, а не мелкой подписью',
    s_imenem.krupno >= 24, s_imenem.krupno);

  await p.locator('.pl-polosa a.pl-strelka-vpered').click();
  await p.waitForTimeout(700);
  const sdvin = await p.evaluate(() => ({
    scrollLeft: Math.round(document.querySelector('.pl-razdely .setka').scrollLeft),
    nazad: getComputedStyle(document.querySelector('.pl-polosa ' +
      'a.pl-strelka-nazad')).visibility }));
  proverka('правая стрелка листает полосу и зажигает левую',
    sdvin.scrollLeft > 100 && sdvin.nazad === 'visible', sdvin);
  await p.locator('.pl-polosa a.pl-strelka-nazad').click();
  await p.waitForTimeout(700);
  proverka('левая стрелка возвращает полосу в начало',
    (await p.evaluate(() => Math.round(document.querySelector(
      '.pl-razdely .setka').scrollLeft))) === 0);

  // ---- настройки: что тренируем ----
  console.log('НАСТРОЙКИ: ЧТО ТРЕНИРУЕМ');
  const vidy = await p.locator('#pleylist-panel a[data-vid] .nastr-tekst')
    .allTextContents();
  proverka('в панели три строки: Даты и определения, Только даты, ' +
    'Только определения',
    vidy.map(bez_ya).join('|') ===
      'Даты и определения|Только даты|Только определения',
    vidy.map(bez_ya).join('|'));
  proverka('«Работы над ошибками» в панели нет — она под полем',
    !(await p.locator('body').innerText()).includes('Работа над ошибками ·') &&
    await p.locator('#pleylist-panel a[data-vid="oshibki"]').count() === 0);
  proverka('по умолчанию выбрано «Даты и определения»',
    bez_ya(await p.locator('#pleylist-panel a[data-vid].aktiven ' +
      '.nastr-tekst').innerText()) === 'Даты и определения');
  proverka('у кнопок «что тренируем» нет чисел — количество дат не указываем',
    await p.locator('#pleylist-panel a[data-vid] .nastr-schet').count() === 0,
    await p.locator('#pleylist-panel a[data-vid] .nastr-schet').count());
  proverka('раздела «За заход» в панели нет',
    !(await p.locator('body').innerText()).includes('За заход') &&
    await p.locator('#pleylist-panel a[data-zahod]').count() === 0);

  // ---- настройки: по какому учебнику ----
  console.log('НАСТРОЙКИ: ВЫБОР УЧЕБНИКА');
  const uchebniki = await p.locator('#pleylist-panel a[data-uch] .nastr-tekst')
    .allTextContents();
  proverka('в панели три строки: Весь курс, История России, Всеобщая история',
    uchebniki.map(bez_ya).join('|') ===
      'Весь курс|История России|Всеобщая история',
    uchebniki.map(bez_ya).join('|'));
  proverka('раздел назван «Выбор учебника»',
    (await p.locator('#pleylist-panel').innerText()).includes('Выбор учебника'));
  proverka('по умолчанию выбран «Весь курс»',
    bez_ya(await p.locator('#pleylist-panel a[data-uch].aktiven ' +
      '.nastr-tekst').innerText()) === 'Весь курс');
  // Выбрали книгу: вопросы только из неё, и об этом сказано над кадром.
  await p.locator('#pleylist-panel a[data-uch="История России"]').click();
  await p.waitForTimeout(200);
  const u_ir = pri_uchebnike('История России');
  proverka(`«История России»: в работе ${u_ir} вопросов этой книги`,
    (await p.evaluate(() => shkUroki().length)) === u_ir &&
    (await p.evaluate(() => shkNastroykiState().uchebnik)) === 'История России',
    await p.evaluate(() => shkUroki().length));
  proverka('в надписи над кадром назван учебник',
    bez_ya(await p.locator('#pleyer-zag').innerText()) ===
      'Даты и определения · История России',
    await p.locator('#pleyer-zag').innerText());
  // И параграфы в поиске — только этой книги: в другой свои номера.
  await p.locator('#nastr-poisk').fill('1');
  await p.waitForTimeout(200);
  const chuzhih = await p.evaluate(() =>
    [...document.querySelectorAll('#nastr-naydennoe a[data-par]')]
      .map(a => a.getAttribute('data-par')).filter(k => k));
  proverka('в поиске параграфов только выбранная книга',
    chuzhih.length > 0 && chuzhih.every(k =>
      paragrafy.find(x => x['kod'] === k)['uchebnik'] === 'История России'),
    chuzhih.length);
  // Очистили поле — список спрятался, как будто поиска и не было.
  await p.locator('#nastr-poisk').fill('');
  await p.waitForTimeout(120);
  await p.locator('#pleylist-panel a[data-uch=""]').click();
  await p.waitForTimeout(200);
  proverka('«Весь курс» возвращает все вопросы',
    (await p.evaluate(() => shkUroki().length)) === vsego &&
    (await p.evaluate(() => shkNastroykiState().uchebnik)) === '',
    await p.evaluate(() => shkUroki().length));

  // ---- настройки: «Ограничить до» — одно поле с поиском ----
  console.log('НАСТРОЙКИ: ОГРАНИЧИТЬ ДО');
  proverka('списка параграфов в панели нет — вместо него поиск',
    await p.locator('#pleylist-panel a[data-par]').count() === 0,
    await p.locator('#pleylist-panel a[data-par]').count());
  proverka('разделов «За заход» и «На каком параграфе остановились» нет',
    !(await p.locator('#pleylist-panel').innerText())
      .includes('На каком параграфе') &&
    !(await p.locator('#pleylist-panel').innerText()).includes('За заход'));
  proverka('при «Весь курсе» раздела «Ограничить до» нет — ограничивать нечем',
    await p.locator('#nastr-par[hidden]').count() === 1 &&
    !(await p.locator('#pleylist-panel').innerText()).includes('Ограничить до'));

  // Ограничивают только книгу: выбираем учебник — раздел появляется.
  await p.locator('#pleylist-panel a[data-uch="История России"]').click();
  await p.waitForTimeout(200);
  const v_ir = pri_uchebnike('История России');
  proverka('у выбранного учебника раздел появился',
    await p.locator('#nastr-par[hidden]').count() === 0 &&
    (await p.locator('#pleylist-panel').innerText()).includes('Ограничить до'));
  proverka('раздел назван «Ограничить до»',
    bez_ya(await p.locator('#nastr-par .nastr-zag').innerText()) ===
      'Ограничить до',
    await p.locator('#nastr-par .nastr-zag').innerText());
  // Строка — надпись и поле под ней: без «На каком параграфе
  // остановились?» и без числа параграфов всего курса.
  proverka('раздел — надпись «Ограничить до» и поле под ней',
    await p.locator('#nastr-par .nastr-zag').isVisible() &&
    await p.locator('#nastr-poisk').isVisible() &&
    await p.locator('#nastr-okno[hidden]').count() === 0 &&
    !(await p.locator('#pleylist-panel').innerText())
      .includes('остановились'));
  proverka('поле поиска стоит сразу — нажимать строку не нужно',
    await p.locator('#nastr-poisk').isVisible() &&
    await p.locator('#nastr-okno[hidden]').count() === 0);
  proverka('поле одно, а не два',
    await p.locator('#pleylist-panel input').count() === 1,
    await p.locator('#pleylist-panel input').count());
  proverka('в поле подсказка «Выберите параграф»',
    bez_ya(await p.locator('#nastr-poisk').getAttribute('placeholder')) ===
      'Выберите параграф',
    await p.locator('#nastr-poisk').getAttribute('placeholder'));
  proverka('подсказок «набери номер…» нет, список пока не раскрыт',
    !(await p.locator('#pleylist-panel').innerText()).includes('Набери номер') &&
    await p.locator('#nastr-naydennoe[hidden]').count() === 1 &&
    await p.locator('#nastr-naydennoe a[data-par]').count() === 0);
  proverka('пока ничего не выбрано, поле пустое и крестика нет',
    (await p.locator('#nastr-poisk').inputValue()) === '' &&
    await p.locator('#nastr-krestik[hidden]').count() === 1 &&
    (await p.evaluate(() => !!document.getElementById('nastr-krestik')
      .closest('.nastr-pole'))) === true);

  // Набрали цифру — список раскрылся прямо под полем: попадание точное,
  // и строк в нём раз-два, а не десять «похожих».
  const po_cifram_ir = naydet_tochno('10', 'История России');
  await p.locator('#nastr-poisk').fill('10');
  await p.waitForTimeout(150);
  const stroki_cifry = await p.locator('#nastr-naydennoe a[data-par]')
    .evaluateAll(spis => spis.map(a => a.getAttribute('data-par')));
  proverka(`набор «10» показал ${po_cifram_ir.length} параграфов книги — ` +
    'только с этим номером',
    stroki_cifry.join('|') === po_cifram_ir.map(x => x['kod']).join('|'),
    [stroki_cifry.join('|'), po_cifram_ir.map(x => x['kod']).join('|')]);
  proverka('строки «Весь курс» в списке нет — ограничение снимает крестик',
    stroki_cifry.indexOf('') < 0, stroki_cifry.join('|'));
  proverka('найденных — единицы, а не десять похожих',
    stroki_cifry.length <= 2, stroki_cifry.length);
  const per = po_cifram_ir[0];
  const stroka_p = p.locator(`#nastr-naydennoe a[data-par="${per['kod']}"]`);
  proverka(`у найденного «§ ${per['nomer']}» видны номер, тема и число вопросов`,
    bez_ya(await stroka_p.locator('.nastr-nomer').innerText()) ===
      '§ ' + po_tire(per['nomer']) &&
    bez_ya(await stroka_p.locator('.nastr-tekst').innerText()) ===
      bez_ya(per['nazvanie']) &&
    bez_ya(await stroka_p.locator('.nastr-schet').innerText()) ===
      String(s_daty(per['kod']) + s_opred(per['kod'])),
    await stroka_p.innerText());

  // Названия не ищем: набранное слово не номер, и точного попадания
  // у него быть не может.
  await p.locator('#nastr-poisk').fill('великие');
  await p.waitForTimeout(150);
  proverka('по слову параграф не находится — ищем только по номеру',
    (await p.locator('#nastr-naydennoe a[data-par]').count()) === 0,
    await p.locator('#nastr-naydennoe').innerText());
  // Сдвоенный параграф находится и по второй половине своего номера.
  const sdvoennye = paragrafy.filter(x => x['uchebnik'] === 'История России' &&
    /[–—]/.test(String(x['nomer'])));
  const vtoraya = String(sdvoennye[0]['nomer']).split(/[–—]/)[1];
  const po_vtoroj = naydet_tochno(vtoraya, 'История России');
  await p.locator('#nastr-poisk').fill(vtoraya);
  await p.waitForTimeout(150);
  proverka(`набор «${vtoraya}» находит сдвоенные параграфы — ` +
    `в том числе § ${sdvoennye[0]['nomer']}`,
    (await p.locator('#nastr-naydennoe a[data-par]')
      .evaluateAll(spis => spis.map(a => a.getAttribute('data-par'))))
      .join('|') === po_vtoroj.map(x => x['kod']).join('|') &&
    po_vtoroj.some(x => x['kod'] === sdvoennye[0]['kod']),
    [vtoraya, po_vtoroj.map(x => x['nomer'])]);

  // Выбрали параграф — он встал в само поле, а в поле, у правого края,
  // появился крестик. Строки ниже нет. Набираем номер как его наберёт
  // ребёнок: у сдвоенного — одну половину.
  const nomer_poiska = String(per['nomer']).split(/[–—]/)[0];
  await p.locator('#nastr-poisk').fill(nomer_poiska);
  await p.waitForTimeout(120);
  await stroka_p.click();
  await p.waitForTimeout(150);
  const v_pole = await p.evaluate(() => {
    const po = document.getElementById('nastr-poisk');
    const kr = document.getElementById('nastr-krestik');
    const pr = po.getBoundingClientRect(), r = kr.getBoundingClientRect();
    // Строка списка — образец, с которым сверяем поле: та же ширина,
    // рост, шрифт и подложка (см. a.nastr-stroka).
    const stroka = document.querySelector('#pleylist-panel a.nastr-stroka');
    const sr = stroka.getBoundingClientRect();
    const st = getComputedStyle(stroka), sp = getComputedStyle(po);
    const st_tekst = getComputedStyle(stroka.querySelector('.nastr-tekst'));
    const sr_tekst = stroka.querySelector('.nastr-tekst').getBoundingClientRect();
    return { tekst: po.value, krestik_viden: !kr.hidden,
             vnutri: r.left > pr.left && r.right < pr.right &&
               r.top > pr.top && r.bottom < pr.bottom,
             otstup: Math.round(pr.right - r.right),
             zapas: parseFloat(sp.paddingRight),
             spisok_skryt: document.getElementById('nastr-naydennoe').hidden,
             strok_ogranicheniya: document.querySelectorAll(
               '.nastr-ogranichenie').length,
             shirina: Math.round(pr.width), shirina_stroki: Math.round(sr.width),
             vysota: Math.round(pr.height), vysota_stroki: Math.round(sr.height),
             kega: sp.fontSize, kega_stroki: st_tekst.fontSize,
             // Надпись поля встаёт на одну линию с надписями строк.
             otstup_teksta: Math.round(
               pr.left + parseFloat(sp.borderLeftWidth) +
               parseFloat(sp.paddingLeft) - sr_tekst.left),
             podlozhka: sp.backgroundColor,
             skruglenie: sp.borderTopLeftRadius,
             skruglenie_stroki: st.borderTopLeftRadius,
             // Выбранный параграф отмечен жёлтой полосой у левого края —
             // как выделенная строка списка.
             polosa: sp.backgroundImage.includes('255, 210, 63'),
             bez_ramki: sp.borderTopColor === 'rgba(0, 0, 0, 0)' };
  });
  proverka('выбранный параграф встал в само поле — «§ …»',
    bez_ya(v_pole.tekst) === '§ ' + po_tire(per['nomer']) &&
    v_pole.strok_ogranicheniya === 0, v_pole);
  proverka('крестик стоит в поле, у правого края, и номер под него не заезжает',
    v_pole.krestik_viden === true && v_pole.vnutri === true &&
    v_pole.otstup > 0 && v_pole.zapas >= 40, v_pole);
  proverka('после выбора список находок спрятался',
    v_pole.spisok_skryt === true);
  proverka('поле — та же строка, что пункты списка: ширина, рост и шрифт',
    Math.abs(v_pole.shirina - v_pole.shirina_stroki) <= 2 &&
    Math.abs(v_pole.vysota - v_pole.vysota_stroki) <= 2 &&
    v_pole.kega === v_pole.kega_stroki &&
    Math.abs(v_pole.otstup_teksta) <= 2 && v_pole.bez_ramki === true,
    [v_pole.shirina, v_pole.shirina_stroki, v_pole.vysota,
     v_pole.vysota_stroki, v_pole.kega, v_pole.kega_stroki,
     v_pole.otstup_teksta]);
  proverka('поле одето как выделенная строка: подложка, скругление, полоса',
    v_pole.podlozhka === 'rgb(35, 44, 56)' && v_pole.polosa === true &&
    v_pole.skruglenie === v_pole.skruglenie_stroki,
    [v_pole.podlozhka, v_pole.polosa, v_pole.skruglenie,
     v_pole.skruglenie_stroki]);
  // Вопросы — с начала книги до выбранного параграфа.
  const v_do = ves.filter(v => v['paragraf'] &&
    v['учебник'] === 'История России' &&
    mesto[v['paragraf']] <= mesto[per['kod']]).length;
  proverka(`в работе вопросы книги до § ${per['nomer']} (${v_do})`,
    (await p.evaluate(() => shkUroki().length)) === v_do &&
    (await p.evaluate(() => shkNastroykiState().paragraf)) === per['kod'],
    await p.evaluate(() => shkUroki().length));
  proverka('в надписи над кадром — «до § …» (номер, без темы)',
    bez_ya(await p.locator('#pleyer-zag').innerText()) ===
      `Даты и определения · История России · до § ${po_tire(per['nomer'])}`,
    await p.locator('#pleyer-zag').innerText());
  proverka('строки «только по выбранному параграфу» в панели нет',
    await p.locator('#nastr-flag').count() === 0 &&
    (await p.evaluate(() => shkNastroykiState().tolko_paragraf)) === undefined);

  // Клавиши: Esc чистит поле, Enter берёт первую находку.
  await p.locator('#nastr-poisk').fill(nomer_poiska);
  await p.waitForTimeout(120);
  await p.keyboard.press('Escape');
  await p.waitForTimeout(120);
  proverka('Esc закрывает поиск, но настройки не закрывает',
    await p.locator('#nastr-naydennoe[hidden]').count() === 1 &&
    await p.locator('#pleylist-panel').isVisible() &&
    (await p.evaluate(() => shkNastroykiState().paragraf)) === per['kod']);
  proverka('Esc вернул в поле выбранный параграф — там его и видно',
    bez_ya(await p.locator('#nastr-poisk').inputValue()) ===
      '§ ' + po_tire(per['nomer']) &&
    await p.locator('#nastr-krestik[hidden]').count() === 0,
    await p.locator('#nastr-poisk').inputValue());
  const po_12 = naydet_tochno('12', 'История России');
  await p.locator('#nastr-poisk').fill('12');
  await p.waitForTimeout(120);
  await p.keyboard.press('Enter');
  await p.waitForTimeout(150);
  proverka('Enter берёт первый найденный параграф',
    (await p.evaluate(() => shkNastroykiState().paragraf)) === po_12[0]['kod'] &&
    await p.locator('#nastr-naydennoe[hidden]').count() === 1,
    await p.evaluate(() => shkNastroykiState().paragraf));
  proverka('и он так же встал в поле, с крестиком',
    bez_ya(await p.locator('#nastr-poisk').inputValue()) ===
      '§ ' + po_tire(po_12[0]['nomer']) &&
    await p.locator('#nastr-krestik[hidden]').count() === 0,
    await p.locator('#nastr-poisk').inputValue());

  // Крестик в поле снимает ограничение.
  await p.locator('#nastr-krestik').click();
  await p.waitForTimeout(200);
  proverka('крестик в поле снимает ограничение',
    (await p.evaluate(() => shkNastroykiState().paragraf)) === '' &&
    (await p.evaluate(() => shkUroki().length)) === v_ir &&
    (await p.locator('#nastr-poisk').inputValue()) === '' &&
    await p.locator('#nastr-krestik[hidden]').count() === 1,
    await p.evaluate(() => shkUroki().length));
  proverka('без ограничения надпись снова про книгу',
    bez_ya(await p.locator('#pleyer-zag').innerText()) ===
      'Даты и определения · История России',
    await p.locator('#pleyer-zag').innerText());

  // Ограничение живёт внутри книги: другая книга его снимает.
  await p.locator('#nastr-poisk').fill(nomer_poiska);
  await p.waitForTimeout(150);
  await stroka_p.click();
  await p.waitForTimeout(150);
  await p.locator('#pleylist-panel a[data-uch="Всеобщая история"]').click();
  await p.waitForTimeout(200);
  proverka('смена книги снимает ограничение — в другой книге свои номера',
    (await p.evaluate(() => shkNastroykiState().paragraf)) === '' &&
    (await p.locator('#nastr-poisk').inputValue()) === '' &&
    await p.locator('#nastr-krestik[hidden]').count() === 1 &&
    (await p.evaluate(() => shkUroki().length)) ===
      pri_uchebnike('Всеобщая история'),
    await p.evaluate(() => shkUroki().length));
  const po_20 = naydet_tochno('20', 'Всеобщая история');
  await p.locator('#nastr-poisk').fill('20');
  await p.waitForTimeout(150);
  proverka('и поиск теперь по второй книге',
    (await p.locator('#nastr-naydennoe a[data-par]')
      .evaluateAll(spis => spis.map(a => a.getAttribute('data-par'))))
      .join('|') === po_20.map(x => x['kod']).join('|') && po_20.length > 0,
    po_20.map(x => x['nomer']));
  await p.locator('#nastr-poisk').fill('');
  await p.locator('#pleylist-panel a[data-uch=""]').click();
  await p.waitForTimeout(200);
  proverka('«Весь курс» возвращает все вопросы',
    (await p.evaluate(() => shkUroki().length)) === vsego &&
    (await p.evaluate(() => shkNastroykiState().uchebnik)) === '',
    await p.evaluate(() => shkUroki().length));
  proverka('и раздел «Ограничить до» снова спрятан',
    await p.locator('#nastr-par[hidden]').count() === 1);

  // ---- статистика: вся в верхней строке поля ----
  console.log('СТАТИСТИКА: В ВЕРХНЕЙ СТРОКЕ ПОЛЯ');
  // Под полем статистики нет вовсе: «осталось пройти» — это разница
  // между «2 / 277» и номером, и отдельной строкой она не нужна.
  proverka('под полем никакой статистики нет',
    await p.locator('.trener-statistika').count() === 0 &&
    await p.locator('#stat-ostalos').count() === 0 &&
    await p.locator('#pleylist-panel #stat-ostalos').count() === 0 &&
    !(await p.locator('.pl-razdely').innerText()).includes('Осталось пройти'));
  const do_otvetov = await p.evaluate(() => {
    const sk = document.getElementById('trener-oshibki-schet');
    return {
      osh_v_pole: document.querySelectorAll('#trener-igra #trener-oshibki').length,
      osh: document.getElementById('stat-oshibok').textContent,
      slovo_oshibok: document.querySelector('.pl-razdely').innerText
        .includes('Ошибок'),
      schet_skryt: sk ? sk.hidden : null,
    };
  });
  // Счёт ошибок живёт с заходом: до него в верхней строке только значки.
  proverka('до захода счёта ошибок в поле нет — он живёт с заходом',
    do_otvetov.schet_skryt === true, do_otvetov.schet_skryt);
  proverka('пока ошибок нет, кнопки ошибок в поле нет',
    do_otvetov.osh_v_pole === 0 && do_otvetov.osh === '0' &&
    !do_otvetov.slovo_oshibok, do_otvetov);
  proverka('сброса под полем нет — он внизу панели настроек',
    await p.locator('#pleylist-panel #trener-sbros').count() === 1);
  proverka('сноски об учебниках нет ни в панели, ни под полем',
    await p.locator('#pleylist-panel .nastr-istochnik').count() === 0 &&
    await p.locator('.trener-istochnik').count() === 0,
    await p.locator('.nastr-istochnik').count());

  // ---- поле и движок ----
  console.log('ПОЛЕ');
  const razmery = await p.locator('#pleyer').boundingBox();
  // Пропорций кадра у тренажёра больше нет: это рабочий экран, он растёт
  // по высоте содержимого и ниже высоты окна не опускается.
  proverka('поле тренажёра — рабочий экран, а не кадр 16:9',
    (await p.evaluate(() => getComputedStyle(document.getElementById('pleyer'))
      .aspectRatio)) === 'auto' &&
    razmery.height >= Math.min(540, Math.round(razmery.width * 0.5)),
    { aspect: await p.evaluate(() => getComputedStyle(
        document.getElementById('pleyer')).aspectRatio),
      vysota: Math.round(razmery.height) });
  // В поле названия набора нет: что решаем, видно в надписи над кадром,
  // а на пустом экране — только кнопка.
  proverka('названия набора в поле нет — оно в надписи над кадром',
    await p.locator('#trener-zag').count() === 0 &&
    bez_ya(await p.locator('#pleyer-zag').innerText()) ===
      'Даты и определения · Весь курс');
  proverka('заголовка «Что потренируем» на странице нет',
    !(await p.locator('body').innerText()).includes('Что потренируем'));
  proverka('до захода в поле карточка-приглашение, вопроса нет',
    await p.locator('#trener-karta #trener-priglashenie').count() === 1 &&
    await p.locator('#trener-igra.vidna').count() === 0);
  proverka('кнопка «Начать» на месте',
    await p.locator('#trener-nachat').count() === 1);
  // Пустой экран: одна кнопка «Начать тренировку». Ни названия набора,
  // ни числа вопросов, ни пояснений — что решаем, видно в надписи над
  // кадром, а как идут вопросы — с первого же вопроса.
  const pustoj = await p.evaluate(() => {
    const kart = document.getElementById('trener-karta');
    const pole = document.getElementById('pleyer').getBoundingClientRect();
    const priv = document.getElementById('trener-priglashenie');
    const kv = document.getElementById('trener-nachat');
    const kn = kv.getBoundingClientRect();
    const st = getComputedStyle(kv);
    const nag = document.getElementById('trener-nagrady');
    const znak = document.getElementById('trener-podskazka-znak');
    const ekr = document.getElementById('trener-vo-ves-ekran').getBoundingClientRect();
    return { vsyo: priv.innerText.replace(/\s+/g, ' ').trim(),
             lishnih: ['вопрос', 'Вопросы идут', 'в работе', 'Определения'].filter(s =>
               priv.innerText.includes(s)),
             schet_oshibok: (() => {
               const s = document.getElementById('trener-oshibki-schet');
               return s ? s.hidden : null;
             })(),
             // Экран помечен пустым: поле пустует и нажимается всё.
             pusto: (kart.className || '').includes('pusto'),
             // Кнопки-плашки нет: подложки нет вовсе, только контур.
             klass: kv.className,
             fon: st.backgroundColor + ' | ' + st.backgroundImage,
             kontur: st.borderTopColor, tolshchina: st.borderTopWidth,
             radius: st.borderTopLeftRadius,
             kega: st.fontSize, cvet: st.color, ves: st.fontWeight,
             // Контур — во всё поле: 12 px от его краёв и по ширине,
             // и по высоте.
             otstupy: [Math.round(kn.left - pole.left),
                       Math.round(pole.right - kn.right),
                       Math.round(kn.top - pole.top),
                       Math.round(pole.bottom - kn.bottom)],
             shirina: Math.round(kn.width), shirina_polya: Math.round(pole.width),
             vysota: Math.round(kn.height), vysota_polya: Math.round(pole.height),
             centr_kn: Math.abs((kn.left + kn.width / 2) -
               (pole.left + pole.width / 2)) < 3,
             po_seredine: Math.abs((kn.top + kn.height / 2) -
               (pole.top + pole.height / 2)) < 3,
             znak_voprosa: znak ?
               (znak.hidden && getComputedStyle(znak).display === 'none') : null,
             nagrady: getComputedStyle(nag).display,
             ekran_sprava: ekr.left > pole.left + pole.width / 2 &&
               ekr.right <= pole.right + 2 };
  });
  proverka('на пустом экране — одна надпись «Начать тренировку»',
    pustoj.vsyo === 'Начать тренировку' && pustoj.lishnih.length === 0 &&
    pustoj.schet_oshibok === true,
    [pustoj.vsyo, pustoj.lishnih, pustoj.schet_oshibok]);
  proverka('пустой экран — сам кнопка: кнопки-плашки в нём нет',
    pustoj.pusto === true && !pustoj.klass.includes('knopka') &&
    pustoj.fon.includes('rgba(0, 0, 0, 0)') && pustoj.tolshchina === '0px',
    [pustoj.pusto, pustoj.klass, pustoj.fon]);
  proverka('у пустого экрана нет обводки, экран жёлтый',
    pustoj.tolshchina === '0px' && pustoj.tolshchina === '0px' &&
    pustoj.fon.includes('rgba(0, 0, 0, 0)'),
    [pustoj.kontur, pustoj.tolshchina, pustoj.fon]);
  proverka('надпись на пустом экране крупная, белая и по центру поля',
    parseFloat(pustoj.kega) >= 40 && pustoj.cvet === 'rgb(255, 255, 255)' &&
    pustoj.ves === '600' && pustoj.centr_kn === true &&
    pustoj.po_seredine === true,
    [pustoj.kega, pustoj.cvet, pustoj.ves, pustoj.centr_kn, pustoj.po_seredine]);
  proverka('знака вопроса на пустом экране нет',
    pustoj.znak_voprosa === true, pustoj.znak_voprosa);
  proverka('полосы времени на пустом экране нет — минута идёт с заходом',
    await p.locator('#trener-vremya').count() === 0);
  proverka('кристаллов на пустом экране не видно — даже серых',
    pustoj.nagrady === 'none', pustoj.nagrady);
  proverka('«во весь экран» стоит у правого края строки, сразу',
    pustoj.ekran_sprava === true, pustoj.ekran_sprava);
  await p.screenshot({ path: 'Временные/снимки/тренажёры-настройки.png' });

  // Заход начинается всем полем: жмём в угол поля, далеко от надписи, —
  // мишень здесь не слова, а весь экран.
  await p.locator('#trener-nachat').scrollIntoViewIfNeeded();
  await p.waitForTimeout(200);
  const ugol = await p.evaluate(() => {
    const r = document.getElementById('pleyer').getBoundingClientRect();
    return { x: Math.round(r.left + 40), y: Math.round(r.bottom - 40) };
  });
  await p.mouse.move(4, 4);
  await p.mouse.click(ugol.x, ugol.y);
  await p.waitForTimeout(250);
  const perv = await p.evaluate(() => shkZahodSostoyanie());
  proverka('пустой экран нажимается весь: заход начался от нажатия в угол поля',
    perv && perv.nomer === 1 && perv.vsego === vsego,
    perv && { nomer: perv.nomer, vsego: perv.vsego, tochka: ugol });
  proverka('вопрос и четыре варианта стоят в поле',
    await p.locator('#trener-igra a.trener-otvet').count() === 4 &&
    await p.locator('#trener-igra .trener-vopros-pod').count() === 0,
    await p.locator('#trener-igra a.trener-otvet').count());
  proverka('среди вариантов ровно один верный',
    perv.verny >= 0 && perv.verny < 4 && new Set(perv.varianty).size === 4,
    perv.varianty);

  // ---- экран тренажёра: заголовок, вопрос, варианты, стрелки ----
  console.log('ЭКРАН ТРЕНАЖЁРА');
  const ekran = await p.evaluate(() => {
    const g = document.getElementById('trener-igra');
    const gb = g.getBoundingClientRect();
    const pole = document.getElementById('pleyer');
    const pb = pole.getBoundingClientRect();
    const zag = document.querySelector('#trener-igra .trener-vopros-zag');
    const v = document.querySelector('#trener-igra .trener-vopros-pod');
    const vb = zag.getBoundingClientRect();
    const otv = [...document.querySelectorAll('#trener-igra a.trener-otvet')];
    const bloki = otv.map(a => a.getBoundingClientRect());
    const teksty = otv.map(a => a.querySelector('.trener-tekst-otveta'));
    const stroka = document.querySelector('.trener-upravlenie');
    const nazad = document.getElementById('trener-nazad').getBoundingClientRect();
    const vpered = document.getElementById('trener-vpered').getBoundingClientRect();
    const forma = document.querySelector('.trener-forma').getBoundingClientRect();
    const strelki = document.querySelector('.trener-strelki').getBoundingClientRect();
    const st = getComputedStyle(g);
    return {
      osh_v_pole: document.querySelectorAll('#trener-igra #trener-oshibki').length,
      kega_voprosa: parseInt(getComputedStyle(zag).fontSize, 10),
      kega_zagolovka: parseInt(getComputedStyle(zag).fontSize, 10),
      zagolovok: zag.textContent.trim(),
      centr: Math.abs((vb.left + vb.width / 2) - (gb.left + gb.width / 2)) < 4,
      kolonok: new Set(bloki.map(b => Math.round(b.left))).size,
      ryadov: new Set(bloki.map(b => Math.round(b.top))).size,
      obrezannyh: teksty.filter(x => x.scrollHeight > x.clientHeight + 1 ||
                                     x.scrollWidth > x.clientWidth + 1).length,
      klamp: getComputedStyle(teksty[0]).webkitLineClamp,
      // Нижняя строка поля на месте всегда: в ней стрелки. Кнопки
      // ошибок в ней нет, пока ошибок нет (см. oshibki_knopka).
      upr_est: !!stroka && stroka.hidden === false,
      knopka_oshibok_net: document.querySelectorAll(
        '.trener-upravlenie #trener-oshibki').length === 0,
      // Стрелки листания — в правом нижнем углу окна: под ответами,
      // у правого края поля и в самом его низу.
      strelki_v_uglu: Math.round(pb.right - pb.width * 0.05 - strelki.right) === 0 &&
        strelki.top > bloki[bloki.length - 1].bottom && nazad.left < vpered.left,
      strelki_v_nizu: Math.round(gb.bottom - strelki.bottom) === 0,
      // От ответов до нижней строки — воздух, а не впритык.
      otstup_snizu: Math.round(strelki.top - bloki[bloki.length - 1].bottom),
      // Своей прокрутки у поля нет: оно растёт по высоте.
      prokrutka_vnutri: g.scrollHeight - g.clientHeight,
      overflow_igry: st.overflowY,
      vysota_polya: Math.round(pb.height),
      shirina_polya: Math.round(pb.width),
      min_vysota: getComputedStyle(pole).minHeight,
      vo_vsyu_shirinu: bloki.every(b => Math.abs(b.width - bloki[0].width) < 2),
      vopros: zag.textContent.trim(),
      pod: '',
      // Счёт ошибок — в верхней строке поля, рядом со счётом вопросов:
      // красный крестик и число.
      osh_schet: (() => {
        const s = document.getElementById('trener-oshibki-schet');
        if (!s) { return null; }
        const r = s.getBoundingClientRect();
        const sc = document.getElementById('trener-schet-za')
          .getBoundingClientRect();
        const vop = document.getElementById('trener-podskazka-znak')
          .getBoundingClientRect();
        const k = s.querySelector('.trener-krestik');
        const sv = s.querySelector('.trener-krestik svg');
        const cifra = s.querySelector('b');
        const cv = getComputedStyle(cifra);
        const c = document.createElement('canvas').getContext('2d');
        c.font = cv.fontWeight + ' ' + cv.fontSize + ' ' + cv.fontFamily;
        const mera = c.measureText('1');
        const svg_r = sv ? sv.getBoundingClientRect() : null;
        const ramka = sv ? sv.getBBox() : null;
        return { skryt: s.hidden, v_verhu: !!s.closest('.trener-verh'),
                 v_znachkah: !!s.closest('.trener-znachki'),
                 do_znachka: r.right <= vop.left + 1,
                 daleko_ot_scheta: r.left > sc.right + 40,
                 chislo: cifra.textContent.trim(),
                 cvet: getComputedStyle(k).color,
                 cvet_chisla: cv.color,
                 cvet_kristalla: getComputedStyle(
                   document.getElementById('trener-chislo')).color,
                 svg: s.querySelectorAll('.trener-krestik svg').length,
                 cifra_vysota: +(mera.actualBoundingBoxAscent +
                   mera.actualBoundingBoxDescent).toFixed(1),
                 // Крестик нарисован как кристалл: та же рамка и тот же
                 // штрих, а сам знак занимает столько же места, сколько
                 // камень (см. знак «ошибка»).
                 shtrih_vysota: ramka ? +((ramka.height + 2) / 24 *
                   svg_r.height).toFixed(1) : 0,
                 ramka: svg_r ? Math.round(svg_r.width) + 'x' +
                   Math.round(svg_r.height) : '',
                 shtrih: sv ? getComputedStyle(sv).strokeWidth : '',
                 // Кристалл для сравнения — тот же ряд знаков. Пока
                 // ни одного не собрано, ряд спрятан: показываем его на
                 // время мерки и возвращаем как было (мерим только вид).
                 // Зазор до кристаллов вдвое больше прочих зазоров строки:
                 // это два разных счёта, и вплотную они читались одним
                 // знаком. Кристаллы для мерки показываем на время.
                 zazor: (() => {
                   const nag = document.getElementById('trener-nagrady');
                   if (!nag) { return null; }
                   const byl = nag.hidden;
                   nag.hidden = false;
                   /* Раскладку пересчитываем нарочно: без этого мерка
                      берётся по старому месту — пока кристаллы были
                      скрыты, группа знаков стояла правее. */
                   void document.body.offsetWidth;
                   const nl = nag.getBoundingClientRect();
                   const r2 = s.getBoundingClientRect();
                   const zn = document.getElementById('trener-podskazka-znak');
                   const zl = zn ? zn.getBoundingClientRect() : null;
                   const otvet = { do_kristallov: Math.round(nl.left - r2.right),
                     mezhdu_znakami: zl ?
                       Math.round(zl.left - nl.right) : null,
                     na_odnoy_stroke: Math.abs(nl.top - r2.top) < 5,
                     marg: getComputedStyle(s).marginRight,
                     gap: getComputedStyle(s.parentNode).gap };
                   nag.hidden = byl;
                   return otvet;
                 })(),
                 kristall: (() => {
                   const nag = document.getElementById('trener-nagrady');
                   if (!nag) { return null; }
                   const byl = nag.hidden;
                   nag.hidden = false;
                   void document.body.offsetWidth;
                   const k = document.querySelector('#trener-kristally svg');
                   let otvet = null;
                   if (k) {
                     const kr = k.getBoundingClientRect();
                     const kb = k.getBBox();
                     otvet = { ramka: Math.round(kr.width) + 'x' +
                         Math.round(kr.height),
                       shtrih: getComputedStyle(k).strokeWidth,
                       vysota: +((kb.height + 2) / 24 * kr.height).toFixed(1) };
                   }
                   nag.hidden = byl;
                   return otvet;
                 })() };
      })(),
      otvety: teksty.map(x => x.textContent.trim()),
      // Верхняя строка поля: счёт «N / M» слева, кристалл с числом
      // и «на весь экран» — справа.
      verh: (() => {
        const u = el => el ? el.getBoundingClientRect() : null;
        const s = u(document.getElementById('trener-schet-za'));
        const k = u(document.getElementById('trener-nagrady'));
        const e = u(document.getElementById('trener-vo-ves-ekran'));
        return { schet: s ? { left: Math.round(s.left - pb.left),
                              top: Math.round(s.top - pb.top),
                              tekst: document.getElementById('trener-schet-za')
                                .textContent.replace(/\s+/g, ' ').trim() } : null,
                 nagrady: k ? { left: Math.round(k.left - pb.left),
                                top: Math.round(k.top - pb.top),
                                kristallov: document.querySelectorAll(
                                  '#trener-kristally svg.kristall').length,
                                vzjato: document.querySelectorAll(
                                  '#trener-kristally svg.vzyt').length,
                                chislo: document.getElementById('trener-chislo')
                                  .textContent.trim() } : null,
                 ekran: e ? { right: Math.round(e.right - pb.left),
                              top: Math.round(e.top - pb.top) } : null,
                 polovina: Math.round(pb.width / 2) };
      })(),
      zhivyh_strelok: document.querySelectorAll('a.trener-strelka').length,
      tusklyh_strelok: document.querySelectorAll('span.trener-strelka').length,
      // «Во весь экран» — тот же значок, что и кнопка поверх кадра:
      // на нём и меряем образец значка поля.
      ekran_znachok: (() => {
        const e = document.getElementById('trener-vo-ves-ekran');
        const s = getComputedStyle(e);
        const r = e.getBoundingClientRect();
        return { padding: s.padding, ramka: s.borderTopWidth,
                 radius: s.borderTopLeftRadius, fon: s.backgroundColor,
                 svg: Math.round(e.querySelector('svg')
                   .getBoundingClientRect().width) };
      })(),
      // Верхняя строка: кристаллы, значок вопроса, «на весь экран».
      znak_voprosa: (() => {
        const z = document.getElementById('trener-podskazka-znak');
        if (!z) { return null; }
        const r = z.getBoundingClientRect();
        const s = getComputedStyle(z);
        return { klass: z.className, teg: z.tagName,
                 rol: z.getAttribute('role'),
                 zapret: z.getAttribute('aria-disabled'),
                 razmer: Math.round(r.width),
                 padding: s.padding, ramka: s.borderTopWidth,
                 radius: s.borderTopLeftRadius, fon: s.backgroundColor,
                 fon_zhivogo: null,
                 svg: Math.round((z.querySelector('svg') || {getBoundingClientRect:
                   () => ({width: 0})}).getBoundingClientRect().width),
                 // Значок вопроса стоит между кристаллами и «на весь экран».
                 mezhdu: (() => {
                   const n = document.getElementById('trener-nagrady')
                     .getBoundingClientRect();
                   const e = document.getElementById('trener-vo-ves-ekran')
                     .getBoundingClientRect();
                   return r.left > n.right - 2 && r.right < e.left + 2;
                 })() };
      })(),
    };
  });
  // Заголовком стоит сам вопрос — событие или значение, — а подзаголовком
  // словами: «Когда это было?», «Как это называется?». Слов «Дата»
  // и «Определение» над вопросом нет.
  const formy = ['Когда это было?', 'Что это за время?', 'Что это значит?',
                 'Как это называется?'];
  proverka('заголовком стоит сам вопрос, подзаголовка под ним нет',
    ekran.zagolovok === perv.vopros && ekran.pod === '' && ekran.centr &&
    await p.locator('#trener-igra .trener-vopros-pod').count() === 0,
    { zag: ekran.zagolovok, pod: ekran.pod, vopros: perv.vopros });
  proverka('слов «Дата» и «Определение» в задании нет вовсе',
    !/(^|\s)(Дата|Определение)(\s|$)/.test(
      (await p.locator('.trener-vopros-blok').innerText()).replace(/\s+/g, ' ')),
    await p.locator('.trener-vopros-blok').innerText());
  proverka('счёт ошибок — слева, после кристалла, в верхней строке',
    ekran.osh_schet && ekran.osh_schet.skryt === true &&
    ekran.osh_schet.v_verhu && !ekran.osh_schet.v_znachkah &&
    ekran.osh_schet.ramka === '0x0', ekran.osh_schet);
  proverka('и крестик, и число ошибок — красные',
    ekran.osh_schet.cvet.includes('255, 107, 107') &&
    ekran.osh_schet.cvet_chisla.includes('255, 107, 107') &&
    ekran.osh_schet.cvet_chisla === ekran.osh_schet.cvet, ekran.osh_schet);
  proverka('символ ошибки — круг с восклицанием, а не крестик',
    ekran.osh_schet.svg === 1 && ekran.osh_schet.cvet.includes('255, 107, 107'),
    ekran.osh_schet);
  // От ошибок до кристаллов — вдвое дальше, чем между прочими знаками
  // строки: два счёта стоят рядом и не должны читаться одним знаком.
  proverka('кристалл и ошибки собраны в левой группе верхней строки',
    !!ekran.osh_schet.zazor && ekran.osh_schet.zazor.do_kristallov > 0,
    ekran.osh_schet.zazor);
  proverka('счёт вопроса — «1 / N», без слов «Вопрос» и «из»',
    ekran.verh.schet && ekran.verh.schet.tekst === `1 / ${vsego}`,
    ekran.verh.schet && ekran.verh.schet.tekst);
  proverka('счёт вопроса — в левом верхнем углу поля',
    ekran.verh.schet.left < ekran.verh.polovina && ekran.verh.schet.top < 90,
    ekran.verh.schet);
  proverka('«на весь экран» — в правом верхнем углу поля',
    ekran.verh.ekran.right > ekran.verh.polovina * 2 - 80 &&
    ekran.verh.ekran.top < 90 &&
    await p.locator('#trener-vo-ves-ekran svg').count() === 1, ekran.verh.ekran);
  // Значки поля — по эталону страницы видео: кнопка «Открыть плейлист»
  // поверх кадра (a.pleyer-knopka). У неё тёмная полупрозрачная подложка,
  // значок 34×34, рамка 3 и скругление 12 — то же и здесь.
  const obrazec = await p.evaluate(() => {
    const vid = el => {
      const s = getComputedStyle(el);
      return [s.padding, s.borderTopWidth, s.borderTopLeftRadius,
              s.backgroundColor].join('|');
    };
    return { na_kadre: vid(document.querySelector('a.pleyer-knopka')),
             obrazec_svg: Math.round(document.querySelector('a.pleyer-knopka svg')
               .getBoundingClientRect().width) };
  }).catch(() => null);
  proverka('значок «во весь экран» — того же вида, что кнопка поверх кадра',
    obrazec ? ekran.ekran_znachok.padding === '10px' &&
    ekran.ekran_znachok.ramka === '3px' &&
    ekran.ekran_znachok.radius === '12px' &&
    ekran.ekran_znachok.fon === 'rgba(10, 13, 18, 0.72)' &&
    ekran.ekran_znachok.svg === obrazec.obrazec_svg : true,
    [ekran.ekran_znachok, obrazec]);
  // А под знаком вопроса подложки нет: он и так читается, а тёмный
  // квадрат рядом с ответами выглядел ещё одной кнопкой.
  proverka('под знаком вопроса подложки нет',
    ekran.znak_voprosa.fon === 'rgba(0, 0, 0, 0)' &&
    ekran.znak_voprosa.ramka === '3px' && ekran.znak_voprosa.svg === 34,
    ekran.znak_voprosa);
  proverka('значок вопроса стоит между кристаллами и «на весь экран»',
    ekran.znak_voprosa.mezhdu === true, ekran.znak_voprosa);
  proverka('значок вопроса живой весь заход — и до ответа тоже',
    !ekran.znak_voprosa.klass.includes('tuskly') &&
    ekran.znak_voprosa.rol === 'button' &&
    ekran.znak_voprosa.zapret === null, ekran.znak_voprosa);
  // И он на самом деле нажимается: до ответа значок открывал бы окно,
  // которого нет, — теперь окно открывается.
  await p.locator('#trener-podskazka-znak').click();
  await p.waitForTimeout(250);
  proverka('до ответа значок открывает окно подсказки',
    (await p.evaluate(() => getComputedStyle(document.getElementById(
      'trener-okno-podskazki')).display)) !== 'none');
  await p.keyboard.press('Escape');
  await p.waitForTimeout(250);
  proverka('поле держит рабочую высоту — не меньше половины экрана (до 560)',
    ekran.min_vysota === '540px' && ekran.vysota_polya >= 540 &&
    await p.evaluate(() => getComputedStyle(document.getElementById('pleyer'))
      .aspectRatio) === 'auto',
    { min: ekran.min_vysota, vysota: ekran.vysota_polya });
  proverka('внутри поля нет своей прокрутки — прокручивается страница',
    ekran.overflow_igry === 'visible' && ekran.prokrutka_vnutri < 90,
    { prokrutka: ekran.prokrutka_vnutri, overflow: ekran.overflow_igry });
  proverka('ни один вариант не обрезан: текст переносится целиком',
    ekran.obrezannyh === 0 && (ekran.klamp === 'none' || !ekran.klamp), ekran);
  // Заголовок — сам вопрос, и он тоже показывается целиком: длинное
  // значение определения переносится строками, а не режется и не
  // уезжает за край поля.
  proverka('заголовок вопроса показан целиком, без обрезки',
    await p.evaluate(() => {
      const z = document.querySelector('#trener-igra .trener-vopros-zag');
      const g = document.getElementById('trener-igra').getBoundingClientRect();
      const r = z.getBoundingClientRect();
      return z.scrollHeight <= z.clientHeight + 1 &&
        z.scrollWidth <= z.clientWidth + 1 &&
        r.left >= g.left - 2 && r.right <= g.right + 2;
    }));
  // Ответы стоят по ширине поля: короткие (годы, короткие события) —
  // по две плашки в ряд, и тогда рядов ровно два, по два ответа
  // в каждом; длинные (значения определений) — в один столбец.
  const klass_otv = await p.evaluate(() =>
    document.querySelector('#trener-igra .trener-otvety').className);
  const setka_otvetov = klass_otv.includes('v-stolbik')
    ? { kolonok: 1, ryadov: 4 }
    : { kolonok: 2, ryadov: 2 };
  proverka(`варианты (${klass_otv.split(' ').pop()}) стоят ` +
    (setka_otvetov.kolonok === 2 ? 'по две в ряд' : 'в один столбец'),
    ekran.kolonok === setka_otvetov.kolonok &&
    ekran.ryadov === setka_otvetov.ryadov,
    { klass: klass_otv, kolonok: ekran.kolonok, ryadov: ekran.ryadov });
  proverka('вопрос и варианты — с заглавной буквы',
    ekran.zagolovok[0] === ekran.zagolovok[0].toUpperCase() &&
    ekran.otvety.every(s => s[0] === s[0].toUpperCase()), ekran);
  proverka('в нижней строке поля пока одни стрелки — кнопки ошибок нет',
    ekran.upr_est === true && ekran.knopka_oshibok_net === true,
    { est: ekran.upr_est, net: ekran.knopka_oshibok_net });
  proverka('стрелки листания — в правом нижнем углу окна, под ответами',
    ekran.strelki_v_uglu && ekran.otstup_snizu >= 30 &&
    await p.locator('.trener-strelki a.trener-strelka, ' +
      '.trener-strelki span.trener-strelka').count() === 2, ekran);
  proverka('строки управления «Работа над ошибками» в поле нет',
    ekran.osh_v_pole === 0, ekran.osh_v_pole);
  // Кнопки нижней строки — одного вида: те же поля, та же рамка, тот же
  // скруглённый угол и та же подложка, что у кнопки сброса под полем.
  const stil_knopok = await p.evaluate(() => {
    const vid = el => {
      const s = getComputedStyle(el);
      return [s.fontSize, s.paddingTop, s.paddingRight, s.borderTopWidth,
              s.borderTopLeftRadius].join('|');
    };
    return { strelka: vid(document.getElementById('trener-vpered')),
             sbros: vid(document.getElementById('trener-sbros')) };
  });
  proverka('кнопка сброса — меркой активного пункта меню',
    stil_knopok.sbros === '21px|8px|14px|3px|12px', stil_knopok);
  proverka('от ответов до нижней строки — большой отступ, не впритык',
    ekran.otstup_snizu >= 28, ekran.otstup_snizu);
  proverka('пока ответа нет, стрелки — серые надписи, а не ссылки',
    ekran.zhivyh_strelok === 0 && ekran.tusklyh_strelok === 2,
    { zhivyh: ekran.zhivyh_strelok, tusklyh: ekran.tusklyh_strelok });
  proverka('«Следующего вопроса» и «Завершить» в строке нет',
    await p.locator('#trener-zavershit').count() === 0 &&
    !(await p.locator('.trener-upravlenie').innerText())
      .includes('Завершить'));
  proverka('счёта захода над кадром нет: он в поле',
    await p.locator('.pleyer-shapka .trener-schet-za').count() === 0 &&
    await p.locator('.trener-verh .trener-schet-za').count() === 1);

  // Полный экран: разворот самого поля средствами страницы. Браузерный
  // requestFullscreen во вложенном окне и на телевизоре не дают — кнопка
  // молчала, поэтому разворачиваемся своим классом на body.
  await p.locator('#trener-vo-ves-ekran').click();
  await p.waitForTimeout(300);
  const polnyj = await p.evaluate(() => {
    const m = document.getElementById('pleyer-mesto').getBoundingClientRect();
    return { klass: document.body.classList.contains('trener-vo-ves-ekran'),
             mesto: [Math.round(m.left), Math.round(m.top),
                     Math.round(m.width), Math.round(m.height)],
             okno: [window.innerWidth, window.innerHeight] };
  });
  proverka('значок разворачивает поле на весь экран', polnyj.klass === true,
    polnyj);
  proverka('в полном экране поле занимает экран целиком — от края до края',
    polnyj.mesto[0] === 0 && polnyj.mesto[1] === 0 &&
    Math.abs(polnyj.mesto[2] - polnyj.okno[0]) < 2 &&
    Math.abs(polnyj.mesto[3] - polnyj.okno[1]) < 2, polnyj);
  // Длинный вопрос выше экрана: поле прокручивается, а верхняя и нижняя
  // строки липнут к краям — счёт и значки сверху, стрелки и «Работа
  // над ошибками» снизу.
  const lipkie = await p.evaluate(() => {
    const m = document.getElementById('pleyer-mesto');
    const s = document.querySelector('.trener-verh');
    const u = document.querySelector('.trener-upravlenie');
    const viden = el => {
      const r = el.getBoundingClientRect();
      return r.top >= -1 && r.bottom <= window.innerHeight + 1;
    };
    const pos = [getComputedStyle(s).position, getComputedStyle(u).position];
    m.scrollTop = m.scrollHeight;
    const vidny = viden(s) && viden(u);
    m.scrollTop = 0;
    return { verh: pos[0], upr: pos[1], vidny,
             prokrutka: m.scrollHeight - m.clientHeight };
  });
  proverka('в полном экране строки липнут к краям и видны при прокрутке',
    lipkie.verh === 'sticky' && lipkie.upr === 'sticky' &&
    lipkie.vidny, lipkie);
  // Значок вопроса — тут же, в верхней строке: в полном экране подсказка
  // тоже нужна, а другого места для неё нет.
  proverka('значок вопроса виден и в полном экране',
    await p.locator('#trener-podskazka-znak').isVisible());
  // Нижняя строка поля в полном экране — та же: стрелки у правого
  // нижнего угла, а кнопки ошибок нет, пока ошибок нет.
  const osh_v_polnom = await p.evaluate(() => {
    const u = document.querySelector('.trener-upravlenie');
    const s = document.querySelector('.trener-strelki').getBoundingClientRect();
    return { est: !!u, pusto: u.querySelector('.trener-oshibki-v-pole').children.length === 0,
             strelki_vidny: s.bottom <= window.innerHeight + 1 && s.top >= 0 };
  });
  proverka('в полном экране без ошибок — одни стрелки в нижнем углу',
    osh_v_polnom.est === true && osh_v_polnom.pusto === true &&
    osh_v_polnom.strelki_vidny === true, osh_v_polnom);
  await p.keyboard.press('Escape');
  await p.waitForTimeout(300);
  proverka('Esc возвращает страницу из полного экрана',
    (await p.evaluate(() =>
      document.body.classList.contains('trener-vo-ves-ekran'))) === false &&
    (await p.evaluate(() => document.body.classList.contains(
      'pleylist-otkryto'))) === true);
  await p.locator('#trener-vo-ves-ekran').click();
  await p.waitForTimeout(300);
  await p.locator('#trener-vo-ves-ekran').click();
  await p.waitForTimeout(300);
  proverka('повторное нажатие значка возвращает страницу',
    (await p.evaluate(() =>
      document.body.classList.contains('trener-vo-ves-ekran'))) === false);
  // Ошибок пока нет — и на странице, и в полном экране кнопка ошибок
  // одна и та же: её просто нет, пока нечего разбирать.
  proverka('вернулись — кнопки ошибок по-прежнему нет, стрелки на месте',
    await p.evaluate(() => {
      const kop = document.querySelector('.trener-upravlenie .trener-oshibki-v-pole');
      return !!kop && kop.children.length === 0 &&
        document.querySelectorAll('.trener-strelki .trener-strelka').length === 2;
    }));
  proverka('над кадром во время захода — те же настройки, без счёта',
    bez_ya(await p.locator('#pleyer-zag').innerText()) ===
      'Даты и определения · Весь курс',
    await p.locator('#pleyer-zag').innerText());
  proverka('счёт «1 / N» стоит в поле и считается от всего набора',
    bez_ya(await p.locator('.trener-schet-za').innerText()) ===
      `1 / ${vsego}`,
    await p.locator('.trener-schet-za').innerText());

  // Верный ответ: балл, зелёная рамка, галочка, искры, статистика.
  await p.evaluate(() => {
    const z = shkZahodSostoyanie();
    document.querySelectorAll('#trener-igra a.trener-otvet')[z.verny].click();
  });
  await p.waitForTimeout(200);
  const posle_v = await p.evaluate(() => ({
    verno: shkZahodSostoyanie().verno,
    zelenaya: document.querySelectorAll('#trener-igra a.trener-otvet.verno').length,
    krasnyh: document.querySelectorAll('#trener-igra a.trener-otvet.neverno').length,
    galka: document.querySelectorAll('#trener-igra a.trener-otvet.verno .trener-galka svg').length,
    iskry: document.querySelectorAll('#trener-igra .trener-iskry i').length,
    // Подсказки под вопросом больше нет: она живёт в окне и открывается
    // значком вопроса из верхней строки поля.
    podskazka_pod_voprosom: document.querySelectorAll(
      '#trener-igra .trener-podrobnee, #trener-igra .trener-podrobno-telo')
      .length,
    otzyv: (document.querySelector('#trener-igra .trener-otzyv') || {}).className || '',
    kristallov: document.querySelectorAll('#trener-kristally svg.vzyt').length,
    kristallov_chislo: document.getElementById('trener-chislo').textContent.trim(),
    vpered: (document.getElementById('trener-vpered') || {}).tagName || '',
    znak_voprosa: (() => {
      const z = document.getElementById('trener-podskazka-znak');
      return { klass: z.className, teg: z.tagName, rol: z.getAttribute('role'),
               zapret: z.getAttribute('aria-disabled') };
    })(),
    nagrady: (() => {
      const n = document.getElementById('trener-nagrady');
      if(!n){ return {top:0, left:0, polovina:0}; }
      const r = n.getBoundingClientRect();
      const p2 = document.getElementById('pleyer').getBoundingClientRect();
      return { top: Math.round(r.top - p2.top),
               left: Math.round(r.left - p2.left),
               polovina: Math.round(p2.width / 2) };
    })(),
    // Стрелка стала живой. Вместе с кнопкой сброса они одного вида:
    // серая подложка — только у немых кнопок. Фокус со стрелки снимаем:
    // под фокусом у кнопки своя, подсвеченная подложка.
    fon_strelki: (() => {
      if (document.activeElement && document.activeElement.blur) {
        document.activeElement.blur();
      }
      return getComputedStyle(
        document.getElementById('trener-vpered')).backgroundColor;
    })(),
    fon_sbrosa: (() => {
      const s = document.getElementById('trener-sbros');
      return s ? getComputedStyle(s).backgroundColor : '';
    })(),
    osh: document.getElementById('stat-oshibok').textContent,
    schet: document.getElementById('trener-schet-za').textContent
      .replace(/\s+/g, ' ').trim(),
    vopros_viden: (() => {
      const g = document.getElementById('trener-igra');
      const v = document.querySelector('#trener-igra .trener-vopros-pod');
      return !v || v.getBoundingClientRect().top >= g.getBoundingClientRect().top - 2;
    })(),
    // Стрелки стоят в самом поле, в нижней строке у правого угла, —
    // наружу ничего не уходит: своей прокрутки у поля нет.
    strelki_v_pole: (() => {
      const ig = document.getElementById('pleyer').getBoundingClientRect();
      const s = document.getElementById('trener-vpered').getBoundingClientRect();
      return s.bottom <= ig.bottom + 2 && s.top >= ig.top - 2;
    })(),
  }));
  proverka('верный ответ подсвечен зелёным, с галочкой',
    posle_v.zelenaya === 1 && posle_v.galka === 1, posle_v);
  proverka('при верном ответе летят искры', posle_v.iskry >= 6, posle_v.iskry);
  proverka('верный ответ зажёг кристалл, и рядом встало число собранных',
    posle_v.kristallov === 1 && posle_v.kristallov_chislo === '1' &&
    posle_v.verno === 1,
    [posle_v.kristallov, posle_v.kristallov_chislo, posle_v.verno]);
  // До первого верного ответа счётчика кристаллов в поле не было вовсе
  // (серого кристалла с нулём не показываем): он появился с первым.
  proverka('счётчик кристаллов встал в левой группе верхней строки',
    posle_v.nagrady.top < 90 &&
    posle_v.nagrady.left < posle_v.nagrady.polovina, posle_v.nagrady);
  proverka('плашки-отзыва «Верно!» больше нет',
    posle_v.otzyv === '' &&
    !(await p.locator('#trener-igra').innerText()).includes('Верно!'));
  proverka('под вопросом никакой подсказки нет — она в окне',
    posle_v.podskazka_pod_voprosom === 0, posle_v.podskazka_pod_voprosom);
  proverka('живая стрелка и кнопка сброса — одной подложки',
    posle_v.fon_strelki === posle_v.fon_sbrosa,
    [posle_v.fon_strelki, posle_v.fon_sbrosa]);
  proverka('после ответа значок вопроса ожил — стал кнопкой подсказки',
    !posle_v.znak_voprosa.klass.includes('tuskly') &&
    posle_v.znak_voprosa.rol === 'button' &&
    posle_v.znak_voprosa.zapret === null, posle_v.znak_voprosa);
  proverka('стрелка вперёд стала живой ссылкой',
    posle_v.vpered === 'A', posle_v.vpered);
  proverka('стрелки стоят в самом поле — наружу ничего не уходит',
    posle_v.strelki_v_pole === true, posle_v.strelki_v_pole);
  proverka('вопрос остался виден — поле после ответа к низу не уехало',
    posle_v.vopros_viden, posle_v);
  proverka('счёт поля посчитал ответ: ошибок 0, «1 / N» на месте',
    posle_v.osh === '0' && posle_v.schet === `1 / ${vsego}`,
    [posle_v.osh, posle_v.schet]);
  // ---- подсказка: подробно, с учебником и ссылкой на урок ----
  console.log('ОКНО ПОДСКАЗКИ');
  // Подсказка открывается значком вопроса в верхней строке поля.
  await p.locator('#trener-podskazka-znak').click();
  await p.waitForTimeout(300);
  const otzyv = await p.evaluate(() => {
    const mesta = document.querySelector('#trener-okno-telo .trener-podrobno span');
    const ss = document.querySelector('#trener-okno-telo a.trener-video');
    const poln = document.querySelector('#trener-okno-telo .trener-poln');
    // Окно встаёт на место поля и того же размера — «размер и место
    // экрана теста»: смотрим по прямоугольникам.
    const k = document.getElementById('trener-okno-karta').getBoundingClientRect();
    const m = document.getElementById('pleyer-mesto').getBoundingClientRect();
    const ok = document.getElementById('trener-okno-podskazki');
    // Окно повторяет место и размер поля; если поле выше экрана — оно
    // сжимается по экрану, но не выходит за его края.
    const zhdem = Math.round(Math.min(m.bottom, window.innerHeight - 12) -
      Math.max(12, m.top));
    return { vidno: getComputedStyle(ok).display !== 'none',
             vysota_zhdem: zhdem,
             vokne: !!document.querySelector('#trener-okno-telo'),
             zag: document.getElementById('trener-okno-zag').textContent.trim(),
             poln: poln ? poln.textContent.trim() : '',
             polnyj: shkZahodSostoyanie().polny,
             par: shkZahodSostoyanie().par,
             mesta: mesta ? mesta.textContent.trim() : '',
             ss: ss ? ss.getAttribute('href') : '',
             ssTekst: ss ? ss.textContent.trim() : '',
             karta: [Math.round(k.left), Math.round(k.top),
                     Math.round(k.width), Math.round(k.height)],
             mesto: [Math.round(m.left), Math.round(m.top),
                     Math.round(m.width), Math.round(m.height)],
             v_igre: document.querySelectorAll('#trener-igra .trener-podrobno')
               .length + document.querySelectorAll(
                 '#trener-igra .trener-podrobno-telo').length };
  });
  proverka('значок вопроса открывает окно подсказки', otzyv.vidno === true,
    otzyv);
  proverka('в окне — подсказка по нынешнему вопросу',
    otzyv.vokne && otzyv.zag === 'Подсказка', otzyv.zag);
  proverka('окно встало на место поля и того же размера',
    otzyv.karta[0] === otzyv.mesto[0] && otzyv.karta[2] === otzyv.mesto[2] &&
    Math.abs(otzyv.karta[3] - otzyv.vysota_zhdem) < 2 &&
    otzyv.karta[1] >= otzyv.mesto[1] - 1 &&
    otzyv.karta[1] >= 11 && otzyv.karta[1] + otzyv.karta[3] <=
      (await p.evaluate(() => window.innerHeight)) - 11,
    [otzyv.karta, otzyv.mesto, otzyv.vysota_zhdem]);
  proverka('подсказка описывает событие целиком, как в учебнике',
    !!otzyv.poln && otzyv.poln.includes(otzyv.polnyj), otzyv.poln.slice(0, 90));
  const nom_para = (otzyv.mesta.match(/§\s*(\d+(?:\s*[-–—]\s*\d+)?)/) || [])[1];
  // Параграф есть не у всех вопросов: в конце учебников идут разделы
  // «Основные события» и «Словарь понятий», оттуда часть дат и
  // определений — у них параграфа нет, и строка подсказки короче.
  proverka('в подсказке названы учебник, страница и параграф',
    otzyv.mesta.includes('стр.') &&
    (otzyv.mesta.includes('История России') ||
     otzyv.mesta.includes('Всеобщая история')) &&
    (!!otzyv.par === !!nom_para),
    [otzyv.mesta, otzyv.par, nom_para]);
  // Ссылка ведёт на урок, и только туда, где урок записан: список
  // параграфов с уроками страница носит с собой (S_VIDEO — метки пунктов
  // со страницы видеоуроков). Уроков записано меньше, чем параграфов
  // в курсе, и ссылка в пустоту хуже её отсутствия.
  const metka_pary = String(nom_para).replace(/[–—]/g, '-').replace(/\s+/g, '');
  const s_video = await p.evaluate(() => {
    const m = document.documentElement.innerHTML.match(/var S_VIDEO = (\[[^\]]*\])/);
    return m ? JSON.parse(m[1]) : [];
  });
  const est_urok = s_video.some(n => String(n).replace(/§/g, '')
    .replace(/[–—]/g, '-').replace(/\s+/g, '') === metka_pary);
  proverka(est_urok ? 'по этому параграфу есть урок — и ссылка на него есть'
                    : 'урока по этому параграфу нет — и ссылки нет',
    est_urok ? otzyv.ss === 'видеоуроки.html#par-' + metka_pary
             : otzyv.ss === '',
    [otzyv.ss, est_urok, nom_para]);

  // Ссылка ведёт на урок именно этого параграфа.
  if (est_urok) {
    const vp = await b.newPage({ viewport: { width: 1500, height: 950 } });
    await vp.goto('file://' + path.resolve(path.dirname(stranica),
      otzyv.ss.split('#')[0]) + '#' + otzyv.ss.split('#')[1]);
    await vp.waitForTimeout(700);
    const privel = await vp.evaluate(() => {
      const a = document.querySelector('.pleylist.aktiven a.trek.aktiven') ||
        document.querySelector('a.trek.aktiven');
      return { aktivnyh: document.querySelectorAll('a.trek.aktiven').length,
               nomer: a ? (a.getAttribute('data-nomer') || '') : '',
               zag: document.getElementById('pleyer-zag').textContent };
    });
    // Номер пункта на странице видеоуроков — метка параграфа: «§ 33–34».
    // Пробелы вокруг тире в метке не значимы («33 – 34» — то же правило
    // тире), поэтому сравниваем без них.
    const bez_probelov_u_tire = s =>
      String(s).replace(/\s*([–—])\s*/g, '$1').replace(/\s+/g, ' ').trim();
    proverka('ссылка открывает урок этого параграфа',
      privel.aktivnyh === 1 &&
      bez_probelov_u_tire(bez_ya(privel.nomer)) ===
        bez_probelov_u_tire('§ ' + po_tire(nom_para)), privel);
    await vp.close();
  }

  // У каждого урока из списка метка на месте: ни одна ссылка не ведёт
  // в пустоту и ни одна метка не потеряется при пересборке.
  const vp2 = await b.newPage();
  await vp2.goto('file://' + path.resolve(path.dirname(stranica),
    'видеоуроки.html'));
  await vp2.waitForTimeout(500);
  const metok = await vp2.evaluate(() => [...document.querySelectorAll('a.trek[id]')]
    .map(a => a.id));
  const bez_metki = s_video.filter(n => !metok.includes('par-' + String(n)
    .replace(/§/g, '').replace(/[–—]/g, '-').replace(/\s+/g, '')));
  proverka('у каждого урока из списка страницы есть своя метка',
    bez_metki.length === 0 && s_video.length > 20,
    [s_video.length, bez_metki.slice(0, 5)]);
  await vp2.close();

  // Окно закрывается крестиком и Esc; настройки при этом остаются: окно
  // живёт поверх страницы само по себе.
  await p.locator('#trener-okno-podskazki a.trener-okno-zakryt').click();
  await p.waitForTimeout(250);
  proverka('крестик в окне закрывает подсказку',
    (await p.evaluate(() => getComputedStyle(document.getElementById(
      'trener-okno-podskazki')).display)) === 'none' &&
    (await p.evaluate(() => document.body.classList.contains(
      'pleylist-otkryto'))) === true);
  await p.locator('#trener-podskazka-znak').click();
  await p.waitForTimeout(250);
  await p.keyboard.press('Escape');
  await p.waitForTimeout(250);
  proverka('Esc закрывает окно подсказки, а настройки оставляет',
    (await p.evaluate(() => getComputedStyle(document.getElementById(
      'trener-okno-podskazki')).display)) === 'none' &&
    (await p.evaluate(() => document.body.classList.contains(
      'pleylist-otkryto'))) === true);

  await p.screenshot({ path: 'Временные/снимки/тренажёры-вопрос.png' });

  // Неверный ответ: красная отметка выбора, верный — зелёным, балл не растёт.
  await p.locator('#trener-vpered').click();
  await p.waitForTimeout(200);
  const vtor = await p.evaluate(() => shkZahodSostoyanie());
  proverka('стрелка вперёд ведёт ко второму вопросу',
    vtor.nomer === 2 && vtor.otvechen === null, vtor.nomer);
  // Обычно подсказка меняется. Исключение одно: год, к которому привязано
  // два события, — такой вопрос задаётся только со стороны события.
  const god_vtorogo = bez_ya(vtor.polny).split(' — ').pop().trim();
  proverka('стороны чередуются: подсказка сменилась (или у года два события)',
    vtor.podskazka !== perv.podskazka ||
    (vtor.podskazka === 'Когда это было?' && skolko_v_godu[god_vtorogo] > 1),
    [perv.podskazka, vtor.podskazka, god_vtorogo,
     skolko_v_godu[god_vtorogo]]);
  await p.evaluate(() => {
    const z = shkZahodSostoyanie();
    document.querySelectorAll('#trener-igra a.trener-otvet')[(z.verny + 1) % 4].click();
  });
  await p.waitForTimeout(200);
  const posle_n = await p.evaluate(() => ({
    ballov: shkZahodSostoyanie().verno,
    oshibok: shkZahodSostoyanie().oshibok,
    krasnyh: document.querySelectorAll('#trener-igra a.trener-otvet.neverno').length,
    pokazan: document.querySelectorAll('#trener-igra a.trener-otvet.pokazat').length,
    ikonok_galki: document.querySelectorAll('#trener-igra a.trener-otvet.pokazat .trener-galka svg').length,
    // На ошибке в поле ничего не раскрывается: подсказка ждёт нажатия
    // значка вопроса.
    okno_zakryto: getComputedStyle(
      document.getElementById('trener-okno-podskazki')).display === 'none',
    znak_zhivoj: !document.getElementById('trener-podskazka-znak')
      .className.includes('tuskly'),
    // После ошибки поле подводится к отмеченным ответам: видно и свой
    // неверный, и верный — тот, ради которого сюда и смотрят.
    otmechennye_vidny: (() => {
      const ig = document.getElementById('trener-igra').getBoundingClientRect();
      const otm = [...document.querySelectorAll('#trener-igra ' +
        'a.trener-otvet.pokazat, #trener-igra a.trener-otvet.neverno')];
      return otm.length === 2 && otm.every(a => {
        const r = a.getBoundingClientRect();
        return r.top >= ig.top - 2 && r.bottom <= ig.bottom + 2;
      });
    })(),
    osh: (document.getElementById('stat-oshibok') || {}).textContent,
    knopka: String(document.getElementById('trener-oshibki')
      .textContent).replace(/\s+/g, ' ').trim(),
    knopka_ssylka: document.getElementById('trener-oshibki').tagName,
  }));
  proverka('неверный ответ кристалла не даёт', posle_n.ballov === 1, posle_n.ballov);
  proverka('выбранный неверный — красный, верный показан зелёным с галочкой',
    posle_n.krasnyh === 1 && posle_n.pokazan === 1 && posle_n.ikonok_galki === 1,
    posle_n);
  proverka('на ошибке окно само не открывается — его зовут значком',
    posle_n.okno_zakryto === true && posle_n.znak_zhivoj === true, posle_n);
  proverka('видно и свой неверный ответ, и верный — поле к ним подведено',
    posle_n.otmechennye_vidny === true, posle_n.otmechennye_vidny);
  proverka('с первой ошибкой появилась кнопка — без числа в тексте',
    posle_n.knopka_ssylka === 'A' &&
    posle_n.knopka === 'Работа над ошибками',
    [posle_n.knopka_ssylka, posle_n.knopka]);
  proverka('счёт ошибок в поле посчитал ошибку: × 1',
    posle_n.osh === '1', posle_n.osh);
  // Классы движка рисует скрипт, статическая проверка вёрстки их не видит
  // (см. proverka_html.py) — поэтому смотрим на вычисленный вид: красный
  // и зелёный должны приходить из оформления, а не быть по умолчанию.
  const cveta = await p.evaluate(() => {
    const krasnyj = document.querySelector('#trener-igra a.trener-otvet.neverno');
    const zelenyj = document.querySelector('#trener-igra a.trener-otvet.pokazat');
    return {krasnyj: getComputedStyle(krasnyj).borderTopColor,
            zelenyj: getComputedStyle(zelenyj).borderTopColor};
  });
  proverka('зелёный и красный ответы различимы и взяты из оформления',
    cveta.krasnyj !== cveta.zelenyj && cveta.zelenyj.includes('62, 207, 142') &&
    cveta.krasnyj.includes('255, 107, 107'), cveta);
  await p.screenshot({ path: 'Временные/снимки/тренажёры-ошибки-ответ.png' });

  // В полном экране нижняя строка поля та же, что и на странице, и
  // оформлена как верхнее меню: та же подложка, те же скруглённые углы
  // и тот же воздух по краям, а не полоса от края до края.
  await p.locator('#trener-vo-ves-ekran').click();
  await p.waitForTimeout(300);
  const polosa_polnogo = await p.evaluate(() => {
    const u = document.querySelector('.trener-upravlenie');
    const su = getComputedStyle(u);
    const ru = u.getBoundingClientRect();
    const v = document.querySelector('.trener-verh');
    const sv = getComputedStyle(v);
    const rv = v.getBoundingClientRect();
    const k = document.querySelector('.trener-oshibki-v-pole a');
    const kr = k ? k.getBoundingClientRect() : null;
    const st = document.querySelector('.trener-strelki').getBoundingClientRect();
    const pod = document.getElementById('trener-oshibki-mesto');
    return { vidna: u.hidden === false,
             knopka: k ? k.textContent.replace(/\s+/g, ' ').trim() : '',
             v_odin_ryad: kr ? Math.abs((kr.top + kr.height / 2) -
               (st.top + st.height / 2)) < 6 : false,
             knopka_sleva: kr ? kr.right <= st.left : false,
             fon_stroki: su.backgroundColor, radius_stroki: su.borderTopLeftRadius,
             pod_polem_net: getComputedStyle(pod).display,
             vid_verh: [sv.borderTopLeftRadius, sv.backgroundColor, sv.padding],
             kraya: [Math.round(rv.left), Math.round(window.innerWidth - rv.right),
                     Math.round(rv.top)],
             kraya_niz: [Math.round(ru.left),
                         Math.round(window.innerWidth - ru.right),
                         Math.round(window.innerHeight - ru.bottom)] };
  });
  proverka('в полном экране кнопка ошибок — в один ряд со стрелками, слева',
    polosa_polnogo.vidna === true && polosa_polnogo.v_odin_ryad === true &&
    polosa_polnogo.knopka_sleva === true &&
    polosa_polnogo.knopka === 'Работа над ошибками', polosa_polnogo);
  // Подложки под нижними кнопками в полном экране нет: смотришь в одно
  // поле, и полоса под кнопками только мешала.
  proverka('подложки под нижней строкой в полном экране нет',
    polosa_polnogo.fon_stroki === 'rgba(0, 0, 0, 0)' &&
    polosa_polnogo.radius_stroki === '0px' &&
    polosa_polnogo.pod_polem_net === 'none', polosa_polnogo);
  // Верхняя строка — как меню страницы: та же подложка, те же скруглённые
  // углы, тот же воздух по краям. Нижняя — без подложки (см. выше).
  proverka('верхняя строка полного экрана — как меню страницы',
    polosa_polnogo.vid_verh[0] === '18px' &&
    polosa_polnogo.vid_verh[1] === 'rgb(22, 32, 43)' &&
    polosa_polnogo.vid_verh[2] === '12px 18px', polosa_polnogo.vid_verh);
  proverka('строки не липнут к краям экрана — по краям воздух',
    polosa_polnogo.kraya[0] > 0 &&
    polosa_polnogo.kraya[0] === polosa_polnogo.kraya[1] &&
    polosa_polnogo.kraya[2] >= 8 && polosa_polnogo.kraya[2] <= 20 &&
    polosa_polnogo.kraya_niz[0] === polosa_polnogo.kraya[0] &&
    polosa_polnogo.kraya_niz[2] >= 8 && polosa_polnogo.kraya_niz[2] <= 20,
    [polosa_polnogo.kraya, polosa_polnogo.kraya_niz]);
  await p.screenshot({ path: 'Временные/снимки/тренажёры-полный-экран-ошибка.png' });
  await p.locator('#trener-vo-ves-ekran').click();
  await p.waitForTimeout(300);

  // ---- листание: «Предыдущий вопрос» и «Дальше» ----
  console.log('ЛИСТАНИЕ ПО ВОПРОСАМ');
  await p.locator('#trener-nazad').click();
  await p.waitForTimeout(250);
  const nazad = await p.evaluate(() => ({
    nomer: shkZahodSostoyanie().nomer,
    zelenaya: document.querySelectorAll('#trener-igra a.trener-otvet.verno')
      .length,
    okno: getComputedStyle(
      document.getElementById('trener-okno-podskazki')).display,
  }));
  proverka('«Предыдущий вопрос» возвращает к первому — с его ответом',
    nazad.nomer === 1 && nazad.zelenaya === 1, nazad);
  proverka('на возврате окно подсказки закрыто — оно про прежний вопрос',
    nazad.okno === 'none', nazad.okno);
  await p.locator('#trener-vpered').click();
  await p.waitForTimeout(250);
  proverka('стрелка вперёд ведёт обратно ко второму вопросу',
    (await p.evaluate(() => shkZahodSostoyanie().nomer)) === 2);
  proverka('итог захода сам не показывается — заход можно прервать',
    (await p.evaluate(() => shkZahodSostoyanie().konec)) === false);

  // ---- цифровой таймер: один ряд со стрелками ----
  console.log('ЦИФРОВОЙ ТАЙМЕР');
  const vremya = await p.evaluate(() => {
    const v = document.getElementById('trener-vremya');
    const s = document.querySelector('.trener-strelki');
    const r = v.getBoundingClientRect(), rs = s.getBoundingClientRect();
    const txt = document.getElementById('trener-vremya-podpis').textContent;
    return {est: !!v, sost: shkVremyaSostoyanie(), txt,
      odna_stroka: Math.abs((r.top+r.height/2)-(rs.top+rs.height/2)) < 3,
      po_seredine: getComputedStyle(document.getElementById('trener-vremya-podpis')).textAlign};
  });
  proverka('цифровой таймер стоит в одном ряду со стрелками',
    vremya.est && vremya.odna_stroka, vremya);
  proverka('таймер показывает только цифровое время и центрирован',
    /^\d{2}:\d{2}$/.test(vremya.txt) && vremya.po_seredine === 'center', vremya);
  proverka('таймер движется только внутри захода',
    vremya.sost.idyot === true && vremya.sost.cikl === 60000, vremya.sost);
  const krug_vremya = await p.evaluate(() =>
    [shkVremyaDolya(0, 60000), shkVremyaDolya(0, 61000)]);
  proverka('по достижении минуты время остаётся на 01:00',
    krug_vremya[0] >= 1 && krug_vremya[1] > 1, krug_vremya);
  await p.screenshot({ path: 'Временные/снимки/тренажёры-полоса-времени.png' });

  // ---- сброс результатов: только по подтверждению ----
  console.log('СБРОС РЕЗУЛЬТАТОВ');
  const do_sbrosa = await p.evaluate(() => ({
    oshibok: document.getElementById('stat-oshibok').textContent,
    kristallov: document.querySelectorAll('#trener-kristally svg.vzyt').length,
    kristall_chislo: document.getElementById('trener-chislo').textContent,
  }));
  const sbras_v_niz = await p.evaluate(() => {
    const k = document.getElementById('trener-sbros');
    const niz = k.closest('.panel-niz');
    const r = k.getBoundingClientRect();
    const pn = document.getElementById('pleylist-panel').getBoundingClientRect();
    // Область списка ищем именно в панели настроек: на странице есть
    // ещё панель меню, и у неё свой .panel-telo.
    const telo = document.querySelector('#pleylist-panel .panel-telo')
      .getBoundingClientRect();
    return { v_paneli: !!k.closest('#pleylist-panel'),
             v_nizu: !!niz,
             // Низ кнопки — у нижнего края экрана и панели.
             do_niza: Math.round(r.bottom) >= Math.round(pn.bottom) - 20 &&
                      Math.round(r.bottom) <= Math.round(pn.bottom),
             // И вне прокручиваемой области: сколько бы настроек ни
             // набралось, кнопка не уезжает.
             vne_spiska: r.top >= telo.bottom - 1,
             vo_vsyu_shirinu: Math.round(r.width) >=
               Math.round(pn.width) - 40,
             knopok_pod_polem: document.querySelectorAll(
               '.trener-statistika #trener-sbros').length };
  });
  proverka('сброс — в панели настроек, у самого нижнего края экрана',
    sbras_v_niz.v_paneli === true && sbras_v_niz.v_nizu === true &&
    sbras_v_niz.do_niza === true && sbras_v_niz.vne_spiska === true,
    sbras_v_niz);
  proverka('кнопка сброса идёт во всю ширину панели, под полем её нет',
    sbras_v_niz.vo_vsyu_shirinu === true &&
    sbras_v_niz.knopok_pod_polem === 0, sbras_v_niz);
  // Линия раздела над кнопкой сброса стоит вдвое выше прежнего: кнопка
  // читалась приклеенной к линии.
  proverka('линия над сбросом поднята вдвое — 24 px воздуха',
    await p.evaluate(() => getComputedStyle(
      document.querySelector('#pleylist-panel .panel-niz')).paddingTop) === '24px',
    await p.evaluate(() => getComputedStyle(
      document.querySelector('#pleylist-panel .panel-niz')).paddingTop));
  proverka('раздела «Результаты» и пяти строк с «Отменой» нет — одна кнопка',
    await p.locator('#nastr-sbros').count() === 0 &&
    await p.locator('#nastr-sbros-podtverdit').count() === 0 &&
    await p.locator('#pleylist-panel .panel-niz a').count() === 1);
  await p.locator('#trener-sbros').click();
  await p.waitForTimeout(200);
  proverka('первое нажатие предупреждает и просит нажать ещё раз',
    bez_ya(await p.locator('#trener-sbros').innerText()) ===
      'Результаты тестирования будут сброшены. ' +
      'Нажмите ещё раз, чтобы подтвердить' &&
    (await p.evaluate(() => document.getElementById('trener-sbros')
      .getAttribute('data-zhdet'))) === '1');
  proverka('предупреждение ничего не стирает',
    (await p.evaluate(() => document.querySelectorAll(
      '#trener-kristally svg.vzyt').length)) === do_sbrosa.kristallov,
    do_sbrosa);
  await p.locator('#trener-sbros').click();
  await p.waitForTimeout(250);
  const posle_sbrosa = await p.evaluate(() => ({
    oshibok: document.getElementById('stat-oshibok').textContent,
    kristallov: document.querySelectorAll('#trener-kristally svg.vzyt').length,
    nagrady: getComputedStyle(document.getElementById('trener-nagrady')).display,
    priglashenie: getComputedStyle(
      document.getElementById('trener-priglashenie')).display !== 'none',
    vid: shkNastroykiState().vid,
    schet_skryt: document.getElementById('trener-schet-za').hidden,
  }));
  proverka('«Сбросить» обнуляет пройденное, кристаллы и ошибки',
    do_sbrosa.kristallov > 0 && posle_sbrosa.oshibok === '0' &&
    posle_sbrosa.kristallov === 0 && posle_sbrosa.nagrady === 'none',
    [do_sbrosa, posle_sbrosa]);
  proverka('после сброса счётчик кристаллов снова спрятан — нуля не видно',
    posle_sbrosa.nagrady === 'none', posle_sbrosa.nagrady);
  proverka('после сброса в поле снова приглашение, а счёта вопроса нет',
    posle_sbrosa.priglashenie === true && posle_sbrosa.schet_skryt === true,
    posle_sbrosa);
  proverka('сброс не тронул настройки — вид остался прежним',
    posle_sbrosa.vid === 'vse', posle_sbrosa.vid);
  proverka('после сброса кнопка снова обычная — «Сбросить результаты теста»',
    bez_ya(await p.locator('#trener-sbros').innerText()) ===
      'Сбросить результаты теста' &&
    (await p.evaluate(() => document.getElementById('trener-sbros')
      .getAttribute('data-zhdet'))) !== '1');

  // ---- «Работа над ошибками»: живёт в поле и оживает с первой ошибкой ----
  console.log('РАБОТА НАД ОШИБКАМИ');
  await p.locator('#trener-nachat').click();
  // Курсор уводим с поля: под мышью у плашки и у кнопки своя, жёлтая
  // рамка, и мерки с неё снимать нельзя.
  await p.mouse.move(4, 4);
  await p.waitForTimeout(300);
  proverka('пока ошибок нет, «Работы над ошибками» нет вовсе',
    await p.locator('#trener-oshibki').count() === 0 &&
    (await p.evaluate(() => document.querySelector('.trener-oshibki-v-pole')
      .children.length)) === 0 &&
    (await p.evaluate(() => document.querySelector('.trener-upravlenie')
      .hidden)) === false);
  await p.evaluate(() => {
    const z = shkZahodSostoyanie();
    document.querySelectorAll('#trener-igra a.trener-otvet')[(z.verny + 1) % 4]
      .click();
  });
  await p.waitForTimeout(250);
  const zhivaya = await p.evaluate(() => {
    const a = document.getElementById('trener-oshibki');
    const s = document.getElementById('trener-sbros');
    const ra = a.getBoundingClientRect();
    const rs = s.getBoundingClientRect();
    // Плашка-образец — обычная, невыбранная: не красная и не зелёная.
    const obyknovennaya = document.querySelector('#trener-igra ' +
      'a.trener-otvet:not(.verno):not(.neverno):not(.pokazat)') ||
      document.querySelector('#trener-igra a.trener-otvet');
    const plitka = obyknovennaya.getBoundingClientRect();
    const oblast = document.querySelector('#trener-igra .trener-otvety')
      .getBoundingClientRect();
    const st = getComputedStyle(a);
    const mesto = document.getElementById('trener-oshibki-mesto');
    const mr = mesto.getBoundingClientRect();
    const pole = document.getElementById('pleyer').getBoundingClientRect();
    const polosa = document.querySelector('.pl-razdely .pl-zagolovok')
      .getBoundingClientRect();
    return { tag: a.tagName,
             pod_polem: !!a.closest('.trener-oshibki-pod') &&
               mr.top >= pole.bottom - 1,
             v_pole: !!a.closest('#trener-igra'),
             otstup_sverhu: Math.round(mr.top - pole.bottom),
             otstup_snizu: Math.round(polosa.top - mr.bottom),
             vo_vsyu_shirinu: Math.round(ra.width) === Math.round(oblast.width),
             tekst: a.textContent.replace(/\s+/g, ' ').trim(),
             vysota: [Math.round(ra.height), Math.round(plitka.height)],
             obvodka: st.borderTopWidth + ' ' + st.borderTopColor,
             radius: st.borderTopLeftRadius,
             prozrachno: st.backgroundColor === 'rgba(0, 0, 0, 0)',
             kak_plitka: (() => {
               const x = getComputedStyle(obyknovennaya);
               return x.borderTopWidth + ' ' + x.borderTopColor;
             })(),
             radius_plitki: getComputedStyle(obyknovennaya).borderTopLeftRadius,
             // Рост однострочной плашки: строка + поля + рамка.
             kak_odnostrochnaya: Math.round(
               parseFloat(getComputedStyle(obyknovennaya).lineHeight) +
               parseFloat(getComputedStyle(obyknovennaya).paddingTop) * 2 +
               parseFloat(getComputedStyle(obyknovennaya).borderTopWidth) * 2),
             po_seredine: getComputedStyle(a).textAlign };
  });
  proverka('с первой же ошибкой кнопка появилась под полем, во всю его ширину',
    zhivaya.tag === 'A' && zhivaya.pod_polem === true &&
    zhivaya.v_pole === false && zhivaya.vo_vsyu_shirinu === true &&
    zhivaya.tekst === 'Работа над ошибками',
    zhivaya);
  proverka('под полем кнопка стоит с теми же отступами: 24 сверху, 46 снизу',
    zhivaya.otstup_sverhu === 24 && zhivaya.otstup_snizu === 46, zhivaya);
  proverka('кнопка ошибок — обычная кнопка с красной обводкой',
    zhivaya.radius === '12px' &&
    zhivaya.obvodka.includes('rgb(255, 107, 107)') && zhivaya.prozrachno === false,
    [zhivaya.obvodka, zhivaya.radius, zhivaya.prozrachno]);
  proverka('кнопка ошибок — ростом с однострочную плашку, надпись по середине',
    zhivaya.vysota[0] === zhivaya.kak_odnostrochnaya &&
    zhivaya.po_seredine === 'center',
    [zhivaya.vysota[0], zhivaya.kak_odnostrochnaya]);
  await p.locator('#trener-oshibki').click();
  await p.waitForTimeout(300);
  const rabota = await p.evaluate(() => ({
    vid: shkNastroykiState().vid, voprosov: shkUroki().length,
    vsego: shkZahodSostoyanie().vsego,
    nadpis: document.getElementById('pleyer-zag').textContent,
  }));
  proverka('нажатие запускает заход только по ошибкам',
    rabota.vid === 'oshibki' && rabota.vsego === 1 && rabota.voprosov === 1,
    rabota);
  proverka('в надписи над кадром видно, что это работа над ошибками',
    rabota.nadpis.includes('Работа над ошибками'), rabota.nadpis);
  const klyuch = await p.evaluate(() => shkZahodSostoyanie().klyuch);
  await p.evaluate(() => {
    const z = shkZahodSostoyanie();
    document.querySelectorAll('#trener-igra a.trener-otvet')[z.verny].click();
  });
  await p.waitForTimeout(250);
  const chistka = await p.evaluate((k) => ({
    oshibok: shkNastroykiState().oshibki.length,
    ushyol: shkNastroykiState().oshibki.indexOf(k) < 0,
    stat_osh: document.getElementById('stat-oshibok').textContent,
    est: !!document.getElementById('trener-oshibki'),
    v_pole: document.querySelector('.trener-oshibki-v-pole').children.length,
  }), klyuch);
  proverka('верный ответ убирает вопрос из ошибок',
    chistka.ushyol && chistka.oshibok === 0, chistka);
  proverka('ошибок больше нет — «Работа над ошибками» пропала снова',
    chistka.stat_osh === '0' && chistka.est === false && chistka.v_pole === 0,
    chistka);
  proverka('на последнем вопросе стрелка вперёд зовёт показать итог',
    (await p.locator('#trener-vpered').getAttribute('aria-label')) === 'Показать итог',
    await p.locator('#trener-vpered').getAttribute('aria-label'));
  await p.locator('#trener-vpered').click();
  await p.waitForTimeout(250);
  const itog = bez_ya(await p.locator('#trener-igra').innerText());
  proverka('итог — «Все вопросы пройдены», без «Ещё захода» и баллов',
    itog.includes('Все вопросы пройдены') && !itog.includes('Ещё заход') &&
    !itog.includes('Балл') && itog.includes('Верно'), itog);
  // Полоса времени живёт с заходом: на итоге её нет вовсе (нижней строки
  // поля там тоже нет), а минута встала.
  const vremya_na_itoge = await p.evaluate(() => ({
    net: document.querySelectorAll('#trener-vremya').length === 0,
    idyot: shkVremyaSostoyanie().idyot,
  }));
  proverka('на итоге полосы времени нет — минута кончилась вместе с заходом',
    vremya_na_itoge.net === true && vremya_na_itoge.idyot === false,
    vremya_na_itoge);
  // На итоге «Работа над ошибками» одна — в самом итоге: нижней строки
  // поля там нет вовсе (стрелки живут с вопросом), а счёт ошибок,
  // как и счёт вопросов, кончился вместе с заходом.
  const itog_karta = await p.evaluate(() => ({
    vsego: document.querySelectorAll('a[onclick="return shkOshibki()"]').length,
    oshibok: shkNastroykiState().oshibki.length,
    id_net: document.querySelectorAll('#trener-oshibki').length,
    niz_stroki_net: document.querySelectorAll('.trener-upravlenie').length,
    schet_oshibok: document.getElementById('trener-oshibki-schet').hidden,
    schet_voprosov: document.getElementById('trener-schet-za').hidden,
  }));
  proverka('на итоге кнопка ошибок одна (или её нет, коли ошибок нет)',
    itog_karta.vsego === (itog_karta.oshibok ? 1 : 0) &&
    itog_karta.id_net === 0 &&
    itog_karta.niz_stroki_net === 0 && itog_karta.schet_oshibok === true &&
    itog_karta.schet_voprosov === true, itog_karta);

  // ---- смена настройки убирает незаконченный заход ----
  console.log('СМЕНА НАСТРОЙКИ');
  await p.locator('#pleylist-panel a[data-vid="daty"]').click();
  await p.waitForTimeout(150);
  proverka('смена настройки убирает незаконченный заход',
    await p.locator('#trener-igra.vidna').count() === 0 &&
    await p.locator('#trener-priglashenie').isVisible());
  proverka('«Только даты»: в наборе остались одни даты',
    bez_ya(await p.locator('#pleyer-zag').innerText()) ===
      'Только даты · Весь курс' &&
    (await p.evaluate(() => shkUroki().length)) === chislo_d,
    await p.evaluate(() => shkUroki().length));
  // Отвеченное не стирается сменой набора: в поле — счёт по новому
  // набору, и он не больше, чем в этом наборе вопросов.
  const v_nabore = await p.evaluate(() => shkUroki().length);
  proverka('в новом наборе — только его вопросы (остаток считается по нему)',
    v_nabore === chislo_d, v_nabore);
  // Даты — короткие ответы: две плашки в ряд, четыре ответа двумя
  // ровными рядами по два.
  await p.locator('#trener-nachat').click();
  await p.waitForTimeout(250);
  const setka_d = await p.evaluate(() => ({
    pod: document.querySelector('.trener-vopros-pod')?.textContent.trim() || '',
    zag: document.querySelector('.trener-vopros-zag').textContent.trim(),
  }));
  proverka('в наборе «Только даты» подзаголовка нет, вопрос — про год или событие',
    setka_d.pod === '' && !['Дата', 'Определение'].includes(setka_d.zag), setka_d);
  // Даты — ответы в одну строку: с ошибкой кнопка ошибок встаёт ростом
  // ровно с такую плашку.
  await p.evaluate(() => {
    const z = shkZahodSostoyanie();
    document.querySelectorAll('#trener-igra a.trener-otvet')[(z.verny + 1) % 4]
      .click();
  });
  await p.mouse.move(4, 4);
  await p.waitForTimeout(250);
  const rost = await p.evaluate(() => {
    const k = document.getElementById('trener-oshibki');
    const o = document.querySelector('#trener-igra a.trener-otvet');
    return { knopka: k ? Math.round(k.getBoundingClientRect().height) : null,
             plitka: o ? Math.round(o.getBoundingClientRect().height) : null };
  });
  proverka('кнопка ошибок и однострочная плашка — одного роста',
    rost.knopka !== null && rost.knopka === rost.plitka, rost);

  // ---- годы: разделение тысяч и «г.»/«гг.» ----
  // Год пишется как в учебнике: 1.552, а не 1552, и с пометкой «г.»
  // (у промежутка — «гг.»). Идём по вопросам-датам и собираем всё, что
  // в них стоит на месте года.
  console.log('ГОДЫ');
  const gody = { varianty: [], polnye: [] };
  for (let i = 0; i < 10; i++) {
    const z = await p.evaluate(() => {
      const s = shkZahodSostoyanie();
      return s && !s.konec ? { varianty: s.varianty, polny: s.polny,
        zag: document.querySelector('.trener-vopros-zag').textContent.trim(),
        pod: '' }
        : null;
    });
    if (!z) { break; }
    if (z.pod === '') {
      gody.varianty.push(...z.varianty);
    }
    gody.polnye.push(z.polny);
    await p.evaluate(() => {
      const s = shkZahodSostoyanie();
      document.querySelectorAll('#trener-igra a.trener-otvet')[s.verny].click();
    });
    await p.waitForTimeout(150);
    if (i < 9) {
      await p.locator('#trener-vpered').click();
      await p.waitForTimeout(200);
    }
  }
  // Разряды года разделены пробелом («1 679»); у промежутка — тире (оно
  // может быть и «—», и «–»). За «г.» или «гг.» идёт точка. Пробел может
  // быть и нерушимым: год не должен разрываться по строке.
  const shablon_goda = new RegExp('^[0-9]{1,3}([ \\u00a0][0-9]{3})*' +
    '(\\s*[—–-]\\s*[0-9]{1,3}([ \\u00a0][0-9]{3})*)? (г\\.|гг\\.)$');
  const gody_v_otvetah = gody.varianty.filter(s => /^[0-9]/.test(s));
  proverka(`в вопросах-датах годы пишутся с «г.» (нашли ${gody_v_otvetah.length})`,
    gody_v_otvetah.length >= 4, gody.varianty.slice(0, 5));
  proverka('каждый год — с разделением разрядов и пометкой «г.»/«гг.»',
    gody_v_otvetah.every(s => shablon_goda.test(s)),
    gody_v_otvetah.filter(s => !shablon_goda.test(s)));
  proverka('тысячи отделены пробелом — «1 679», а не «1.679» и не «1679»',
    gody_v_otvetah.every(s => {
      const pervoe = Number(String(s).split(/[\.\s\u00a0]/)[0]);
      return !(pervoe >= 1000) || /[ \u00a0]/.test(s);
    }) && gody_v_otvetah.some(s => /[0-9][ \u00a0][0-9]{3}/.test(s)) &&
    gody_v_otvetah.every(s => !/[0-9]\.[0-9]{3}/.test(s)),
    gody_v_otvetah.slice(0, 5));
  proverka('в подсказке год тоже с «г.» — и когда год, и когда событие',
    gody.polnye.every(s => s.split(' — ').every(ch =>
      !/^[0-9]/.test(ch) || shablon_goda.test(ch))),
    gody.polnye.filter(s => !s.split(' — ').every(ch =>
      !/^[0-9]/.test(ch) || shablon_goda.test(ch))).slice(0, 3));
  // Проверка прошла по десяти вопросам — начинаем заход заново: дальше
  // он проверяется с чистого вопроса.
  await p.evaluate(() => shkNachat());
  await p.waitForTimeout(200);

  // ---- «Переходить к следующему вопросу сам» ----
  console.log('ПРОХОЖДЕНИЕ: ПЕРЕХОДИТЬ САМ');
  proverka('строка-флажок стоит без заголовка — «Прохождения» в панели нет',
    !(await p.locator('#pleylist-panel').innerText()).includes('Прохождение') &&
    bez_ya(await p.locator('#nastr-avto').innerText()) ===
      'Переходить к следующему вопросу автоматически' &&
    await p.locator('#nastr-avto .nastr-galochka svg').count() === 1);
  // Строка настройки — тем же шрифтом, что надпись раздела «Выбор
  // учебника»: и ростом, и цветом. Флажок — одного роста с кружочками
  // выбора и по первой строке текста: настройка длинная, и по середине
  // всего текста он уезжал бы вниз.
  const seryj = await p.evaluate(() => {
    const a = document.querySelector('#nastr-avto .nastr-tekst');
    const b = [...document.querySelectorAll('#pleylist-panel .nastr-zag')]
      .find(x => x.textContent.trim() === 'Выбор учебника');
    const sa = getComputedStyle(a), sb = getComputedStyle(b);
    const g = document.querySelector('#nastr-avto .nastr-galochka');
    const k = document.querySelector('#pleylist-panel .nastr-kolco svg');
    const gr = g.getBoundingClientRect(), kr = k.getBoundingClientRect();
    const tr = a.getBoundingClientRect();
    return { kega: [sa.fontSize, sb.fontSize], cvet: [sa.color, sb.color],
             kvadrat: [Math.round(gr.width), Math.round(gr.height)],
             krug: [Math.round(kr.width), Math.round(kr.height)],
             po_pervoj_stroke: Math.abs((gr.top + gr.height / 2) -
               (tr.top + parseFloat(sa.lineHeight) / 2)) < 3 };
  });
  proverka('текст настройки — как «Выбор учебника»: и ростом, и цветом',
    seryj.kega[0] === seryj.kega[1] && seryj.cvet[0] === seryj.cvet[1] &&
    seryj.kega[0] === '21px' && seryj.cvet[0] === 'rgb(139, 149, 165)', seryj);
  proverka('квадратик флажка — одного размера с кружочками',
    seryj.kvadrat[0] === seryj.krug[0] && seryj.kvadrat[1] === seryj.krug[1],
    [seryj.kvadrat, seryj.krug]);
  proverka('флажок выровнен по первой строке текста, а не по середине',
    seryj.po_pervoj_stroke === true, seryj);
  proverka('по умолчанию галочка снята — решение идёт в своём темпе',
    (await p.evaluate(() => shkNastroykiState().avto)) === false &&
    await p.locator('#nastr-avto.aktiven').count() === 0);
  await p.locator('#nastr-avto').click();
  await p.waitForTimeout(150);
  proverka('нажатие ставит галочку',
    (await p.evaluate(() => shkNastroykiState().avto)) === true &&
    await p.locator('#nastr-avto.aktiven').count() === 1);
  // Верный ответ — вопрос сменяется сам; ошиблись — остаёмся на месте
  // (рассказ надо прочитать). Заход уже идёт (даты): продолжаем его.
  await p.evaluate(() => { if(!shkZahodSostoyanie()){ shkNachat(); } });
  await p.waitForTimeout(200);
  const a_bylo = await p.evaluate(() => shkZahodSostoyanie().nomer);
  await p.evaluate(() => {
    const z = shkZahodSostoyanie();
    document.querySelectorAll('#trener-igra a.trener-otvet')[z.verny].click();
  });
  await p.waitForTimeout(150);
  const az = await p.evaluate(() => shkZahodSostoyanie().nomer);
  await p.waitForTimeout(1300);
  const ap = await p.evaluate(() => shkZahodSostoyanie().nomer);
  proverka('при верном ответе вопрос сменяется сам',
    az === a_bylo && ap === a_bylo + 1, { bylo: az, stalo: ap });
  const o_bylo = await p.evaluate(() => shkZahodSostoyanie().nomer);
  await p.evaluate(() => {
    const z = shkZahodSostoyanie();
    document.querySelectorAll('#trener-igra a.trener-otvet')[(z.verny + 1) % 4]
      .click();
  });
  await p.waitForTimeout(150);
  const ao = await p.evaluate(() => shkZahodSostoyanie().nomer);
  await p.waitForTimeout(1300);
  const aposle = await p.evaluate(() => shkZahodSostoyanie().nomer);
  proverka('при ошибке перехода нет — рассказ читают на месте',
    ao === o_bylo && aposle === o_bylo, { bylo: ao, stalo: aposle });
  await p.locator('#nastr-avto').click();
  await p.waitForTimeout(150);
  proverka('повторное нажатие снимает галочку',
    (await p.evaluate(() => shkNastroykiState().avto)) === false &&
    await p.locator('#nastr-avto.aktiven').count() === 0);

  // ---- панель закрывается и возвращается кнопкой ----
  console.log('ПАНЕЛЬ');
  await p.locator('#pleylist-panel .panel-verh a.panel-zakryt').click();
  await p.waitForTimeout(400);
  proverka('крестик закрывает настройки',
    await p.locator('body.pleylist-otkryto').count() === 0);
  await p.locator('a.nastr-knopka').click();
  await p.waitForTimeout(400);
  proverka('кнопка настроек возвращает панель',
    await p.locator('body.pleylist-otkryto').count() === 1);
  // Значок настроек — как значок меню: второе нажатие прячет панель,
  // третье возвращает.
  await p.locator('a.nastr-knopka').click();
  await p.waitForTimeout(400);
  proverka('повторное нажатие значка настроек прячет панель',
    await p.locator('body.pleylist-otkryto').count() === 0);
  await p.locator('a.nastr-knopka').click();
  await p.waitForTimeout(400);
  proverka('третье нажатие снова открывает панель',
    await p.locator('body.pleylist-otkryto').count() === 1);
  await p.close();

  // ---- узкое окно: панель сама не открывается ----
  console.log('УЗКОЕ ОКНО (900)');
  const u = await b.newPage({ viewport: { width: 900, height: 1200 } });
  u.on('console', m => { if (m.type() === 'error') bedy.push(m.text()); });
  u.on('pageerror', e => bedy.push('js: ' + e.message));
  await u.goto(adres);
  await u.waitForTimeout(300);
  proverka('на узком окне панель закрыта — видно поле',
    await u.locator('body.pleylist-otkryto').count() === 0);
  proverka('на узком окне счёт поля тот же — в верхней строке поля',
    await u.locator('.trener-statistika').count() === 0 &&
    await u.locator('#stat-ostalos').count() === 0 &&
    await u.locator('.trener-verh #stat-oshibok').count() === 1);
  await u.locator('a.nastr-knopka').click();
  await u.waitForTimeout(400);
  proverka('кнопка настроек открывает панель и здесь',
    await u.locator('body.pleylist-otkryto').count() === 1);
  await u.locator('#pleylist-panel a[data-uch="История России"]').click();
  await u.waitForTimeout(200);
  proverka('«Ограничить до» с полем поиска видны и в узкой панели',
    await u.locator('#nastr-par[hidden]').count() === 0 &&
    await u.locator('#nastr-poisk').isVisible());
  await u.screenshot({ path: 'Временные/снимки/тренажёры-узко.png' });
  await u.close();

  console.log('ОШИБКИ КОНСОЛИ: ' + (bedy.length ? bedy.join(' | ') : 'нет'));
  await b.close();
  console.log(oshibki ? `ИТОГО: ${oshibki} ошибок` : 'ИТОГО: всё сходится');
})();
