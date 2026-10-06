// Стенд плеера: без браузера проверяем весь путь зрителя.
//
// Подставляем крошечный DOM и запускаем скрипты, снятые с настоящей
// страницы видеоуроков. Плейлисты берём из её же разметки, поэтому
// стенд проверяет то, что ребёнок увидит на телевизоре, а не выдумку.
//
// Запуск:
//   node Временные/proverka_pleera.js "Проект/База данных/5 класс/История/видеоуроки.html"

const fs = require('fs');

const put = process.argv[2] || 'Проект/База данных/5 класс/История/видеоуроки.html';
const html = fs.readFileSync(put, 'utf8');

const skripty = (html.match(/<script>[\s\S]*?<\/script>/g) || [])
  .map(s => s.replace(/<\/?script>/g, ''));
const skript_pleera = skripty.find(s => s.includes('shkola.urok.'));
const skript_stranicy = skripty.find(s => s.includes('shkola.home'));
if (!skript_pleera) { console.error('НЕ НАЙДЕН скрипт плеера в ' + put); process.exit(2); }

// ---------- настоящие плейлисты из разметки ----------
function razor(blok) {
  const treki = [];
  const re = /<a class="trek"[^>]*data-video="([^"]*)"[^>]*data-zag="([^"]*)"[^>]*data-nomer="([^"]*)"[^>]*data-tema="([^"]*)"[^>]*>/g;
  let m;
  while ((m = re.exec(blok))) {
    treki.push({ video: m[1], zag: m[2], nomer: m[3], tema: m[4] });
  }
  return treki;
}
const razmery = /<div class="pleylist([^"]*)" data-nabor="(\d+)"/g;
const nachala = [];
let mm;
while ((mm = razmery.exec(html))) {
  nachala.push({ nomer: Number(mm[2]), otkryt: mm[1].includes('aktiven'),
                 ot: mm.index });
}
// Кусок плейлиста — до начала следующего (или до конца панели):
// внутри списка есть свои div'ы (заголовки групп), по ним не режем.
const naydeno = nachala.map((x, i) => ({
  nomer: x.nomer, otkryt: x.otkryt,
  kusok: html.slice(x.ot, i + 1 < nachala.length ? nachala[i + 1].ot
                                                 : html.indexOf('</aside>', x.ot)),
}));
const kuski = naydeno.map(x => ({ nomer: x.nomer, otkryt: x.otkryt, treki: razor(x.kusok) }));
// Плейлисты под кадром: имя берём из шапки блока, а пункты — из его же
// разметки. Так стенд проверяет и то, что списков два (в панели и под
// кадром), и то, что содержимое у них одно и то же.
const nachala_blokov = [...html.matchAll(/<details class="pl-blok([^"]*)"\s+data-nabor="(\d+)"/g)]
  .map(m => ({ nomer: Number(m[2]), aktiven: m[1].includes('aktiven'), ot: m.index }));
const konec_podvideo = html.indexOf('<aside class="panel" id="pleylist-panel">');
const knopki = nachala_blokov.map((x, i) => {
  const kusok = html.slice(x.ot, i + 1 < nachala_blokov.length
                                  ? nachala_blokov[i + 1].ot : konec_podvideo);
  return { nomer: x.nomer, aktiven: x.aktiven,
           imya: (kusok.match(/<span class="pl-nazv">([^<]*)<\/span>/) || [])[1] || '',
           treki: razor(kusok) };
});

// ---------- крошечный DOM ----------
function uzel(tag, attrs) {
  const u = {
    tag, attrs: attrs || {}, kids: [], style: {}, className: attrs && attrs.class || '',
    textContent: '', src: '', onclick: null,
    prokruchivat: () => {},
    getAttribute(k) { return this.attrs[k] !== undefined ? this.attrs[k] : null; },
    setAttribute(k, v) { this.attrs[k] = v; },
    appendChild(c) { this.kids.push(c); },
    addEventListener() {},
    scrollIntoView() {},
    focus() {},
    set className(v) { this._cl = v; if (this.attrs) this.attrs.class = v; },
    get className() { return this._cl !== undefined ? this._cl : (this.attrs.class || ''); },
  };
  Object.defineProperty(u, 'className', {
    get() { return this._cl !== undefined ? this._cl : (this.attrs.class || ''); },
    set(v) { this._cl = v; if (this.attrs) this.attrs.class = v; },
  });
  return u;
}

