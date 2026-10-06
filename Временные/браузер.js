// Настоящий браузер: открывает страницу пакета, меряет и снимает.
//
//   node Временные/браузер.js "<страница.html>" [до/после]
//
// Нужен там, где стенд бессилен: прокрутка, приклеенные шапки, отступы,
// как оно выглядит на самом деле. Снимки кладёт в Временные/снимки/.
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

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

  // 2. Под кадром: названия плейлистов и их цвет
  const pod = await stranica.evaluate(() => {
    const imena = [...document.querySelectorAll('.pl-vse .pl-imya')];
    const g = document.querySelector('.pl-vse .trek-gruppa');
    return {
      skolko: imena.length,
      pervoe: imena[0] && getComputedStyle(imena[0]).color,
      pervaya_podlozhka: imena[0] && getComputedStyle(imena[0]).backgroundColor,
      vtoroe: imena[1] && getComputedStyle(imena[1]).color,
      zagolovok_gruppy: g && getComputedStyle(g).color,
      otstup: getComputedStyle(document.querySelector('.pl-vse')).paddingLeft,
    };
  });
  console.log('=== плейлисты под кадром');
  console.log('   названий:', pod.skolko, '| цвет первого:', pod.pervoe,
              '| подложка:', pod.pervaya_podlozhka, '| второго:', pod.vtoroe);
  console.log('   заголовок главы:', pod.zagolovok_gruppy, '| отступ слева:', pod.otstup);
  await stranica.screenshot({ path: `${kuda}/${imya}-под-кадром.png`, fullPage: false });

  await brauzer.close();
})();
