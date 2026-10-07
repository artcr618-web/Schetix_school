// Проверка, что оформление подключено файлом и правда применилось.
// Смотреть надо вычисленные стили, а не ссылку: ссылка может быть,
// а файл — не найтись, и страница молча станет голым текстом.
//
// Запуск: bash Инструменты/с_плейрайтом.sh node Временные/proverka_oformleniya.js
const { chromium } = require('/home/user/Временные/плейрайт.js');
const path = require('path');
const fs = require('fs');

const stranicy = [
  ['вход (корень)',    'Проект/Начать учиться.html'],
  ['класс',            'Проект/База данных/5 класс.html'],
  ['предмет',          'Проект/База данных/5 класс/История.html'],
  ['материалы',        'Проект/База данных/5 класс/История/видеоуроки.html'],
  ['кино',             'Проект/База данных/5 класс/История/кино.html'],
  ['тренажёры 7Англ',  'Проект/База данных/7 класс/Английский/тренажёры.html'],
  ['список ненайденного', 'Проект/Что не нашлось.html'],
];

(async () => {
  const b = await chromium.launch();
  let oshibki = 0;
  for (const [imya, f] of stranicy) {
    // 1) в самой странице не должно быть ни одного <style>
    const syroy = fs.readFileSync(f, 'utf8');
    const est_stil = /<style[\s>]/.test(syroy);
    // 2) ссылка на файл оформления должна быть
    const ssylka = syroy.match(/<link[^>]+href="([^"]+\.css)"/);
    const put_css = ssylka &&
      path.resolve(path.dirname(f), ssylka[1]);
    const fayl_est = put_css && fs.existsSync(put_css);
    // 3) оформление должно быть применено (проверяем в браузере)
    const p = await b.newPage({ viewport: { width: 1440, height: 900 } });
    await p.goto('file://' + path.resolve(f), { waitUntil: 'load' });
    await p.waitForTimeout(250);
    const m = await p.evaluate(() => {
      const telo = getComputedStyle(document.body);
      const listov = [...document.styleSheets];
      return {
        fon: telo.backgroundColor,
        shrift: telo.fontFamily.slice(0, 22),
        tablic: listov.length,
        pravila: listov.reduce((s, l) => {
          try { return s + l.cssRules.length; } catch (e) { return s - 0; }
        }, 0),
      };
    });
    const holodnyy_fon = m.fon === 'rgb(14, 17, 22)' || m.fon === 'rgb(17, 20, 26)';
    const ok = !est_stil && !!ssylka && fayl_est && m.tablic >= 1 && holodnyy_fon;
    console.log((ok ? '  ок   ' : '  ОШИБКА ') + imya.padEnd(20) +
      ' style в html: ' + (est_stil ? 'есть (!)' : 'нет') +
      ', файл: ' + (fayl_est ? 'найден' : 'НЕТ') +
      ', таблиц: ' + m.tablic + ', фон: ' + m.fon +
      (ok ? '' : '   ← ' + JSON.stringify(m)));
    if (!ok) oshibki++;
    await p.close();
  }
  await b.close();
  console.log('\nОформление: вердикт — ' +
    (oshibki ? 'плохо, ошибок ' + oshibki : 'хорошо, везде файл подключён и применён'));
  process.exit(oshibki ? 1 : 0);
})();