function pleylist(kusok) {
  const u = uzel('div', { 'data-nabor': String(kusok.nomer),
                          class: 'pleylist' + (kusok.otkryt ? ' aktiven' : '') });
  u.attrs['data-imya'] = kusok.imya || '';
  u.treks = kusok.treki.map(t => uzel('a', {
    class: 'trek', 'data-video': t.video, 'data-zag': t.zag,
    'data-nomer': t.nomer, 'data-tema': t.tema,
  }));
  u.querySelector = sel => (sel === '.trek' ? (u.treks[0] || null) : null);
  u.querySelectorAll = sel => (sel === '.trek' ? u.treks : []);
  if (!kusok.otkryt) u.style.display = 'none';
  u.treks.forEach(t => { t.parentNode = u; });
  return u;
}

const spiski = kuski.map(pleylist);
spiski.forEach((sp, i) => { sp.attrs['data-imya'] = knopki[i].imya; });
// Блок под кадром — это <details> с раскрывающимся <summary>. Ссылки
// внутри него — те же уроки, что и в панели.
const knopki_uzly = knopki.map(k => {
  const u = uzel('details', { class: 'pl-blok' + (k.aktiven ? ' aktiven' : ''),
                              'data-nabor': String(k.nomer) });
  u.open = k.aktiven;
  u.textContent = k.imya;
  u.summary = uzel('summary', { class: 'pl-imya' });
  u.summary.parentNode = u;
  u.treki = k.treki;
  return u;
});

const elId = {};
['pleyer', 'pleyer-zag', 'pleyer-vybor', 'vybor-tekst', 'vybor-glavnaya',
 'vybor-vtoraya', 'pleylist-panel', 'pl-zag'].forEach(i => { elId[i] = uzel('div', {}); });
if (html.includes('id="pl-zag"')) {
  elId['pl-zag'].textContent = (html.match(/id="pl-zag">\s*([^<]*)/) || [])[1] || '';
}
// ручки ширины и окно — для проверки растягивания панели
const ruki = [...html.matchAll(/<div class="panel-tyanulka ([a-z]+)"/g)].map(m => m[1]);
const ruki_uzly = ruki.map(k => {
  const u = uzel('div', { class: 'panel-tyanulka ' + k });
  u.setPointerCapture = () => {};
  return u;
});
// панель умеет искать внутри себя — это делает общий скрипт страницы
elId['pleylist-panel'].querySelector = () => spiski[0].treks[0] || null;

const telo = uzel('body', {});
const klassy_tela = new Set();
telo.classList = {
  add: c => klassy_tela.add(c),
  remove: c => klassy_tela.delete(c),
  contains: c => klassy_tela.has(c),
  has: c => klassy_tela.has(c),
};
global.localStorage = {
  dannye: {},
  getItem(k) { return (k in this.dannye) ? this.dannye[k] : null; },
  setItem(k, v) { this.dannye[k] = String(v); },
  removeItem(k) { delete this.dannye[k]; },
};
const sobytiya = {};
global.window = {
  SHK_HOME: put,
  addEventListener(n, f) { (sobytiya[n] = sobytiya[n] || []).push(f); },
};
global.document = {
  readyState: 'complete',
  body: telo,
  addEventListener() {},
  createElement() {
    const f = uzel('iframe', {});
    f.contentWindow = { postMessage(soob) { (f.otpravleno = f.otpravleno || []).push(JSON.parse(soob)); } };
    elId.ramka = f;
    return f;
  },
  getElementById(id) { return elId[id] !== undefined ? elId[id] : null; },
  querySelectorAll(sel) {
    if (sel === '.pleylist') return spiski;
    if (sel === '.trek') return spiski.flatMap(s => s.treks);
    if (sel === '.pl-blok') return knopki_uzly;
    if (sel === '.panel-tyanulka') return ruki_uzly;
    return [];
  },
  querySelector(sel) {
    if (sel === '.pleylist.aktiven') {
      return spiski.find(s => s.className.includes('aktiven')) || null;
    }
    return null;
  },
};
global.location = { pathname: '/' + put };
// Раскрывающиеся шапки плейлистов под кадром: браузер сам вешает на них
// onclick из разметки, поэтому в стенде подставляем то же самое.
knopki_uzly.forEach(u => {
  u.summary.onclick = () => {
    const r = window.shkRaskryt(u.summary);
    if (r !== false) { u.open = !u.open; }   // так делает сам браузер
    return r;
  };
});
global.window = Object.assign(global.window || {}, { innerWidth: 1600 });
// у body своя переменная ширины панели
const stil_tela = { '--panel-shirina': '420px' };
telo.style = { setProperty: (k, v) => { stil_tela[k] = v; } };
global.getComputedStyle = () => ({
  getPropertyValue: k => stil_tela[k] || '',
});

