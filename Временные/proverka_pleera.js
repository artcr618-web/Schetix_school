// Стенд плеера: без браузера проверяем весь путь зрителя.
//
// Подставляем крошечный DOM и запускаем скрипты, снятые с настоящей
// страницы видеоуроков. Правила оформления берём из файла, на который
// страница ссылается, — в самой странице их больше нет. Плейлисты берём из её же разметки, поэтому
// стенд проверяет то, что ребёнок увидит на телевизоре, а не выдумку.
//
// Запуск:
//   node Временные/proverka_pleera.js "Проект/База данных/HTML/5 класс/История/видеоуроки.html"

const fs = require('fs');

const put = process.argv[2] || 'Проект/База данных/HTML/5 класс/История/видеоуроки.html';
const path = require('path');
// Оформление лежит отдельным файлом, поэтому часть проверок смотрит
// правила, а часть — разметку. Читаем оба и склеиваем: правил в этой
// странице больше нет, они в файле, на который она ссылается.
const syroy = fs.readFileSync(put, 'utf8');
const ssylka = syroy.match(/<link[^>]+href="([^"]+\.css)"/);
if (!ssylka) { console.error('В странице нет ссылки на файл оформления: ' + put); process.exit(2); }
const css_put = path.resolve(path.dirname(put), ssylka[1]);
const css = fs.readFileSync(css_put, 'utf8');
const html = syroy + '\n/* оформление: ' + path.basename(css_put) + ' */\n' + css;

// Страница лекций устроена как страница кино (подпись пункта — тоже
// время), но слова у неё свои, и говорит она о себе сама — атрибутом
// на body. Ищем именно тег: то же слово стоит и в скрипте, в примечании,
// и по нему стенд принимал бы за лекции страницу кино.
const lekcii = /<body[^>]*data-rezhim="лекции"/.test(syroy);

const skripty = (html.match(/<script>[\s\S]*?<\/script>/g) || [])
  .map(s => s.replace(/<\/?script>/g, ''));
const skript_pleera = skripty.find(s => s.includes('shkola.urok.'));
const skript_stranicy = skripty.find(s => s.includes('shkola.home'));
if (!skript_pleera) { console.error('НЕ НАЙДЕН скрипт плеера в ' + put); process.exit(2); }

// ---------- настоящие плейлисты из разметки ----------
function razor(blok) {
  const treki = [];
  const re = /<a class="trek"[^>]*data-video="([^"]*)"[^>]*data-zag="([^"]*)"[^>]*data-nomer="([^"]*)"[^>]*data-tema="([^"]*)"[^>]*data-glava="([^"]*)"[^>]*>(<span class="trek-nomer[^"]*")?/g;
  let m;
  while ((m = re.exec(blok))) {
    treki.push({ video: m[1], zag: m[2], nomer: m[3], tema: m[4],
                 glava: m[5], kolco: (m[6] || '').includes('trek-kolco') });
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
// Плейлисты под кадром — теперь СПИСОК ПЛЕЙЛИСТОВ: строка на каждый,
// без содержимого (уроки живут в панели). Строка того же класса, что
// пункт бокового меню, поэтому вид у них буквально один и тот же.
// Отсюда и берём: сколько строк, как называются, какая открыта.
const knopki = [...html.matchAll(
    /<a class="panel-plitka pl-plitka([^"]*)"[^>]*data-nabor="(\d+)"[^>]*>([^<]*)<\/a>/g)]
  .map(m => ({ nomer: Number(m[2]), aktiven: m[1].includes('tekushchiy'),
               imya: m[3], treki: [] }));
const nachala_blokov = knopki.map(k => ({ ot: 0 }));

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
    'data-nomer': t.nomer, 'data-tema': t.tema, 'data-glava': t.glava,
  }));
  u.querySelector = sel => (sel === '.trek' ? (u.treks[0] || null) : null);
  u.querySelectorAll = sel => (sel === '.trek' ? u.treks : []);
  if (!kusok.otkryt) u.style.display = 'none';
  u.treks.forEach(t => { t.parentNode = u; });
  return u;
}

