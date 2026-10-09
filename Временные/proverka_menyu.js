// Боковое меню и панель плейлиста: проверка с вердиктами.
//
// Проверяем всё, на что жаловались: задвоенные разделительные линии,
// плашки с фоном и жёлтые обводки у строк, разное поведение крестика
// в двух панелях, а также маленькую строку с именем и целью и кнопку
// «Закрыть» на уведомлении. Не «печатаем замеры», а сравниваем с тем,
// как должно быть, и в конце считаем ошибки.
//
//   node Временные/proverka_menyu.js "Проект/База данных/HTML/5 класс/История/видеоуроки.html"
const fs = require('fs');
const path = require('path');
const { chromium } = require('./плейрайт.js');

const put = process.argv[2] ||
  'Проект/База данных/HTML/5 класс/История/видеоуроки.html';
const kuda = 'Временные/снимки';
fs.mkdirSync(kuda, { recursive: true });

let oshibki = 0;
const proverka = (chto, uslovie, fakticheski) => {
  console.log((uslovie ? '  ок   ' : '  ОШИБКА ') + chto +
              (uslovie ? '' : ' → ' + JSON.stringify(fakticheski)));
  if (!uslovie) oshibki++;
};
const rgb = t => (t.match(/\d+/g) || []).map(Number);
const ne_siniy = t => {
  const c = rgb(t);
  return !c.length || c[2] - c[0] < 40;
};

// Полноширинные линии: разделители панели. Рамки кнопок и крестика
// сюда не попадают — они шириной со кнопку, а не с панель.
// Прозрачные рамки строк списков тоже не считаем: у каждой строки своя
// рамка 3 px (место под жёлтую), но в покое она прозрачная — линии нет,
// а разделитель — это линия, которую видно.
async function linii(p, panel) {
  return p.evaluate((sel) => {
    const kor = document.querySelector(sel);
    if (!kor) return null;
    const shirina = kor.getBoundingClientRect().width;
    const naideno = [];
    const vidno = c => c && c !== 'transparent' &&
                      !/rgba\(\s*0,\s*0,\s*0,\s*0\s*\)/.test(c);
    kor.querySelectorAll('*').forEach(el => {
      const s = getComputedStyle(el);
      const w = el.getBoundingClientRect().width;
      if (w < shirina * 0.7) return;
      // Разделитель — это линия шириной с панель: рамка сверху или
      // снизу. У строк списков рамка идёт по всему краю (видна и
      // слева, и справа) — это не линия, а обводка строки: её не
      // считаем. Стиль рамки проверяем: браузер отдаёт цвет рамки
      // даже там, где рамки нет вовсе (color = currentColor).
      const stor = (w, st, c) => parseFloat(w) > 0 && st !== 'none' && vidno(c);
      const po_krugu = stor(s.borderLeftWidth, s.borderLeftStyle, s.borderLeftColor) &&
                       stor(s.borderRightWidth, s.borderRightStyle, s.borderRightColor);
      if (po_krugu) return;
      if (parseFloat(s.borderBottomWidth) > 0 &&
          s.borderBottomStyle !== 'none' && vidno(s.borderBottomColor))
        naideno.push(el.className || el.tagName);
      if (parseFloat(s.borderTopWidth) > 0 &&
          s.borderTopStyle !== 'none' && vidno(s.borderTopColor))
        naideno.push(el.className || el.tagName);
    });
    return naideno;
  }, panel);
}


async function krestik(p, panel) {
  return p.evaluate((sel) => {
    const a = document.querySelector(sel + ' .panel-zakryt');
    if (!a) return null;
    const s = getComputedStyle(a);
    return { ramka: s.borderTopWidth + ' ' + s.borderTopColor,
             fon: s.backgroundColor, kraska: s.color };
  }, panel);
}

// Строка списка: подложка, рамки, обводка, цвет.
async function stil_stroki(p, selektor) {
  return p.evaluate((sel) => {
    const el = document.querySelector(sel);
    if (!el) return null;
    const s = getComputedStyle(el);
    return {
      fon: s.backgroundColor,
      ramki: [s.borderTopWidth, s.borderRightWidth, s.borderBottomWidth,
              s.borderLeftWidth].join(' '),
      polosa: s.borderLeftColor,
      obvodka: s.outlineStyle + ' ' + s.outlineWidth,
      kraska: s.color,
    };
  }, selektor);
}