eval(skript_pleera);

function soobshchenie(obj) {
  (sobytiya['message'] || []).forEach(f => f({ data: JSON.stringify(obj) }));
}
function perezagruzka() {
  elId.ramka = null;
  sobytiya['message'] = [];
  spiski.forEach((s, i) => { s.className = i === 0 ? 'pleylist aktiven' : 'pleylist'; });
  // Живая перезагрузка начинается с чистого окна: снимаем всё, что
  // поставил прошлый запуск, иначе он ведёт себя как вторая копия.
  // SHK_HOME не трогаем: его ставит скрипт страницы, а не плеера —
  // без него имя записи в памяти получилось бы другим.
  ['shkIgrat', 'shkPanel', 'shkPleylist', 'shkPleylistTog', 'shkMenu',
   'shkProdolzhit', 'shkTyan', 'shkRaskryt', 'shkBanner',
   'shkBannerIgrat', 'shkBannerGde'
  ].forEach(i => { try { delete window[i]; } catch (e) { window[i] = undefined; } });
  eval(skript_pleera);
}
let oshibki = 0;
const proverka = (imya, uslovie, fakticheskoe) => {
  console.log((uslovie ? '  ок   ' : '  ОШИБКА ') + imya +
              (uslovie ? '' : ' → ' + JSON.stringify(fakticheskoe)));
  if (!uslovie) oshibki++;
};
const knopka = id => elId[id].textContent;

// ---------- проверки ----------
console.log('проверяем: ' + put);
console.log('плейлистов в разметке: ' + spiski.length +
            ' (' + spiski.map(s => s.treks.length).join(', ') + ')' +
            ' | кнопок вариантов: ' + knopki_uzly.length);

if (!spiski.length) {
  // Страница предмета с баннером: списки лекций там свои (a.banner-trek),
  // их проверяет proverka_bannera.js. Молча «0 ошибок» не пишем, чтобы
  // пропавшие списки на видеостранице нельзя было принять за успех.
  console.log('на странице нет списков под кадром — верный стенд: ' +
              'proverka_bannera.js');
  process.exit(3);
}

console.log('=== 1. пустая память: страница ничего не запускает');
proverka('кадра нет', !elId.ramka);

console.log('=== 2. выбрали второй пункт первого плейлиста');
const pervyi_pleylist = spiski[0].treks;
window.shkIgrat(pervyi_pleylist[1]);
proverka('кадр создан', !!elId.ramka);
proverka('адрес без автозапуска',
         elId.ramka.src === pervyi_pleylist[1].attrs['data-video'] ,
         elId.ramka.src);
proverka('шапка — название урока',
         elId['pleyer-zag'].textContent === pervyi_pleylist[1].attrs['data-zag'],
         elId['pleyer-zag'].textContent);
proverka('подсвечен один пункт', pervyi_pleylist.filter(t => t.className.includes('aktiven')).length === 1,
         pervyi_pleylist.map(t => t.className));

console.log('=== 3. плеер готов, играет, присылает время');
soobshchenie({ type: 'player:ready' });
proverka('команд play отправлено',
         (elId.ramka.otpravleno || []).some(m => m.type === 'player:play'));
