// Блок «Ещё по курсу» на страницах материалов: проверка связей, а не вида.
//
// Блок «Ещё по курсу» (плашки остальных материалов предмета) ставится под
// содержимым на каждой странице материала — и на видеоуроках, и на кино,
// и на контрольных, и на страницах-заглушках. Правило у него одно:
// **страница ссылается ровно на все остальные страницы своего предмета**
// — не больше и не меньше, и никогда на саму себя (плашка вела бы туда,
// где человек и стоит).
//
// Проверка статическая: читаем html и сверяем адреса с файлами на диске.
// Браузер не нужен, поэтому прогон занимает доли секунды — можно гонять
// на каждой сборке.
//
//   node Временные/proverka_razdelov.js
//   node Временные/proverka_razdelov.js "Проект/База данных/HTML"
const fs = require('fs');
const path = require('path');

const koren = process.argv[2] || 'Проект/База данных/HTML';

let oshibki = 0;
const proverka = (chto, uslovie, fakticheski) => {
  console.log((uslovie ? '  ок   ' : '  ОШИБКА ') + chto +
    (uslovie ? '' : ' → ' + JSON.stringify(fakticheski)));
  if (!uslovie) oshibki++;
};
const bez_myagkih = s => String(s || '').replace(/\u00ad/g, '');

// Страница материала — та, что лежит в папке предмета: класс/предмет/файл.
// Страницы уровней (класс, предмет, вход) в счёт не идут: у них своё
// устройство, и блока «Ещё по курсу» на них нет.
const po_papkam = new Map();
function sobiraem(sp) {
  for (const imya of fs.readdirSync(sp).sort()) {
    const polny = path.join(sp, imya);
    if (fs.statSync(polny).isDirectory()) sobiraem(polny);
    else if (imya.endsWith('.html')) {
      const otnositelno = path.relative(koren, polny).split(path.sep);
      if (otnositelno.length !== 3) continue;   // не класс/предмет/страница
      const papka = path.dirname(polny);
      if (!po_papkam.has(papka)) po_papkam.set(papka, []);
      po_papkam.get(papka).push(imya);
    }
  }
}
sobiraem(koren);

let stranic = 0, s_blokom = 0;
for (const [papka, fayly] of po_papkam) {
  // В папке, где лежит один материал, ссылаться не на что.
  const drugie = new Set(fayly);
  for (const imya of fayly) {
    stranic++;
    const gde = path.relative(koren, path.join(papka, imya)).replace(/\\/g, '/');
    const html = fs.readFileSync(path.join(papka, imya), 'utf8');
    const est = html.includes('<div class="pl-razdely">');
    if (fayly.length === 1) {
      proverka(`${gde}: страница одна — блока «Ещё по курсу» нет`,
        !est, est ? 'есть' : 'нет');
      continue;
    }
    if (!est) {
      proverka(`${gde}: блок «Ещё по курсу» на месте`, false, 'нет блока');
      continue;
    }
    s_blokom++;
    // Плашки блока — от надписи «Ещё по курсу» и до конца страницы.
    const kusok = html.slice(html.indexOf('<div class="pl-razdely">'));
    const adresa = [...kusok.matchAll(/<a class="plitka[^"]*" href="([^"]+)"/g)]
      .map(m => bez_myagkih(m[1]));
    const imena_faylov = adresa.map(a =>
      decodeURIComponent(path.basename(a)).replace(/\\/g, '/'));
    const ozhidaem = [...drugie].filter(x => x !== imya);
    const netu = ozhidaem.filter(x => !imena_faylov.includes(x));
    const lishnie = imena_faylov.filter(x => !drugie.has(x));
    proverka(`${gde}: плашек ${ozhidaem.length} — все материалы предмета, кроме своего`,
      imena_faylov.length === ozhidaem.length && !netu.length && !lishnie.length,
      { plitok: imena_faylov.length, netu, lishnie });
    proverka(`${gde}: ни одна плашка не ведёт на саму эту страницу`,
      !imena_faylov.includes(imya), imena_faylov);
    proverka(`${gde}: повторов среди плашек нет`,
      new Set(imena_faylov).size === imena_faylov.length, imena_faylov);
    // Каждый адрес — существующий файл рядом со страницей.
    const bitye = adresa.filter(a =>
      !fs.existsSync(path.resolve(papka, decodeURIComponent(a))));
    proverka(`${gde}: все адреса ведут на существующие страницы`,
      bitye.length === 0, bitye);
  }
}

console.log(`\nстраниц просмотрено: ${stranic}, с блоком «Ещё по курсу»: ${s_blokom}`);
console.log(oshibki ? `ИТОГО: ${oshibki} ошибок` : 'ИТОГО: связь страниц сходится');
process.exit(oshibki ? 1 : 0);
