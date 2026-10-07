// Боковое меню и панель плейлиста: проверка с вердиктами.
//
// Проверяем всё, на что жаловались: задвоенные разделительные линии,
// плашки с фоном и жёлтые обводки у строк, разное поведение крестика
// в двух панелях, а также маленькую строку с именем и целью и кнопку
// «Закрыть» на уведомлении. Не «печатаем замеры», а сравниваем с тем,
// как должно быть, и в конце считаем ошибки.
//
//   node Временные/proverka_menyu.js "Проект/База данных/5 класс/История/видеоуроки.html"
const fs = require('fs');
const path = require('path');
const { chromium } = require('./плейрайт.js');

const put = process.argv[2] ||
  'Проект/База данных/5 класс/История/видеоуроки.html';
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
async function linii(p, panel) {
  return p.evaluate((sel) => {
    const kor = document.querySelector(sel);
    if (!kor) return null;
    const shirina = kor.getBoundingClientRect().width;
    const naideno = [];
    kor.querySelectorAll('*').forEach(el => {
      const s = getComputedStyle(el);
      const w = el.getBoundingClientRect().width;
      if (w < shirina * 0.7) return;
      if (parseFloat(s.borderBottomWidth) > 0 && s.borderBottomStyle !== 'none')
        naideno.push(el.className || el.tagName);
      if (parseFloat(s.borderTopWidth) > 0 && s.borderTopStyle !== 'none')
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
    ['класс в меню', '#panel summary.klass-knopka'],
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
             /^0px 0px 0px 6px$/.test(stroka_plitka.ramki) &&
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
    proverka('предмет в меню в покое — текст, без подложки и рамок',
             (obychnye.menu.fon === 'rgba(0, 0, 0, 0)' ||
              obychnye.menu.fon === 'transparent') &&
             /^0px 0px 0px 6px$/.test(obychnye.menu.ramki) &&
             obychnye.menu.polosa === 'rgba(0, 0, 0, 0)' &&
             !/^solid/.test(obychnye.menu.obvodka) &&
             ne_siniy(obychnye.menu.kraska), obychnye.menu);
  }
  const tek = await p.evaluate(() => {
    const a = document.querySelector('#panel .panel-telo a.panel-plitka.tekushchiy')
           || document.querySelector('#panel .klass-spisok a.panel-plitka.tekushchiy');
    if (!a) return null;
    const s = getComputedStyle(a);
    return { tekst: a.textContent.trim(), fon: s.backgroundColor,
             polosa: s.borderLeftWidth + ' ' + s.borderLeftColor,
             radius: s.borderTopLeftRadius, kraska: s.color };
  });
  if (tek) {
    proverka('текущий пункт меню: серая подложка и жёлтая чёрточка со скруглением',
             tek.fon === 'rgb(35, 44, 56)' &&
             tek.polosa === '6px rgb(255, 210, 63)' && tek.radius === '12px',
             tek);
  }
  // У панели плейлиста вид свой, прежний: плашка, жёлтая полоса слева,
  // жёлтый номер параграфа. Правка «просто текст» её не касалась —
  // простой текст это список под кадром и боковое меню.
  // Меряем спокойное состояние: снимаем фокус и уводим курсор, иначе
  // строка под ним считается наведённой и плашка у неё светлее.
  await p.evaluate(() => {
    if (document.activeElement && document.activeElement.blur) {
      document.activeElement.blur();
    }
  });
  await p.mouse.move(4, 4);
  await p.waitForTimeout(250);
  const v_paneli = await p.evaluate(() => {
    const vse = [...document.querySelectorAll('#pleylist-panel a.trek')];
    // Берём строку с номером и не играющую: у играющей плашка светлее,
    // а у первой строки курса номера может не быть вовсе («Введение»).
    const a = vse.find(x => x.querySelector('.trek-nomer') &&
                            !x.className.includes('aktiven')) ||
              vse.find(x => x.querySelector('.trek-nomer'));
    if (!a) return null;
    const s = getComputedStyle(a);
    const sn = getComputedStyle(a.querySelector('.trek-nomer'));
    return { fon: s.backgroundColor, polosa: s.borderLeftWidth + ' ' +
             s.borderLeftColor, ramka: s.borderTopWidth,
             nomer: sn.color, igraet: a.className.includes('aktiven'),
             kraska: s.color };
  });
  if (v_paneli) {
    proverka('в панели у пункта плашка, как и было',
             v_paneli.fon === 'rgb(27, 33, 43)' ||
             (v_paneli.igraet && v_paneli.fon === 'rgb(35, 44, 56)'), v_paneli);
    proverka('в панели жёлтая полоса слева, как и было',
             v_paneli.polosa === '6px rgb(255, 210, 63)', v_paneli);
    proverka('в панели номер параграфа жёлтый, как и было',
             v_paneli.nomer === 'rgb(255, 210, 63)', v_paneli);
    proverka('в панели плашка без рамки вокруг',
             v_paneli.ramka === '0px', v_paneli);
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
    // Строка в панели стоит на плашке: при наведении чуть ярче становится
    // и текст, и плашка. Синим не подсвечиваем.
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
  if (est_pleer) {
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
      proverka('строка плейлиста в покое — текст, подложки и рамок нет',
               (pod.fon === 'rgba(0, 0, 0, 0)' || pod.fon === 'transparent') &&
               /^0px 0px 0px 6px$/.test(pod.ramki) &&
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
      return { fon: s.backgroundColor,
               polosa: s.borderLeftWidth + ' ' + s.borderLeftColor,
               radius: s.borderTopLeftRadius, kraska: s.color };
    });
    if (aktiv) {
      proverka('открытый плейлист: подложка и жёлтая чёрточка со скруглением',
               aktiv.fon === 'rgb(35, 44, 56)' &&
               aktiv.polosa === '6px rgb(255, 210, 63)' &&
               aktiv.radius === '12px', aktiv);
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
    // Отступ от номера параграфа до текста в панели: зазор задан, и он
    // одинаков во всех строках — это и просили убрать («слишком большой
    // отступ от номера до текста»).
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
      return { strok: z.length, min: Math.min(...z), maks: Math.max(...z),
               kolonka: Math.round(ryady[0].getBoundingClientRect().width),
               za: getComputedStyle(ryady[0]).textAlign };
    });
    if (zazor) {
      proverka('от номера до текста ровно один зазор, одинаковый во всех строках',
               zazor.min === zazor.maks && zazor.min <= 20,
               zazor);
      proverka('номер прижат вправо в своей колонке',
               zazor.za === 'right', zazor.za);
    }
    await p.screenshot({ path: path.join(kuda, 'меню-под-кадром.png'),
                         fullPage: true });
  }

  // --- крестик на уведомлении (уведомление бывает только с плеером).
  // Слова «Закрыть» на карточке нет: в правом верхнем углу иконка.
  if (est_pleer) {
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

  console.log('\nИтог: ошибок ' + oshibki);
  await b.close();
  process.exit(oshibki ? 1 : 0);
})();