for (let t = 0; t <= 300; t += 10) soobshchenie({ type: 'player:currentTime', data: { time: t } });
const zapis = JSON.parse(Object.values(localStorage.dannye)[0]);
proverka('время запомнено (≈300)', zapis.vremya === 300, zapis.vremya);
proverka('урок и номер записаны',
         zapis.kod === pervyi_pleylist[1].attrs['data-video'] && !!zapis.nomer, zapis);

console.log('=== 4. пауза: время спрашиваем у плеера');
elId.ramka.otpravleno.length = 0;
soobshchenie({ type: 'player:changeState', data: { state: 'paused' } });
proverka('запрос времени', elId.ramka.otpravleno.some(m => m.type === 'player:currentTime'));

// Страница кино говорит иначе, чем страница уроков: у фильмов подпись
// пункта — время («1 ч 20 мин»), у уроков — «§ 12». Стенд повторяет это
// же правило, иначе он ругался бы на правильную страницу.
const podpis_mesta = (pervyi_pleylist[1].attrs['data-nomer'] || '').trim();
const kino = !!podpis_mesta && podpis_mesta[0] !== '§';
const sledSlovo = kino ? 'Следующий фильм' : 'Следующий параграф';

console.log('=== 5. новая загрузка страницы: урок на паузе и карточка');
perezagruzka();
proverka('шапка — название урока',
         elId['pleyer-zag'].textContent === pervyi_pleylist[1].attrs['data-zag'],
         elId['pleyer-zag'].textContent);
proverka('карточка показана', elId['pleyer-vybor'].style.display === '',
         elId['pleyer-vybor'].style.display);
proverka('текст про остановку', /^Вы остановились на (?:§|«)/.test(elId['vybor-tekst'].textContent),
         elId['vybor-tekst'].textContent);
proverka('главная кнопка — «Продолжить»', knopka('vybor-glavnaya') === 'Продолжить',
         knopka('vybor-glavnaya'));
proverka('вторая — «' + sledSlovo + '»',
         knopka('vybor-vtoraya') === sledSlovo, knopka('vybor-vtoraya'));
proverka('кадр на паузе: адрес без autoplay',
         elId.ramka.src === pervyi_pleylist[1].attrs['data-video'] ,
         elId.ramka.src);
proverka('подсвечен тот же пункт', pervyi_pleylist[1].className.includes('aktiven'),
         pervyi_pleylist.map(t => t.className));

console.log('=== 6. «Продолжить»: перемотка на 300 с и play');
elId.ramka.otpravleno = [];
elId['vybor-glavnaya'].onclick();
soobshchenie({ type: 'player:ready' });
const komandy = elId.ramka.otpravleno.map(m => m.type + (m.data && m.data.time !== undefined ? ':' + m.data.time : ''));
proverka('перемотка на 300', komandy.includes('player:setCurrentTime:300'), komandy);
proverka('play после перемотки', komandy.includes('player:play'), komandy);
proverka('карточка скрыта', elId['pleyer-vybor'].style.display === 'none',
         elId['pleyer-vybor'].style.display);

console.log('=== 7. «' + sledSlovo + '» идёт по своему плейлисту');
const tretiy = pervyi_pleylist[2];
elId['vybor-vtoraya'].onclick();
proverka('включён третий пункт того же плейлиста',
         elId.ramka.src === tretiy.attrs['data-video'] ,
         elId.ramka.src);
proverka('он же подсвечен', tretiy.className.includes('aktiven'),
         pervyi_pleylist.map(t => t.className));

console.log('=== 8. урок досмотрен: предлагают следующий');
soobshchenie({ type: 'player:playComplete' });
perezagruzka();
proverka(kino ? 'текст «посмотрели»' : 'текст «закончен»',
         (kino ? /посмотрели$/.test(elId['vybor-tekst'].textContent)
               : /закончен$/.test(elId['vybor-tekst'].textContent)),
         elId['vybor-tekst'].textContent);
proverka('главная кнопка — следующий',
         kino ? /Следующий фильм|Посмотреть снова|Повторить/.test(knopka('vybor-glavnaya'))
              : /Начать|Следующий|Повторить/.test(knopka('vybor-glavnaya')),
         knopka('vybor-glavnaya'));