const spiski = kuski.map(pleylist);
spiski.forEach((sp, i) => { sp.attrs['data-imya'] = knopki[i].imya; });
// Строка под кадром — та же ссылка, что пункт меню: href, data-nabor
// и onclick. Нажатие открывает плейлист в панели (shkNabor).
const knopki_uzly = knopki.map(k => {
  const u = uzel('a', { class: 'panel-plitka pl-plitka' +
                               (k.aktiven ? ' tekushchiy' : ''),
                        'data-nabor': String(k.nomer) });
  u.textContent = k.imya;
  u.closest = () => null;
  return u;
});

const elId = {};
['pleyer', 'pleyer-zag', 'pleyer-podzag', 'pleyer-vybor', 'vybor-tekst',
 'vybor-glavnaya', 'vybor-vtoraya', 'pleylist-panel', 'pl-zag']
  .forEach(i => { elId[i] = uzel('div', {}); });
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

// body страницы: класс (плейлист открыт) и признак страницы лекций.
// Второй берём из самой страницы, из тега body, — по нему скрипт плеера
// выбирает слова («Следующая лекция» вместо «Следующий фильм»).
const telo = uzel('body', lekcii ? { 'data-rezhim': 'лекции' } : {});
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
    if (sel === '.pl-plitka') return knopki_uzly;
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
// Нажатие на строку под кадром: браузер сам зовёт onclick из разметки,
// в стенде подставляем то же самое — открыть этот плейлист в панели.
knopki_uzly.forEach(u => {
  u.onclick = () => window.shkNabor(u.attrs['data-nabor']);
});
global.window = Object.assign(global.window || {}, { innerWidth: 1600 });
// у body своя переменная ширины панели
const stil_tela = { '--panel-shirina': '420px' };
telo.style = { setProperty: (k, v) => { stil_tela[k] = v; } };
global.getComputedStyle = () => ({
  getPropertyValue: k => stil_tela[k] || '',
});

eval(skript_pleera);
zastavka_paneli();

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
   'shkProdolzhit', 'shkTyan', 'shkBanner',
   'shkBannerIgrat', 'shkBannerGde'
  ].forEach(i => { try { delete window[i]; } catch (e) { window[i] = undefined; } });
  eval(skript_pleera);
  zastavka_paneli();
}
/* Открытие панели живёт в скрипте страницы, а стенд подставляет его
   позже — в настоящей странице скрипты тоже идут друг за другом, и к
   моменту нажатия всё уже на месте. До этого ставим заглушку и
   запоминаем, что её позвали: проверяем, что строка плейлиста под
   кадром ОТКРЫВАЕТ плейлист в панели, а не запускает урок. */
let panel_otkryvali = [];
function zastavka_paneli(){
  if(!window.shkPleylist){
    window.shkPleylist = function(o){ panel_otkryvali.push(!!o); return false; };
  }
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
// Над заголовком — глава пункта: её приносит плейлист (data-glava),
// и стоит она только тогда, когда у пункта она есть.
proverka('над шапкой — глава пункта из плейлиста',
         elId['pleyer-podzag'].textContent ===
           (pervyi_pleylist[1].attrs['data-glava'] || '') &&
         (elId['pleyer-podzag'].hidden ===
            !pervyi_pleylist[1].attrs['data-glava']),
         { v_shapke: elId['pleyer-podzag'].textContent,
           v_pleyliste: pervyi_pleylist[1].attrs['data-glava'],
           skryt: !!elId['pleyer-podzag'].hidden });
// Глава — не часть пункта: в подписи пункта её быть не должно вовсе
// («Гл. I. … — § 1. …» больше не встречается).
const kusok_pervogo = kuski[0];
proverka('у пункта глава — не сам пункт: в подписи нет слова «Глава»',
         !kusok_pervogo.treki.some(x => /^Гл\.|^Глава\b/.test(x.zag)),
         kusok_pervogo.treki.filter(x => /^Гл\.|^Глава\b/.test(x.zag)).map(x => x.zag));
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

// Страница кино и страница лекций говорят иначе, чем страница уроков:
// там подпись пункта — время («1 ч 20 мин»), у уроков — «§ 12». Стенд
// повторяет это же правило, иначе он ругался бы на правильную страницу.
const podpis_mesta = (pervyi_pleylist[1].attrs['data-nomer'] || '').trim();
const kino = !!podpis_mesta && podpis_mesta[0] !== '§';
const sledSlovo = lekcii ? 'Следующая лекция'
                         : (kino ? 'Следующий фильм' : 'Следующий параграф');

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
         kino ? /Следующ(ий фильм|ая лекция)|Посмотреть снова|Повторить/
                  .test(knopka('vybor-glavnaya'))
              : /Начать|Следующий|Повторить/.test(knopka('vybor-glavnaya')),
         knopka('vybor-glavnaya'));