const stroka_chistaya = s => s &&
  (s.fon === 'rgba(0, 0, 0, 0)' || s.fon === 'transparent') &&
  /^0px 0px 0px 0px$/.test(s.ramki) &&
  /^(none|0px)/.test(s.obvodka) && ne_siniy(s.kraska);

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
  console.log('проверяем: ' + put);

  // --- строка с именем и целью
  console.log('=== строка с именем и целью');
  const stroka = await p.evaluate(() => {
    const s = document.getElementById('imya-stroka');
    const t = document.querySelector('.kniga-stroka');
    const put = document.querySelector('.put-stroka');
    const dom = !!document.getElementById('imya');   // это главный экран
    return { est: !!s, tekst: s ? s.textContent : '',
             skryta: s ? s.hidden : null, dom: dom,
             nizhe_puti: (s && put)
               ? s.getBoundingClientRect().top >= put.getBoundingClientRect().bottom - 2
               : null,
             nad_knigoy: (s && t)
               ? s.getBoundingClientRect().bottom <= t.getBoundingClientRect().top + 2
               : null,
             razmer: s ? getComputedStyle(s).fontSize : '' };
  });
  if (stroka.dom) {
    // Главный экран: имя и цель стоят полями, строка здесь была бы повтором.
    proverka('на главном экране строка скрыта и пуста',
             stroka.skryta === true && !stroka.tekst.trim(), stroka);
  } else {
    proverka('строка есть и заполнена', stroka.est && !!stroka.tekst.trim(),
             stroka);
    proverka('строка идёт под путём', stroka.nizhe_puti === true, stroka);
    proverka('строка стоит выше учебника',
             stroka.nad_knigoy === null || stroka.nad_knigoy === true, stroka);
  }

  // --- задвоенные разделители: их не должно быть нигде
  proverka('служебных разделителей .panel-razd нет',
           await p.evaluate(() => document.querySelectorAll('.panel-razd')
                                  .length === 0));

  // --- боковое меню
  console.log('=== боковое меню');
  await p.evaluate(() => window.shkMenu());
  await p.waitForTimeout(700);
  const linii_menu = await linii(p, '#panel');
  proverka('в меню одна разделительная линия',
           linii_menu && linii_menu.length === 1, linii_menu);
  await p.mouse.move(4, 4);
  await p.waitForTimeout(200);
  const menu_bez = await krestik(p, '#panel');
  proverka('крестик меню в покое без подсветки',
           menu_bez && menu_bez.ramka === '3px rgba(0, 0, 0, 0)' &&
           menu_bez.fon === 'rgba(0, 0, 0, 0)', menu_bez);
  await p.hover('#panel .panel-zakryt');
  await p.waitForTimeout(250);
  const menu_naveden = await krestik(p, '#panel');
  proverka('крестик меню на наведении жёлтый',
           menu_naveden && menu_naveden.ramka === '3px rgb(255, 210, 63)' &&
           rgb(menu_naveden.fon)[0] > 20, menu_naveden);
  await p.mouse.move(4, 4);
  await p.waitForTimeout(200);

  // --- шапка панели: название класса одной строкой с крестиком
  // Просили: крупные заголовки меню — тем же шрифтом, что мелкие подписи
  // («Путь», «История России»), они не должны выглядеть активными, и
  // стоять в одну строку с крестиком. Списка классов здесь больше нет:
  // класс выбирают плитками на его странице (см. proverka_knopok.js),
  // поэтому у названия ни стрелки, ни самого списка.
  console.log('=== шапка меню');
  const shapka = await p.evaluate(() => {
    const verh = document.querySelector('#panel .panel-verh');
    const s = verh && verh.querySelector('.klass-imya');
    if (!s) return null;
    const tekst = s;
    const krest = verh.querySelector('.panel-zakryt');
    const st = getComputedStyle(s);
    const sverhu = verh.getBoundingClientRect();
    const rtekst = tekst.getBoundingClientRect();
    const rkrest = krest.getBoundingClientRect();
    const rp = document.querySelector('#panel').getBoundingClientRect();
    const tsentr = r => Math.round(r.top + r.height / 2 - sverhu.top);
    return {
      // Крестик — у правого края панели, название — у левого: меряем
      // зазоры до кромок самой панели, а не до соседа.
      do_pravoy: Math.round(rp.right - rkrest.right),
      ot_levoy: Math.round(rtekst.left - rp.left),
      razmer: parseInt(st.fontSize, 10),
      tolshchina: st.fontWeight,
      kraska: st.color,
      fon: st.backgroundColor,
      zazor_do_krestika: Math.round(rkrest.left - rtekst.right),
      tsentr_zag: tsentr(rtekst),
      tsentr_krest: tsentr(rkrest),
      strok: Math.round(rtekst.height / (parseFloat(st.lineHeight) || 1)),
      spiskov: document.querySelectorAll('#panel .klass-spisok, ' +
        '#panel .vybor-klassa').length,
      strelok: verh.querySelectorAll('.strela').length,
    };
  });
  if (shapka) {
    proverka('заголовок класса — 23px, обычного начертания, без подложки',
             shapka.razmer === 23 &&
             /^(400|normal)$/.test(String(shapka.tolshchina)) &&
             (shapka.fon === 'rgba(0, 0, 0, 0)' || shapka.fon === 'transparent'),
             shapka);
    proverka('заголовок класса приглушённого цвета, как мелкие подписи',
             rgb(shapka.kraska)[0] < 190 && ne_siniy(shapka.kraska),
             shapka.kraska);
    proverka('заголовок и крестик стоят по одной середине',
             Math.abs(shapka.tsentr_zag - shapka.tsentr_krest) <= 10,
             [shapka.tsentr_zag, shapka.tsentr_krest]);
    proverka('списка классов в меню нет — ни строки, ни стрелки',
             shapka.spiskov === 0 && shapka.strelok === 0, shapka);
    proverka('название класса стоит слева, крестик — у правого края',
             shapka.do_pravoy <= 22 && shapka.ot_levoy <= 46, shapka);
  } else {
    console.log('     (эта страница без меню)');
  }
  await p.screenshot({ path: path.join(kuda, 'меню-боковое.png') });

  // --- панель плейлиста (её нет на страницах без плеера)
  const est_panel = await p.evaluate(() =>
    !!document.querySelector('#pleylist-panel'));
  if (est_panel) {
    console.log('=== панель плейлиста');
    await p.evaluate(() => window.shkPleylistTog());
    await p.waitForTimeout(700);
    const pl_linii = await linii(p, '#pleylist-panel');
    proverka('в панели плейлиста одна разделительная линия',
             pl_linii && pl_linii.length === 1, pl_linii);
    const pl_shapka = await p.evaluate(() => {
      const verh = document.querySelector('#pleylist-panel .panel-verh');
      const z = verh.querySelector('.panel-zag');
      const krest = verh.querySelector('.panel-zakryt');
      const st = getComputedStyle(z);
      const sverhu = verh.getBoundingClientRect();
      const rz = z.getBoundingClientRect(), rk = krest.getBoundingClientRect();
      const tsentr = r => Math.round(r.top + r.height / 2 - sverhu.top);
      return { zag: z.textContent.trim(), razmer: parseInt(st.fontSize, 10),
               tolshchina: st.fontWeight, kraska: st.color,
               odna_stroka: st.whiteSpace === 'nowrap',
               tsentr_zag: tsentr(rz), tsentr_krest: tsentr(rk) };
    });
    proverka('заголовок панели — 23px, обычного начертания, серый, в одну строку',
             pl_shapka.razmer === 23 &&
             /^(400|normal)$/.test(String(pl_shapka.tolshchina)) &&
             pl_shapka.odna_stroka === true &&
             rgb(pl_shapka.kraska)[0] < 190, pl_shapka);
    proverka('заголовок панели и крестик — по одной середине',
             Math.abs(pl_shapka.tsentr_zag - pl_shapka.tsentr_krest) <= 10,
             [pl_shapka.tsentr_zag, pl_shapka.tsentr_krest]);
    await p.mouse.move(4, 4);
    await p.waitForTimeout(200);
    const pl_bez = await krestik(p, '#pleylist-panel');
    await p.hover('#pleylist-panel .panel-zakryt');
    await p.waitForTimeout(250);
    const pl_naveden = await krestik(p, '#pleylist-panel');
    await p.mouse.move(4, 4);
    await p.waitForTimeout(200);
    proverka('крестик плейлиста ведёт себя как в меню',
             JSON.stringify(pl_bez) === JSON.stringify(menu_bez) &&
             JSON.stringify(pl_naveden) === JSON.stringify(menu_naveden),
             { pl_bez, pl_naveden, menu_bez, menu_naveden });
    await p.screenshot({ path: path.join(kuda, 'меню-плейлист.png') });
  } else {
    console.log('=== панели плейлиста на этой странице нет — только меню');
  }

  // --- строки списков: ни подложек, ни рамок, ни жёлтых обводок
  console.log('=== строки списков');
  const stroki = [
    ['заголовок главы в панели', '#pleylist-panel .trek-gruppa'],
    ['название класса в меню', '#panel .klass-imya'],
  ];
  for (const [imya, sel] of stroki) {
    const s = await stil_stroki(p, sel);
    if (!s) { console.log('     (' + imya + ' на этой странице нет)'); continue; }
    proverka(imya + ' — просто текст, без подложки и рамок',
             stroka_chistaya(s), s);
  }
  // Строка плейлиста под кадром — того же вида, что пункт меню: подложки
  // в покое нет, а место под жёлтую чёрточку оставлено (прозрачная
  // полоса 6 px). Поэтому проверка тут своя: у заголовков рамок нет
  // вовсе, а у строки списка полоса есть всегда — иначе отметка
  // сдвигала бы текст.
  const stroka_plitka = await stil_stroki(p, '.pl-vse a.pl-plitka:not(.tekushchiy)');
  if (stroka_plitka) {
    proverka('строка плейлиста под кадром — текст, как пункт меню',
             (stroka_plitka.fon === 'rgba(0, 0, 0, 0)' ||
              stroka_plitka.fon === 'transparent') &&
             /^3px 3px 3px 3px$/.test(stroka_plitka.ramki) &&
             stroka_plitka.polosa === 'rgba(0, 0, 0, 0)' &&
             /^(none|0px)/.test(stroka_plitka.obvodka) &&
             ne_siniy(stroka_plitka.kraska), stroka_plitka);
  } else {
    console.log('     (плейлист на этой странице один — строка отмечена текущей)');
  }
  // Строка списка — текст: в покое ни подложки, ни рамок, ни обводки.
  // Но место под жёлтую чёрточку оставлено у КАЖДОЙ строки (прозрачная
  // полоса 6 px): поэтому отметка играющего пункта ничего не сдвигает.
  // Меряем в покое и без фокуса — при открытии меню фокус встаёт на
  // первую строку, и она подсвечена наведением.
  await p.evaluate(() => {
    if (document.activeElement && document.activeElement.blur) {
      document.activeElement.blur();
    }
    // фокус уводим на тело документа, чтобы строка не считалась наведённой
    document.body.setAttribute('tabindex', '-1');
    document.body.focus();
  });
  await p.mouse.move(4, 4);
  await p.waitForTimeout(250);
  const obychnye = await p.evaluate(() => {
    const a = document.querySelector('#panel a.panel-plitka:not(.tekushchiy)');
    const t = document.querySelector('.pl-vse a.pl-plitka:not(.tekushchiy)');
    const mertva = el => {
      if (!el) return null;
      const s = getComputedStyle(el);
      const n = el.querySelector('.trek-nomer');
      return { fon: s.backgroundColor,
               ramki: [s.borderTopWidth, s.borderRightWidth, s.borderBottomWidth,
                       s.borderLeftWidth].join(' '),
               polosa: s.borderLeftColor, obvodka: s.outlineStyle + ' ' + s.outlineWidth,
               kraska: s.color,
               nomer: n ? getComputedStyle(n).color : '—' };
    };
    return { menu: mertva(a), trek: mertva(t) };
  });
  if (obychnye.menu) {
    proverka('предмет в меню в покое — текст, рамка прозрачная, подложки нет',
             (obychnye.menu.fon === 'rgba(0, 0, 0, 0)' ||
              obychnye.menu.fon === 'transparent') &&
             /^3px 3px 3px 3px$/.test(obychnye.menu.ramki) &&
             obychnye.menu.polosa === 'rgba(0, 0, 0, 0)' &&
             !/^solid/.test(obychnye.menu.obvodka) &&
             ne_siniy(obychnye.menu.kraska), obychnye.menu);
  }
  const tek = await p.evaluate(() => {
    const a = document.querySelector(
      '#panel .panel-telo a.panel-plitka.tekushchiy');
    if (!a) return null;
    const s = getComputedStyle(a);
    return { tekst: a.textContent.trim(),
             sloi: s.backgroundImage,
             razmery: s.backgroundSize,
             ramka: s.borderTopWidth + ' ' + s.borderTopColor,
             radius: s.borderTopLeftRadius, kraska: s.color };
  });
  if (tek) {
    // Отметка текущего пункта — как у плашки: жёлтая полоса во всю
    // высоту у левого края, под нею серая подложка. Короткой чёрточки
    // посреди строки больше нет (просили заменить на полосу).
    proverka('текущий пункт меню: подложка, рамка и жёлтая полоса слева',
             /linear-gradient\(rgb\(255, 210, 63\), rgb\(255, 210, 63\)\)/.test(tek.sloi) &&
             /linear-gradient\(rgb\(35, 44, 56\), rgb\(35, 44, 56\)\)/.test(tek.sloi) &&
             /^8px 100%, 100% 100%$/.test(tek.razmery) &&
             tek.ramka === '3px rgb(255, 210, 63)' &&
             tek.radius === '10px',
             tek);
  }
  // Панель плейлиста — тот же вид, что и все списки: у обычного пункта
  // ни подложки, ни полосы, ни жёлтого номера. Выделяется только
  // играющий — плашкой и жёлтой чёрточкой (класс .aktiven).
  // Меряем спокойное состояние: снимаем фокус и уводим курсор, иначе
  // строка под ним считается наведённой.
  await p.evaluate(() => {
    if (document.activeElement && document.activeElement.blur) {
      document.activeElement.blur();
    }
  });
  await p.mouse.move(4, 4);
  await p.waitForTimeout(250);
  const v_paneli = await p.evaluate(() => {
    const vse = [...document.querySelectorAll('#pleylist-panel a.trek')];
    // Берём строку с номером и не играющую: у играющей отметка есть,
    // а у первой строки курса номера может не быть вовсе («Введение»).
    const a = vse.find(x => x.querySelector('.trek-nomer') &&
                            !x.className.includes('aktiven')) ||
              vse.find(x => x.querySelector('.trek-nomer'));
    if (!a) return null;
    const s = getComputedStyle(a);
    const sn = getComputedStyle(a.querySelector('.trek-nomer'));
    return { fon: s.backgroundColor,
             ramki: [s.borderTopWidth, s.borderRightWidth,
                     s.borderBottomWidth, s.borderLeftWidth].join(' '),
             polosa: s.borderLeftColor,
             nomer: sn.color, kraska: s.color };
  });
  if (v_paneli) {
    proverka('в панели у обычного пункта подложки нет',
             v_paneli.fon === 'rgba(0, 0, 0, 0)' ||
             v_paneli.fon === 'transparent', v_paneli);
    proverka('в панели у обычного пункта рамка прозрачная, лишнего нет',
             /^3px 3px 3px 3px$/.test(v_paneli.ramki) &&
             v_paneli.polosa === 'rgba(0, 0, 0, 0)', v_paneli);
    proverka('в панели номер обычного пункта серый, как у прочих строк',
             v_paneli.nomer === 'rgb(139, 149, 165)', v_paneli);
  }
  // наведение делает строку чуть ярче и не синим
  const pered = await p.evaluate(() => {
    // Берём строку НЕ активную и не под фокусом: у обеих цвет и так
    // самый яркий — при открытии панели фокус встаёт на первую строку,
    // и она уже выглядит наведённой.
    if (document.activeElement && document.activeElement.blur) {
      document.activeElement.blur();
    }
    const vse = [...document.querySelectorAll('#pleylist-panel a.trek')]
      .filter(a => !a.className.includes('aktiven'));
    const a = vse[Math.min(2, vse.length - 1)];
    if (!a) return null;
    a.scrollIntoView({ block: 'center' });
    const r = a.getBoundingClientRect();
    a.setAttribute('data-proverka-kursor', '1');
    return { x: Math.round(r.left + r.width / 2), y: Math.round(r.top + r.height / 2),
             kraska: getComputedStyle(a).color,
             fon: getComputedStyle(a).backgroundColor };
  });
  if (pered) {
    await p.mouse.move(pered.x, pered.y);
    await p.waitForTimeout(250);
    const posle = await p.evaluate(() => {
      const a = document.querySelector('[data-proverka-kursor]');
      const el = document.elementFromPoint(
        Math.round(a.getBoundingClientRect().left + a.getBoundingClientRect().width / 2),
        Math.round(a.getBoundingClientRect().top + a.getBoundingClientRect().height / 2));
      const sverkhu = !!el && (el === a || a.contains(el) || el.closest('a') === a);
      return { sverkhu, kraska: getComputedStyle(a).color,
               fon: getComputedStyle(a).backgroundColor };
    });
    proverka('курсор на строке плейлиста', posle.sverkhu, posle);
    // Строка в панели — простой текст: при наведении появляется серая
    // подложка, текст становится ярче. Синим не подсвечиваем.
    proverka('наведение делает строку ярче и не синим',
             (posle.kraska !== pered.kraska || posle.fon !== pered.fon) &&
             ne_siniy(posle.kraska) && ne_siniy(posle.fon),
             [posle.kraska, pered.kraska, posle.fon, pered.fon]);
    await p.mouse.move(4, 4);
    await p.waitForTimeout(200);
    await p.evaluate(() => document.querySelectorAll('[data-proverka-kursor]')
      .forEach(e => e.removeAttribute('data-proverka-kursor')));
  }

  // --- список плейлистов под кадром (только там, где есть плеер)
  const est_pleer = await p.evaluate(() => !!document.querySelector('#pleyer'));
  // Страница тренажёров устроена как страница видео (то же поле, та же
  // панель), но списка плейлистов под кадром у неё нет: там свои пункты.
  // Поэтому проверки про плейлисты идут только там, где он есть.
  const est_plitok = await p.evaluate(() => !!document.querySelector('.pl-vse'));
  if (est_pleer && est_plitok) {
    console.log('=== список плейлистов под кадром');
    await p.evaluate(() => window.shkPleylist(false));
    await p.waitForTimeout(400);
    // Под кадром — только названия плейлистов, без самих уроков:
    // уроки живут в панели. Строки идут тем же классом, что пункты
    // бокового меню, поэтому и вид у них один и тот же.
    const sostav = await p.evaluate(() => ({
      strok: document.querySelectorAll('.pl-vse a.pl-plitka').length,
      plitok: document.querySelectorAll('.pl-vse a.panel-plitka').length,
      urokev: document.querySelectorAll('.pl-vse a.trek').length,
      razdelov: document.querySelectorAll('.pl-vse .trek-gruppa').length,
    }));
    proverka('под кадром — список плейлистов, а не уроки',
             sostav.strok > 0 && sostav.strok === sostav.plitok &&
             sostav.urokev === 0 && sostav.razdelov === 0, sostav);
    const pod = await p.evaluate(() => {
      const a = document.querySelector('.pl-vse a.pl-plitka:not(.tekushchiy)');
      if (!a) return null;
      const s = getComputedStyle(a);
      return { fon: s.backgroundColor, ramki: [s.borderTopWidth, s.borderRightWidth,
               s.borderBottomWidth, s.borderLeftWidth].join(' '),
               polosa: s.borderLeftColor, kraska: s.color, razmer: s.fontSize };
    });
    if (pod) {
      proverka('строка плейлиста в покое — текст, рамка прозрачная, подложки нет',
               (pod.fon === 'rgba(0, 0, 0, 0)' || pod.fon === 'transparent') &&
               /^3px 3px 3px 3px$/.test(pod.ramki) &&
               pod.polosa === 'rgba(0, 0, 0, 0)' && ne_siniy(pod.kraska), pod);
    } else {
      // Плейлист на странице один: он же и играет, и отмечен. Покоя,
      // который тут можно померить, нет — не выдумывать ошибку.
      console.log('     (плейлист один — в покое мерить нечего)');
    }
    const aktiv = await p.evaluate(() => {
      const a = document.querySelector('.pl-vse a.pl-plitka.tekushchiy');
      if (!a) return null;
      const s = getComputedStyle(a);
      return { sloi: s.backgroundImage, razmery: s.backgroundSize,
               ramka: s.borderTopWidth + ' ' + s.borderTopColor,
               radius: s.borderTopLeftRadius, kraska: s.color };
    });
    if (aktiv) {
      proverka('открытый плейлист: подложка, прозрачная рамка и жёлтая полоса слева',
               /linear-gradient\(rgb\(255, 210, 63\), rgb\(255, 210, 63\)\)/.test(aktiv.sloi) &&
               /^8px 100%, 100% 100%$/.test(aktiv.razmery) &&
               aktiv.ramka === '3px rgba(0, 0, 0, 0)' &&
               aktiv.radius === '10px', aktiv);
    }
    // Реакция на наведение — как у пункта меню: та же серая подложка.
    // Наводим настоящей мышью: подделанное правило проиграло бы
    // настоящему по точности селектора, и проверка соврала бы.
    if (pod) {
      const do_navedeniya = await p.evaluate(() => getComputedStyle(
        document.querySelector('.pl-vse a.pl-plitka:not(.tekushchiy)'))
        .backgroundColor);
      await p.hover('.pl-vse a.pl-plitka:not(.tekushchiy)');
      await p.waitForTimeout(250);
      const posle_navedeniya = await p.evaluate(() => getComputedStyle(
        document.querySelector('.pl-vse a.pl-plitka:not(.tekushchiy)'))
        .backgroundColor);
      await p.mouse.move(4, 4);
      await p.waitForTimeout(200);
      proverka('наведение на строку плейлиста даёт ту же серую подложку',
               posle_navedeniya === 'rgb(27, 33, 43)' &&
               do_navedeniya === 'rgba(0, 0, 0, 0)',
               [do_navedeniya, posle_navedeniya]);
    }
    // Отступ от номера параграфа до текста в панели: один зазор на все
    // строки. Был 12 px — просили сократить примерно на треть, стало
    // 10 px; колонка номера сжалась с 58 до 50 px (по самому длинному
    // «§ 45»), чтобы между «§ 1» и текстом не оставалось пустоты.
    const zazor = await p.evaluate(() => {
      // Только видимые строки: у скрытых плейлистов прямоугольники
      // нулевые, и замер показал бы зазор 0 вместо настоящего.
      const ryady = [...document.querySelectorAll('#pleylist-panel .trek-nomer')]
        .filter(n => n.getBoundingClientRect().width > 0);
      const z = [];
      ryady.forEach(n => {
        const a = n.closest('a.trek'); const t = a && a.querySelector('.trek-tema');
        if (!t) return;
        z.push(Math.round(t.getBoundingClientRect().left -
                          n.getBoundingClientRect().right));
      });
      if (!z.length) return null;
      // О чём колонка: «§ 1» — номер параграфа, «1 ч 22 мин» — время
      // проигрывания (кино и лекции). От неё и ширина колонки.
      const nadpis = ryady[0].textContent.trim();
      return { strok: z.length, min: Math.min(...z), maks: Math.max(...z),
               kolonka: Math.round(ryady[0].getBoundingClientRect().width),
               za: getComputedStyle(ryady[0]).textAlign,
               vid: /^§|^\d+$/.test(nadpis) ? 'параграфы' : 'время' };
    });
    if (zazor) {
      proverka('от номера до текста ровно один зазор (10 px), как во всех строках',
               zazor.min === zazor.maks && zazor.min === 10,
               zazor);
      // У кино и лекций в колонке стоит время («1 ч 22 мин» — 132 px),
      // и колонка шире: это не пустота, а сама подпись.
      proverka('номер прижат к левому краю колонки — ближе к кромке панели',
               zazor.za === 'left' &&
               (zazor.kolonka <= 50 || /время/.test(zazor.vid || '')),
               [zazor.za, zazor.kolonka, zazor.vid || 'параграфы']);
      // Номер не липнет к левой кромке строки: отступ 28 px — иначе
      // «§ 1» упирался бы в край, а у играющего пункта ещё и в полосу.
      const otstup = await p.evaluate(() => {
        const a = document.querySelector('#pleylist-panel a.trek');
        const n = a && a.querySelector('.trek-nomer');
        if (!n) return null;
        const ra = a.getBoundingClientRect(), rn = n.getBoundingClientRect();
        return { ot: Math.round(rn.left - ra.left),
                 v_pravilah: getComputedStyle(a).paddingLeft };
      });
      if (otstup) {
        proverka('номер не липнет к левой кромке строки (28 px)',
                 otstup.ot >= 25 && otstup.v_pravilah === '28px', otstup);
      }
    }
    await p.screenshot({ path: path.join(kuda, 'меню-под-кадром.png'),
                         fullPage: true });
  }

  // --- крестик на уведомлении.
  // Слова «Закрыть» на карточке нет: в правом верхнем углу иконка.
  // Карточка возврата — только у видеоуроков: у тренажёров своё поле,
  // и крестика в нём нет.
  if (est_pleer && est_plitok) {
    const krestik = await p.evaluate(() => {
      const a = document.getElementById('vybor-zakryt');
      const k = document.querySelector('#vybor-karta');
      const v = document.getElementById('pleyer-vybor');
      if (!a) return { est: false };
      const r = a.getBoundingClientRect();
      const kr = k.getBoundingClientRect();
      return { est: true,
               // На свежей странице карточки возврата нет: она показывается
               // только когда помнится недосмотренный урок. Тогда измерить
               // её углы нечем — об этом и говорим, а не считаем ошибкой:
               // положение крестика на всех ширинах ловит proverka_knopok.js.
               pokazana: !!v && getComputedStyle(v).display !== 'none',
               slovo: /Закрыть/.test(k.textContent),
               podpiz: a.getAttribute('aria-label') || '',
               sverkhu_sprava: r.top < kr.top + kr.height / 2 &&
                               r.right > kr.left + kr.width / 2,
               ne_kryta: !!document.elementFromPoint(
                 Math.round(r.left + r.width / 2),
                 Math.round(r.top + r.height / 2)) };
    });
    proverka('на уведомлении крестик закрытия', krestik.est, krestik);
    if (krestik.est) {
      proverka('слова «Закрыть» на уведомлении нет', !krestik.slovo, krestik);
      proverka('крестик подписан для скринридеров',
               krestik.podpiz === 'Закрыть', krestik);
      if (krestik.pokazana) {
        proverka('крестик в правом верхнем углу карточки',
                 krestik.sverkhu_sprava && krestik.ne_kryta, krestik);
      } else {
        console.log('  ок   карточки возврата на свежей странице нет — ' +
                    'её углы и ширины проверяет proverka_knopok.js');
      }
    }
  } else {
    console.log('=== плеера на этой странице нет — уведомления тоже');
  }

  // --- панель не закрывается сама: открыл — и она остаётся открытой,
  // даже когда уходишь на другую страницу; закрывает только человек
  // (крестик или Escape). Проверяем по-настоящему: кликаем пункт меню,
  // браузер уходит на другую страницу, и там смотрим на панель.
  console.log('=== панель не закрывается сама');
  await p.evaluate(() => {
    try { localStorage.removeItem('shkola.panel-otkryt'); } catch (e) {}
  });
  await p.evaluate(() => window.shkPanel(true));
  const klyuch_otkryli = await p.evaluate(() => {
    try { return localStorage.getItem('shkola.panel-otkryt'); } catch (e) { return 'нет доступа'; }
  });
  proverka('открыли меню — оно запомнено в браузере',
           klyuch_otkryli === 'menu', klyuch_otkryli);

  const ssylka = await p.evaluate(() => {
    const a = [...document.querySelectorAll('#panel .panel-telo a.panel-plitka')]
      .find(x => x.href && /\.html$/.test(x.pathname) &&
                 !x.className.includes('tekushchiy'));
    if (!a) return null;
    a.setAttribute('data-proverka-perehod', '1');
    return a.getAttribute('href');
  });
  if (ssylka) {
    await Promise.all([
      p.waitForNavigation({ waitUntil: 'load' }),
      p.click('[data-proverka-perehod]'),
    ]);
    await p.waitForTimeout(400);
    const posle = await p.evaluate(() => ({
      stranica: location.pathname.split('/').slice(-2).join('/'),
      otkryto: document.body.classList.contains('menu-otkryto'),
      klyuch: (() => { try { return localStorage.getItem('shkola.panel-otkryt'); }
                       catch (e) { return null; } })(),
    }));
    proverka('после перехода по пункту меню панель осталась открытой',
             posle.otkryto && posle.klyuch === 'menu', posle);

    // Теперь крестик: только он закрывает — и это тоже запоминается.
    await p.click('#panel .panel-zakryt');
    await p.waitForTimeout(300);
    const zakryto = await p.evaluate(() => ({
      otkryto: document.body.classList.contains('menu-otkryto'),
      klyuch: (() => { try { return localStorage.getItem('shkola.panel-otkryt'); }
                       catch (e) { return null; } })(),
    }));
    proverka('крестик закрывает панель — и это тоже запоминается',
             !zakryto.otkryto && zakryto.klyuch === '', zakryto);
    await p.reload({ waitUntil: 'load' });
    await p.waitForTimeout(300);
    const posle_perezagruzki = await p.evaluate(() =>
      document.body.classList.contains('menu-otkryto'));
    proverka('новая страница помнит, что панель закрыта',
             posle_perezagruzki === false, posle_perezagruzki);
  } else {
    console.log('     (пунктов-переходов в меню нет — переход пропускаем)');
  }

  console.log('\nИтог: ошибок ' + oshibki);
  await b.close();
  process.exit(oshibki ? 1 : 0);
})();