console.log('=== 9. кнопки вариантов плейлиста');
if (spiski.length > 1) {
  const vtoroy = spiski[1].treks;
  window.shkNabor(1);
  proverka('открыт второй плейлист',
           spiski[1].style.display === '' && spiski[0].style.display === 'none',
           spiski.map(s => s.style.display));
  proverka('под кадром подсвечен тот же вариант',
           knopki_uzly[1].className.includes('aktiven') &&
           !knopki_uzly[0].className.includes('aktiven'),
           knopki_uzly.map(k => k.className));
  proverka('в кадре — первый урок второго плейлиста, на паузе',
           elId.ramka.src === vtoroy[0].attrs['data-video'] ,
           elId.ramka.src);
  proverka('подсвечен он же', vtoroy[0].className.includes('aktiven'),
           vtoroy.map(t => t.className));
  // выбрали урок во втором варианте и перезагрузили страницу
  // Пункт во втором плейлисте бывает и один: берём последний, какой есть.
  const vtoroy_2 = vtoroy[Math.min(1, vtoroy.length - 1)];
  window.shkIgrat(vtoroy_2);
  perezagruzka();
  proverka('после перезагрузки открыт тот вариант, где запомненный урок',
           spiski[1].style.display === '' && spiski[0].style.display === 'none',
           spiski.map(s => s.style.display));
  proverka('шапка — название того же урока',
           elId['pleyer-zag'].textContent === vtoroy_2.attrs['data-zag'],
           elId['pleyer-zag'].textContent);
  // У второго плейлиста может быть всего один пункт (например, в кино
  // художественный фильм один): тогда «следующего» просто нет, и
  // кнопку должны были спрятать.
  if (vtoroy.length > 1) {
    const cel = vtoroy[Math.min(2, vtoroy.length - 1)];
    elId['vybor-vtoraya'].onclick();
    proverka('«следующий» идёт по второму варианту, а не по первому',
             elId.ramka.src === cel.attrs['data-video'], elId.ramka.src);
  } else {
    console.log('  (во втором плейлисте один пункт — «следующий» проверяем иначе)');
    proverka('«следующий» не предлагают: в плейлисте больше нечего',
             (elId['vybor-vtoraya'].style.display || '') === 'none',
             elId['vybor-vtoraya'].style.display);
  }
} else {
  console.log('  (вариант один)');
  proverka('под кадром всё равно есть его название',
           knopki_uzly.length === 1 && knopki_uzly[0].textContent ===
           elId['pl-zag'].textContent,
           [knopki_uzly.length, knopki_uzly[0] && knopki_uzly[0].textContent,
            elId['pl-zag'].textContent]);
}

console.log('=== 10. две панели: открыта всегда одна');
if (skript_stranicy) {
  eval(skript_stranicy);
  klassy_tela.clear();
  window.shkPleylist(true);
  proverka('плейлист открылся', telo.classList.has('pleylist-otkryto'));
  window.shkPanel(true);
  proverka('меню закрыло плейлист',
           telo.classList.has('menu-otkryto') && !telo.classList.has('pleylist-otkryto'));
  window.shkPleylist(true);
  proverka('плейлист закрыл меню',
           telo.classList.has('pleylist-otkryto') && !telo.classList.has('menu-otkryto'));
  window.shkPleylist(false);
  proverka('крестик закрывает', !telo.classList.has('pleylist-otkryto'));
} else {
  console.log('  (общий скрипт страницы не найден — пропускаем)');
}