console.log('=== 9. кнопки вариантов плейлиста');
if (spiski.length > 1) {
  const vtoroy = spiski[1].treks;
  // Выбор плейлиста сам урок не включает: кадр остаётся как был, пока
  // человек не нажмёт пункт. Так же ведёт себя и пункт бокового меню.
  const bylo_v_kadre = elId.ramka.src;
  window.shkNabor(1);
  proverka('открыт второй плейлист',
           spiski[1].style.display === '' && spiski[0].style.display === 'none',
           spiski.map(s => s.style.display));
  proverka('под кадром подсвечен тот же вариант',
           knopki_uzly[1].className.includes('tekushchiy') &&
           !knopki_uzly[0].className.includes('tekushchiy'),
           knopki_uzly.map(k => k.className));
  proverka('выбор плейлиста кадр не трогает',
           elId.ramka.src === bylo_v_kadre,
           [bylo_v_kadre, elId.ramka.src]);
  window.shkIgrat(vtoroy[0]);
  proverka('нажатие на пункт включает урок второго плейлиста',
           elId.ramka.src === vtoroy[0].attrs['data-video'],
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
console.log('=== 14. стандарт списков: текст, а играющий пункт — плашкой');
// Строка списка — простой текст: подложки нет, рамок нет. Но место под
// жёлтую чёрточку оставлено у каждой строки (прозрачная полоса 6 px),
// иначе играющий пункт сдвигал бы соседей. Играющий пункт — подложка,
// жёлтая чёрточка слева и жёлтый номер параграфа. Стандарт один на все
// списки: и под кадром, и в боковом меню, и в панели плейлиста.
const blok = (ot) => {
  const i = html.indexOf(ot);
  return i < 0 ? '' : html.slice(i, html.indexOf('}', i) + 1);
};
const plytka = blok('a.panel-plitka{');
const trek = blok('a.trek{');
proverka('у пункта меню в покое нет подложки',
         !!plytka && !/\n\s*background:#/.test(plytka.split(':hover')[0]),
         plytka);
proverka('у пункта меню рамка прозрачная, номер не липнет к кромке (28 px)',
         !!plytka && /border:3px solid transparent/.test(plytka) &&
         /padding:8px 14px 8px 28px/.test(plytka), plytka);
proverka('у пункта под кадром в покое нет подложки',
         !!trek && !/\n\s*background:#/.test(trek.split(':hover')[0]), trek);
proverka('у пункта под кадром тот же отступ слева (28 px)',
         !!trek && /border:3px solid transparent/.test(trek) &&
         /padding:8px 14px 8px 28px/.test(trek), trek);
// Строка плейлиста под кадром — тот же класс, что пункт бокового меню:
// отдельных правил у неё нет, поэтому вид буквально один и тот же.
proverka('строка плейлиста под кадром — тем же классом, что пункт меню',
         html.includes('class="panel-plitka pl-plitka'),
         (html.match(/class="panel-plitka pl-plitka[^"]*"/) || [])[0] || 'нет');
proverka('под кадром нет раскрывающихся списков уроков',
         !/\.pl-telo|summary\.pl-imya|class="pl-blok/.test(html));
// Отметка активной строки — общее правило: те же подложка и полоса у
// пункта списка, у строки настроек тренажёра и у плашки меню.
const akt = blok('a.trek.aktiven, a.nastr-stroka.aktiven, a.panel-plitka.tekushchiy{');
proverka('играющий пункт — серая подложка под жёлтой полосой',
         !!akt && /--fon-stroki:linear-gradient\(#232c38, #232c38\)/.test(akt) &&
         !/border-color:#ffd23f/.test(akt), akt);
// Играющий пункт — как плашка предмета: жёлтая полоса во всю высоту
// строки у левого края и подложка потемнее. Короткой чёрточки посреди
// строки больше нет (её просили заменить на полосу).
proverka('у играющего пункта — жёлтая полоса слева во всю высоту, как у плашки',
         /a\.trek\.aktiven, a\.nastr-stroka\.aktiven, a\.panel-plitka\.tekushchiy\{[\s\S]{0,900}?--polosa-stroki:8px[\s\S]{0,900}?background-image:linear-gradient\(#ffd23f, #ffd23f\)[\s\S]{0,900}?background-size:var\(--polosa-stroki\) 100%/.test(html));
proverka('чёрточки-флажка посреди строки не осталось',
         !/a\.trek\.aktiven::before/.test(html));
proverka('скругление строки списка — 10 px',
         !!trek && /border-radius:10px/.test(trek), trek);
proverka('у играющего пункта жёлтый номер параграфа',
         /a\.trek\.aktiven \.trek-nomer, a\.nastr-stroka\.aktiven \.nastr-schet\{[\s\S]{0,80}?color:#ffd23f/.test(html),
         (html.match(/a\.trek\.aktiven \.trek-nomer[^}]*\}/) || [])[0]);
// Рамка в списках одинарная: под курсором и на клавиатурном фокусе.
// Двойная рамка — это плашки (жёлтая плюс свечение), у строк её нет.
proverka('рамку строка списка получает под курсором и на фокусе, одинарную',
         /a\.trek:hover, a\.trek:focus-visible\{border-color:#ffd23f\}/.test(html) &&
         !/a\.trek[^{]*\{[^}]*box-shadow/.test(html));
const akt_menu = blok('a.panel-plitka.tekushchiy{');
proverka('текущий пункт меню — та же отметка: подложка и жёлтая полоса',
         !!akt_menu && /--polosa-stroki:8px/.test(akt_menu) &&
         /background-size:var\(--polosa-stroki\) 100%/.test(akt_menu),
         akt_menu);
// Размеры списков набраны по эталону YouTube/Rutube: строка 24 px,
// заголовок главы 21 px, номер в колонке 58 px с зазором 12 px.
proverka('строка списка — 24 px, заголовок главы — 21 px',
         /\.trek-tema\{[^}]*font-size:24px/.test(html) &&
         /\.trek-gruppa\{[\s\S]{0,140}?font-size:21px/.test(html));
// Колонка номера — ФИКСИРОВАННОЙ ширины, 58 px по самому широкому номеру
// («§ 45» — 50 px, «§ 10,» — 58 px при 24 px), до темы 10 px: раньше стоял
// min-width:50px, и «§ 10–11» (93 px) раздвигала колонку — темы начинали
// строки на разном месте.
proverka('номер стоит по левому краю колонки 58 px, до темы 10 px',
         /\.trek-nomer\{[\s\S]{0,400}?flex:0 0 58px[\s\S]{0,120}?text-align:left/
           .test(html) &&
         /a\.trek\{[\s\S]{0,220}?gap:10px/.test(html));
// Сдвоенный параграф — двумя строками: «§ 10,» и «11». Так и единичный,
// и парный номер занимают одну колонку, а не растягивают её.
proverka('сдвоенный параграф в колонке — двумя строками («§ 10,» / «11»)',
         /<span class="trek-nomer">§ \d+,<br>\d+<\/span>/.test(html),
         (html.match(/<span class="trek-nomer">[^<]*<br>[^<]*<\/span>/) || [])[0] || 'нет');
proverka('тире в колонке номера не осталось',
         !/<span class="trek-nomer">[^<]*[–—][^<]*<\/span>/.test(html),
         (html.match(/<span class="trek-nomer">[^<]*[–—][^<]*<\/span>/) || [])[0] || 'нет');
// Пункт без параграфа («Введение», «Итоговое повторение»): в колонке
// номера — кольцо с точкой, размером с цифру.
const est_kolco = html.includes('class="trek-nomer trek-kolco"');
proverka('у пункта без параграфа — кольцо с точкой вместо номера',
         (!est_kolco && !html.match(/data-nomer=""/)) ||
         (/\.trek-kolco\{[\s\S]{0,180}?align-self:flex-start/.test(html) &&
          /\.trek-kolco svg\{[\s\S]{0,80}?width:22px/.test(html) &&
          /class="trek-nomer trek-kolco"[\s\S]{0,400}?<circle cx="12" cy="12" r="8\.6"/.test(html)),
         est_kolco ? 'кольцо есть' : 'пунктов без номера на странице нет');
// «Введение» — это не параграф: ни «§ 1» в подписи пункта, ни номера
// в данных. То же у «Итогового повторения» и «Итогов главы».
// Разметка строки: data-zag (подпись для шапки), data-nomer, data-tema.
const bez_nomera = [...html.matchAll(/<a class="trek"[^>]*?data-zag="([^"]*)"[^>]*?data-nomer="([^"]*)"[^>]*?data-tema="([^"]*)"/g)]
  .map(m => ({ zag: m[1], nomer: m[2], tema: m[3] }));
const bez_nom = bez_nomera.filter(m => !m.nomer);
const s_nomerom = bez_nomera.filter(m => m.nomer);
proverka('у пункта без номера подпись — без «§» (просто тема)',
         bez_nom.every(m => m.zag === m.tema),
         bez_nom.filter(m => m.zag !== m.tema).slice(0, 3));
// У кино и лекций в колонке номера стоит время проигрывания, и точка
// после него не нужна: «§ 1. Тема» — для параграфов, «1 ч 20 мин Тема» —
// для фильмов.
const paragrafy = s_nomerom.filter(m => m.nomer.startsWith('§'));
// В подписи сдвоенный параграф разворачивается без тире: «§ 10–11. Тема»
// становится «§ 10, 11. Тема» — как в колонке, только в строку.
const nomer_v_tekste = n => n.replace(/^(§\s*\d+)\s*[–—-]\s*(\d+)$/, '$1, $2');
proverka('у параграфа подпись — «§ N. Тема», как в учебнике',
         paragrafy.every(m => m.zag === nomer_v_tekste(m.nomer) + '. ' + m.tema),
         paragrafy.filter(m => m.zag !== nomer_v_tekste(m.nomer) + '. ' + m.tema)
           .slice(0, 3));
proverka('у пункта со временем проигрывания подпись — время и тема',
         s_nomerom.filter(m => !m.nomer.startsWith('§'))
           .every(m => m.zag === m.nomer + ' ' + m.tema));
// Глава — отдельная строка, а не часть пункта: ни «Гл. I. … — § 1. …»
// в теме пункта, ни времени проигрывания в заголовке группы.
proverka('глава не склеена с пунктом',
         !bez_nomera.some(m => /^Гл\.|^Глава\b/.test(m.tema) && m.tema.includes('§')),
         bez_nomera.filter(m => /^Гл\.|^Глава\b/.test(m.tema) && m.tema.includes('§')).slice(0, 2));
const gruppy = [...html.matchAll(/<div class="trek-gruppa">([^<]*)<\/div>/g)]
  .map(m => m[1]);
proverka('в заголовках групп нет времени проигрывания',
         !gruppy.some(g => /\d+\s*(час|урок)/i.test(g)),
         gruppy.filter(g => /\d+\s*(час|урок)/i.test(g)));
proverka('«Гл.» в заголовке группы развёрнуто в «Глава»',
         !gruppy.some(g => /^\s*Гл\./.test(g)),
         gruppy.filter(g => /^\s*Гл\./.test(g)));
// Под кадром: глава — подзаголовком, под ней линия, надпись и список
// плейлистов, а ниже — плашки разделов предмета. Над кадром остаётся
// только название урока.
proverka('глава — под кадром (#pleyer-podzag внутри .pleyer-niz)',
         /<div class="pleyer-niz">[\s\S]{0,400}?id="pleyer-podzag"/.test(html) &&
         /\.pleyer-podzag\{[\s\S]{0,200}?color:#8b95a5/.test(html));
proverka('под кадром есть разделительная линия, как в шапке панели',
         /<div class="pl-razd">/.test(html) &&
         /\.pl-razd\{[\s\S]{0,120}?border-top:2px solid #2a3340/.test(html));
proverka('над списком плейлистов стоит надпись «Плейлисты»',
         /<div class="pl-zagolovok">Плейлисты<\/div>/.test(html) &&
         /\.pl-zagolovok\{[\s\S]{0,160}?font-size:21px/.test(html));
const por = html.match(/<div class="pleyer-niz">[\s\S]*?<\/div><\/div>/);
// Порядок в разметке: кадр → глава → линия → «Плейлисты» → строки.
const i_kadr = html.indexOf('<div class="pleyer-mesto">');
const i_glava = html.indexOf('id="pleyer-podzag"');
const i_lin = html.indexOf('<div class="pl-razd">');
const i_zag = html.indexOf('<div class="pl-zagolovok">');
const i_spis = html.indexOf('<div class="pl-vse">');
proverka('порядок под кадром: кадр, глава, линия, надпись, список',
         i_kadr >= 0 && i_kadr < i_glava && i_glava < i_lin &&
         i_lin < i_zag && i_zag < i_spis,
         { kadr: i_kadr, glava: i_glava, liniya: i_lin, zag: i_zag, spis: i_spis });
// Плашки разделов: те же, что на странице предмета, а плашка текущего
// материала не показывается — она вела бы на страницу, где мы и стоим.
const est_razdely = /<div class="pl-razdely">[\s\S]{0,200}?pl-zagolovok">Ещё по курсу</.test(html);
// Подсказка о прокрутке: надпись с рукой посреди полосы. Показывается
// только там, где листают пальцем, и только пока полосу не сдвинули.
if (est_razdely) {
  proverka('в полосе есть подсказка «Листайте вбок» с рукой',
           /<div class="pl-podskazka" aria-hidden="true">[\s\S]{0,900}?<span>Листайте вбок<\/span><\/div>/.test(html));
  proverka('подсказка показывается только пальцем и прячется после сдвига',
           /\.pl-podskazka\{display:none\}/.test(html) &&
           /\(hover:none\) and \(pointer:coarse\)/.test(html) &&
           /\.pl-polosa\[data-kon="1"\]:not\(\[data-listano\]\) \.pl-podskazka/.test(html) &&
           /data-listano/.test(html));
}
proverka('под плейлистами — блок «Ещё по курсу» с плашками',
         est_razdely || !/<a class="plitka/.test(html),
         est_razdely ? 'есть' : 'на этой странице плашек разделов нет');
if (est_razdely) {
  const blok = html.slice(html.indexOf('<div class="pl-razdely">'));
  const imena_plitok = [...blok.matchAll(/<a class="plitka[^"]*"[^>]*>[\s\S]*?<span class="nazv">([^<]*)/g)]
    .map(m => m[1]);
  proverka('плашек разделов не меньше двух', imena_plitok.length >= 2, imena_plitok);
  const svoih = imena_plitok.filter(n => n.includes('Видеоуроки'));
  proverka('плашка текущего раздела скрыта',
           svoih.length === 0, imena_plitok);
}
proverka('шапка собрана в столбик: глава над заголовком',
         /\.pleyer-shapka\{[\s\S]{0,220}?flex-direction:column/.test(html));
proverka('списки в панели начинаются от кромки: отступа у всего списка нет',
         !/\.panel-telo \.pleylist\{margin-left/.test(html));
// Панель не закрывается сама — состояние живёт в браузере.
proverka('панель помнит, что открыта (ключ shkola.panel-otkryt)',
         /shkola\.panel-otkryt/.test(html));
proverka('открытие запоминается, закрытие стирается',
         /localStorage\.setItem\(KP, chto\)/.test(html) &&
         /panel_pomnit\('menu'\)/.test(html) &&
         /panel_pomnit\(''\)/.test(html));
proverka('на новой странице панель возвращается открытой',
         /localStorage\.getItem\(KP\)/.test(html));
// Панель плейлиста — тем же простым текстом, что и остальные списки:
// своих правил у её строк нет (отменено 8 октября — плашка и жёлтая
// полоса были у каждого пункта, и список выглядел как сплошь активный).
proverka('у панели плейлиста строки — по общим правилам, без своего вида',
         !/#pleylist-panel a\.trek/.test(html) &&
         !/#pleylist-panel \.trek-nomer/.test(html),
         (html.match(/#pleylist-panel [^{]*\{/g) || []).join(' | ') || 'нет');
// Окно побольше: у правила теперь длинный пояснительный комментарий.
proverka('номер обычной строки серый, как у прочих строк списка',
         /\.trek-nomer\{[\s\S]{0,700}color:#8b95a5/.test(html));
// Время проигрывания (кино, лекции) длиннее колонки номера: таким строкам
// колонка — по содержимому, без переноса на три строки.
proverka('время проигрывания стоит одной строкой, колонку не ломает',
         /\.trek-nomer\.trek-vremya\{[\s\S]{0,200}?white-space:nowrap/.test(html) &&
         /<span class="trek-nomer trek-vremya">\d+\s*ч\s*\d+\s*мин<\/span>/.test(html) ||
         !/<span class="trek-nomer[^"]*">\d+ ч/.test(html),
         (html.match(/<span class="trek-nomer trek-vremya">[^<]*<\/span>/) || [])[0] || 'нет');
proverka('синим ничего не подсвечиваем',
         !/#[0-9a-f]*[0-9a-f]*(a0c|07c|1a4f7a|3b82f6)/i.test(html));
proverka('у заголовков глав в панели нет жёлтого',
         /\.trek-gruppa\{[\s\S]{0,220}color:#8b95a5/.test(html));
proverka('в боковом меню не осталось задвоенного разделителя',
         !/class="panel-razd"/.test(html));
// На пульте указателя нет: где стоит пульт, видно по жёлтой рамке
// на фокусе — как у плашек. Обычная браузерная обводка снята.
proverka('в покое у пунктов меню обводки нет',
         /a\.panel-plitka:focus, a\.panel-plitka:hover,[^{]*\{[^}]*outline:none/
           .test(html));
proverka('на фокусе у пунктов меню жёлтая рамка',
         /a\.panel-plitka:hover, a\.panel-plitka:focus-visible\{border-color:#ffd23f\}/
           .test(html));
proverka('в покое у пунктов под кадром обводки нет',
         /a\.trek:hover, a\.trek:focus, a\.trek:focus-visible\{[^}]*outline:none/
           .test(html));
proverka('на фокусе у пунктов под кадром жёлтая рамка',
         /a\.trek:hover, a\.trek:focus-visible\{border-color:#ffd23f\}/
           .test(html));
proverka('на уведомлении крестик закрытия, а не слово «Закрыть»',
         /id="vybor-zakryt"[^>]*aria-label="Закрыть"/.test(html) &&
         !/vybor-tretiya/.test(html) &&
         !/>Закрыть</.test(html));
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

console.log('=== 13. список плейлистов под кадром');
proverka('под кадром столько строк, сколько плейлистов',
         knopki_uzly.length === spiski.length,
         [knopki_uzly.length, spiski.length]);
proverka('названия совпадают с панелью',
         knopki.every((k, i) => k.imya === spiski[i].attrs['data-imya']) &&
         knopki.length > 0,
         knopki.map((k, i) => [k.imya, spiski[i].attrs['data-imya']]));
proverka('под кадром нет самих уроков — только строки плейлистов',
         !/<div class="pl-vse">[\s\S]{0,4000}?class="trek"/.test(html),
         (html.match(/<div class="pl-vse">[\s\S]{0,200}/) || [])[0] || 'нет');
proverka('открытый плейлист отмечен текущим',
         knopki_uzly[0].className.includes('tekushchiy'),
         knopki_uzly.map(k => k.className));
if (elId['pl-zag'] && knopki_uzly.length > 1) {
  // Нажали на строку второго плейлиста — он открылся в панели,
  // а кадр не тронут: человек ещё выбирает, что смотреть.
  window.shkIgrat(spiski[0].treks[0]);          // что-то уже играет
  const bylo = elId.ramka.src;
  panel_otkryvali = [];
  knopki_uzly[1].onclick();
  proverka('нажатие открывает этот плейлист в панели',
           spiski[1].style.display === '' && spiski[0].style.display === 'none',
           spiski.map(s => s.style.display));
  proverka('и панель плейлиста открылась',
           telo.classList.has('pleylist-otkryto'),
           telo.classList.has('pleylist-otkryto'));
  proverka('шапка панели — его название',
           elId['pl-zag'].textContent === knopki_uzly[1].textContent,
           [elId['pl-zag'].textContent, knopki_uzly[1].textContent]);
  proverka('кадр открытие списка не трогает — урок тот же',
           elId.ramka.src === bylo, [bylo, elId.ramka.src]);
  knopki_uzly[0].onclick();
  proverka('вернулись к первому — он открыт в панели',
           spiski[0].style.display === '' && spiski[1].style.display === 'none',
           spiski.map(s => s.style.display));
  proverka('и отметка снова на нём',
           knopki_uzly[0].className.includes('tekushchiy') &&
           !knopki_uzly[1].className.includes('tekushchiy'),
           knopki_uzly.map(k => k.className));
} else {
  console.log('  (плейлист один — переключение пропускаем)');
}

console.log('\nИтог: ошибок ' + oshibki);
process.exit(oshibki ? 1 : 0);
