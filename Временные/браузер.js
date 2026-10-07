// Настоящий браузер: открывает страницу пакета, меряет и снимает.
//
//   node Временные/браузер.js "<страница.html>" [до/после]
//
// Нужен там, где стенд бессилен: прокрутка, приклеенные шапки, отступы,
// как оно выглядит на самом деле. Снимки кладёт в Временные/снимки/.
const fs = require('fs');
const path = require('path');
const { chromium } = require('./плейрайт.js');

const put = process.argv[2] || 'Проект/База данных/5 класс/География/видеоуроки.html';
const imya = path.basename(path.dirname(put)) + '-' + path.basename(put, '.html');
const kuda = 'Временные/снимки';
fs.mkdirSync(kuda, { recursive: true });

(async () => {
  const brauzer = await chromium.launch();
  const stranica = await brauzer.newPage({ viewport: { width: 1920, height: 1080 } });
  await stranica.goto('file://' + path.resolve(put));
  await stranica.waitForTimeout(600);

  // 1. Панель плейлиста: шапка на месте и при прокрутке списка?
  const doProkrutki = await stranica.evaluate(() => {
    const shap = document.querySelector('#pleylist-panel .panel-verh');
    const telo = document.querySelector('#pleylist-panel .panel-telo');
    const pervyy = document.querySelector('#pleylist-panel .trek');
    if (!shap || !telo || !pervyy) return null;
    return {
      shap: shap.getBoundingClientRect().top,
      telo: telo.getBoundingClientRect().top,
      pervyy: pervyy.getBoundingClientRect().top,
      list: document.querySelector('#pleylist-panel .pleylist'),
      otstup: document.querySelector('#pleylist-panel .pleylist')
        ? getComputedStyle(document.querySelector('#pleylist-panel .pleylist')).marginLeft : '',
    };
  });
  await stranica.screenshot({ path: `${kuda}/${imya}-панель.png`,
                              clip: { x: 1920 - 460, y: 0, width: 460, height: 700 } });

  const posle = await stranica.evaluate(() => {
    const telo = document.querySelector('#pleylist-panel .panel-telo');
    telo.scrollTop = 600;
    const shap = document.querySelector('#pleylist-panel .panel-verh');
    return { shap: shap.getBoundingClientRect().top, teloTop: telo.getBoundingClientRect().top,
             prokrutka: telo.scrollTop };
  });
  await stranica.waitForTimeout(200);
  await stranica.screenshot({ path: `${kuda}/${imya}-панель-прокрутка.png`,
                              clip: { x: 1920 - 460, y: 0, width: 460, height: 700 } });

  console.log('=== панель плейлиста');
  if (doProkrutki) {
    console.log('   шапка сверху:', Math.round(doProkrutki.shap));
    console.log('   начало списка:', Math.round(doProkrutki.telo));
    console.log('   первый пункт :', Math.round(doProkrutki.pervyy));
    console.log('   воздух между линией шапки и первым пунктом:',
                Math.round(doProkrutki.pervyy - doProkrutki.telo));
    console.log('   отступ списка слева:', doProkrutki.otstup);
  }
  console.log('   шапка после прокрутки:', Math.round(posle.shap), '(прокручено', posle.prokrutka, 'px)');
  console.log('   шапка уехала:', Math.abs(posle.shap - doProkrutki.shap) > 2 ? 'ДА — ЭТО ОШИБКА' : 'нет, стоит на месте');

  // 2. Под кадром: список плейлистов (уроков там больше нет)
  const pod = await stranica.evaluate(() => {
    const stroki = [...document.querySelectorAll('.pl-vse a.pl-plitka')];
    const urokev = document.querySelectorAll('.pl-vse a.trek').length;
    const otkr = document.querySelector('.pl-vse a.pl-plitka.tekushchiy');
    // «в покое» берём НЕ отмеченную строку: у играющей отметка по замыслу
    const pokoy = document.querySelector('.pl-vse a.pl-plitka:not(.tekushchiy)') || stroki[0];
    return {
      skolko: stroki.length, urokev: urokev,
      pervyy_tekst: pokoy && pokoy.textContent.trim(),
      fon: pokoy && getComputedStyle(pokoy).backgroundColor,
      otkr_fon: otkr && getComputedStyle(otkr).backgroundColor,
      otkr_polosa: otkr && (getComputedStyle(otkr).borderLeftWidth + ' ' +
                            getComputedStyle(otkr).borderLeftColor),
    };
  });
  console.log('=== плейлисты под кадром');
  console.log('   строк:', pod.skolko, '| уроков в блоке:', pod.urokev,
              '| первый неотмеченный:', pod.pervyy_tekst);
  console.log('   в покое:', pod.fon, '| открытый:', pod.otkr_fon,
              pod.otkr_polosa);
  await stranica.screenshot({ path: `${kuda}/${imya}-под-кадром.png`, fullPage: false });

  await brauzer.close();
})();