console.log('=== 11. ширина панели и название плейлиста в шапке');
if (ruki_uzly.length) {
  proverka('ручки ширины на странице', ruki_uzly.length >= 1, ruki_uzly.length);
  window.shkTyan({ key: 'ArrowLeft', shiftKey: false });
  proverka('стрелка влево расширяет (420 → 450)', stil_tela['--panel-shirina'] === '450px',
           stil_tela['--panel-shirina']);
  window.shkTyan({ key: 'ArrowRight', shiftKey: true });
  proverka('стрелка вправо сужает (450 → 370)', stil_tela['--panel-shirina'] === '370px',
           stil_tela['--panel-shirina']);
  for (let i = 0; i < 40; i++) window.shkTyan({ key: 'ArrowRight', shiftKey: true });
  proverka('уже 300 px панель не сделать', stil_tela['--panel-shirina'] === '300px',
           stil_tela['--panel-shirina']);
  for (let i = 0; i < 40; i++) window.shkTyan({ key: 'ArrowLeft', shiftKey: true });
  proverka('шире окна (окно 1600, минимум работы 320) панель не сделать',
           parseFloat(stil_tela['--panel-shirina']) <= 1280, stil_tela['--panel-shirina']);
  proverka('ширина запомнена в браузере', !!localStorage.dannye['shkola.panel'],
           localStorage.dannye['shkola.panel']);
}
if (spiski.length > 1) {
  window.shkNabor(1);
  proverka('в шапке панели — название открытого плейлиста',
           elId['pl-zag'].textContent === knopki_uzly[1].textContent,
           [elId['pl-zag'].textContent, knopki_uzly[1].textContent]);
  window.shkNabor(0);
  proverka('переключили обратно — и название тоже',
           elId['pl-zag'].textContent === knopki_uzly[0].textContent,
           elId['pl-zag'].textContent);
}

console.log('=== 12. кнопка плейлиста на кадре и значок меню');
proverka('в меню нет пункта «Плейлист»',
         !/class="panel-plitka pl-punkt"/.test(html));
proverka('значок меню зовёт shkMenu()',
         /aria-label="Меню"[^>]*onclick="return shkMenu\(\)"/.test(html));
proverka('на кадре есть кнопка плейлиста',
         /class="pleyer-knopka"[^>]*onclick="return shkPleylistTog\(\)"/.test(html));
console.log('=== 14. единый стандарт списков: просто текст');
// Ни пункты меню, ни пункты плейлиста не носят ни подложки, ни жёлтой
// полосы слева, ни рамки в фокусе. Проверяем сами правила оформления:
// строка списка — это текст, а не кнопка.
const blok = (ot, do_) => {
  const i = html.indexOf(ot);
  return i < 0 ? '' : html.slice(i, html.indexOf('}', i) + 1);
};
const plytka = blok('a.panel-plitka{');
const trek = blok('a.trek{');
proverka('у пункта меню нет подложки',
         !!plytka && !/background:(?!none)/.test(plytka), plytka);
proverka('у пункта меню нет жёлтой полосы слева',
         !!plytka && !/border-left/.test(plytka), plytka);
proverka('у пункта плейлиста нет подложки',
         !!trek && !/background:(?!none)/.test(trek), trek);
proverka('у пункта плейлиста нет полосы слева и рамки',
         !!trek && !/border-left\s*:\s*[1-9]/.test(trek) &&
         !/(^|;)\s*border\s*:\s*[1-9]/.test(trek) &&
         !/outline\s*:\s*(?!none)/.test(trek), trek);
proverka('синим ничего не подсвечиваем',
         !/#[0-9a-f]*[0-9a-f]*(a0c|07c|1a4f7a|3b82f6)/i.test(html));
proverka('название плейлиста не обводится рамкой в фокусе',
         /summary\.pl-imya:focus[^}]*outline:none/.test(html));
proverka('у названий плейлистов и глав нет жёлтого',
         /summary\.pl-imya\{[\s\S]{0,320}color:#8b95a5/.test(html) &&
         /\.trek-gruppa\{[\s\S]{0,220}color:#8b95a5/.test(html));
proverka('в боковом меню не осталось задвоенного разделителя',
         !/class="panel-razd"/.test(html));
proverka('у пунктов меню нет обводки на фокусе',
         /a\.panel-plitka:focus[^{]*\{[^}]*outline:none/.test(html));
proverka('у пунктов плейлиста нет обводки на фокусе',
         /a\.trek:focus[^{]*\{[^}]*outline:none/.test(html));
proverka('на уведомлении есть кнопка «Закрыть»',
         /id="vybor-tretiya"[^>]*>Закрыть</.test(html));
proverka('строка с именем и целью есть на странице',
         /id="imya-stroka"/.test(html));
proverka('крестик подсвечивается одинаково в обеих панелях',
         /a\.panel-zakryt:focus, a\.panel-zakryt:hover/.test(html) &&
         !/\.panel-verh[^{]*\.panel-zakryt\{[^}]*border-color:#ffd23f/.test(html));
// Панель — столбик: шапка отдельной полосой, список прокручивается в
// своей области. Иначе при прокрутке список уносил шапку с собой.
proverka('панель собрана столбиком',
         /\.panel\{[\s\S]{0,260}display:flex; flex-direction:column/.test(html));
proverka('шапка панели не прокручивается вместе со списком',
         /\.panel-verh\{[\s\S]{0,120}flex:0 0 auto/.test(html));
proverka('у панели есть своя область прокрутки',
         /\.panel-telo\{[\s\S]{0,120}overflow-y:auto/.test(html));
proverka('обе панели: и меню, и плейлист — с областью прокрутки',
         (html.match(/class="panel-telo"/g) || []).length === 2,
         (html.match(/class="panel-telo"/g) || []).length);
if (skript_stranicy && elId['pleylist-panel']) {
  klassy_tela.clear();
  window.shkPleylist(false);
  window.shkPleylistTog();
  proverka('кнопка вернула закрытый плейлист',
           telo.classList.has('pleylist-otkryto'));
  window.shkPleylistTog();
  proverka('кнопка закрыла плейлист', !telo.classList.has('pleylist-otkryto'));
  window.shkMenu();
  proverka('значок меню открывает меню', telo.classList.has('menu-otkryto'));
  window.shkMenu();
  proverka('и закрывает его', !telo.classList.has('menu-otkryto'));
} else {
  console.log('  (общий скрипт не найден — переключение пропускаем)');
}

console.log('=== 13. плейлисты под кадром');
proverka('под кадром столько же плейлистов, сколько в панели',
         knopki_uzly.length === spiski.length,
         [knopki_uzly.length, spiski.length]);
proverka('содержимое совпадает с панелью',
         knopki.every((k, i) => {
           const a = k.treki.map(t => t.video).join(',');
           const b = spiski[i].treks.map(t => t.attrs['data-video']).join(',');
           return a === b && a.length > 0;
         }),
         knopki.map((k, i) => [k.treki.length, spiski[i].treks.length]));
proverka('открытый плейлист подсвечен',
         knopki_uzly[0].className.includes('aktiven'),
         knopki_uzly.map(k => k.className));
if (elId['pl-zag'] && knopki_uzly.length > 1) {
  // Нажали на пункт в списке под кадром — урок играет, а в панели
  // открылся тот плейлист, откуда его взяли.
  const chuzhoy = knopki_uzly[1];
  const ego_trek = spiski[1].treks[0];
  window.shkNabor(0);
  window.shkIgrat(ego_trek);
  proverka('нажатие на пункт включает урок',
           elId.ramka.src === 
                              ego_trek.attrs['data-video'] ,
           elId.ramka.src);
  proverka('и в панели открылся тот плейлист, откуда урок',
           spiski[1].style.display === '' && spiski[0].style.display === 'none',
           spiski.map(s => s.style.display));
  proverka('шапка панели — его название',
           elId['pl-zag'].textContent === knopki_uzly[1].textContent,
           [elId['pl-zag'].textContent, knopki_uzly[1].textContent]);
  // Раскрытие: открыт всегда один.
  knopki_uzly[0].open = false; knopki_uzly[1].open = false;
  knopki_uzly[0].summary.onclick();
  proverka('раскрыли первый — он и открыт, второй закрылся',
           knopki_uzly[0].open === true && knopki_uzly[1].open === false,
           [knopki_uzly[0].open, knopki_uzly[1].open]);
  knopki_uzly[1].summary.onclick();
  proverka('раскрыли второй — первый закрылся',
           knopki_uzly[1].open === true && knopki_uzly[0].open === false,
           [knopki_uzly[0].open, knopki_uzly[1].open]);
  proverka('в панели тоже открылся второй',
           spiski[1].style.display === '' && spiski[0].style.display === 'none',
           spiski.map(s => s.style.display));
} else {
  console.log('  (плейлист один — переключение пропускаем)');
}

console.log('\nИтог: ошибок ' + oshibki);
process.exit(oshibki ? 1 : 0);
