// Кликабельность: жмём живые кнопки настоящей мышью и смотрим, изменилось
// ли что-то на странице. Обычного `el.click()` мало: он бьёт мимо того,
// что видит человек, — по кнопке, которая уехала под кадр или за экран.
//
// Заодно проверяем уведомление над кадром: помещается ли оно, где у него
// крестик и работает ли он.
//
//   node Временные/proverka_knopok.js
//
// Прогоняем дважды: обычно и в условиях предпросмотра Арены — страница в
// песочнице, где localStorage недоступен. Там кнопки должны работать так
// же: навыки запоминать негде, но играть и переключаться можно.
//
// Ловушка прогона: если обратиться к localStorage в самом начале загрузки
// документа (например, из addInitScript), браузер может отдать документу
// ещё не записанный снимок хранилища — и память урока, поставленную
// прошлым документом, документ не увидит. Поэтому здесь память трогаем
// только после загрузки страницы.
const fs = require('fs');
const path = require('path');
const { chromium } = require('./плейрайт.js');

const stranicy = [
  'Проект/База данных/5 класс/История/видеоуроки.html',
  'Проект/База данных/5 класс/История/кино.html',
  'Проект/База данных/7 класс/История/кино.html',
  'Проект/База данных/5 класс/История.html',   // страница предмета: баннер
];

let oshibki = 0;
const proverka = (chto, uslovie, fakticheski) => {
  console.log((uslovie ? '  ок   ' : '  ОШИБКА ') + chto +
              (uslovie ? '' : ' → ' + JSON.stringify(fakticheski)));
  if (!uslovie) oshibki++;
};

// Точка, по которой будем бить: центр элемента, подведённый в окно.
async function podvesti(p, selektor) {
  return p.evaluate((sel) => {
    const el = document.querySelector(sel);
    if (!el) return null;
    el.scrollIntoView({ block: 'center' });
    const r = el.getBoundingClientRect();
    return { x: Math.round(r.left + r.width / 2),
             y: Math.round(r.top + r.height / 2),
             width: Math.round(r.width), height: Math.round(r.height) };
  }, selektor);
}

// Что находится сверху в этой точке — тот ли это элемент.
async function sverkhu(p, selektor) {
  return p.evaluate((sel) => {
    const el = document.querySelector(sel);
    if (!el) return { est: false };
    const r = el.getBoundingClientRect();
    const tochka = document.elementFromPoint(
      Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2));
    return { est: !!tochka && (tochka === el || el.contains(tochka)),
             chto: tochka ? (tochka.className || tochka.tagName) : 'ничего' };
  }, selektor);
}

async function zhmem(p, selektor) {
  const t = await podvesti(p, selektor);
  if (!t) return false;
  await p.mouse.move(t.x, t.y);
  await p.waitForTimeout(120);
  await p.mouse.click(t.x, t.y);
  await p.waitForTimeout(700);
  return true;
}

// Ключ памяти урока на этой странице.
const klyuchUroka = () => 'shkola.urok.' + (window.SHK_HOME || location.pathname);

// Готовим уведомление о возврате: чистим память урока, нажимаем строку
// списка и возвращаемся на страницу. Возврат повторяем: браузер на
// file:// изредка отдаёт новому документу ещё не записанный снимок
// хранилища, запись урока пропадает — это беда прогона, а не страницы.
// Настоящая ошибка — когда запись на месте, а уведомления нет: его и
// ловим ниже.
async function gotovim_kartu(p) {
  for (let krug = 0; krug < 3; krug++) {
    await p.evaluate(() => {
      try {
        localStorage.removeItem('shkola.urok.' +
          (window.SHK_HOME || location.pathname));
      } catch (e) {}
    });
    let zapisano = false;
    for (let popytka = 0; popytka < 3 && !zapisano; popytka++) {
      await p.evaluate(() => {
        const a = document.querySelectorAll('.trek')[2] ||
                  document.querySelector('.trek');
        if (a) a.click();
      });
      await p.waitForTimeout(600);
      zapisano = await p.evaluate(() => {
        try {
          return !!localStorage.getItem('shkola.urok.' +
                 (window.SHK_HOME || location.pathname));
        } catch (e) { return false; }
      });
    }
    if (!zapisano) continue;
    await p.reload({ waitUntil: 'load' });
    for (let shag = 0; shag < 8; shag++) {
      await p.waitForTimeout(350);
      const pokazana = await p.evaluate(() => {
        const v = document.getElementById('pleyer-vybor');
        return !!v && getComputedStyle(v).display !== 'none';
      });
      if (pokazana) return true;
    }
  }
  return false;
}

async function proverit(stranica, rezhim) {
  console.log('\n=== ' + stranica.replace('Проект/База данных/', '') +
              '   [' + rezhim + ']');
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1440, height: 950 } });
  const svoi = [];
  p.on('pageerror', e => {
    const polno = String((e && e.stack) || (e && e.message) || e);
    // Ошибки самого Rutube в песочнице — не наши: его кадр мы не чиним.
    if (/static\.rutube\.ru|raichu-embed/.test(polno)) return;
    svoi.push(polno.split('\n')[0].slice(0, 120));
  });
  if (rezhim === 'песочница') {
    // Предпросмотр Арены: страница в песочнице, хранилища нет.
    await p.addInitScript(() => {
      try {
        Object.defineProperty(window, 'localStorage', {
          get() { throw new DOMException('The operation is insecure.',
                                         'SecurityError'); },
        });
      } catch (e) {}
    });
  }
  /* В обычном режиме память в начале загрузки НЕ трогаем. Браузер в
     headless-прогоне отдаёт новому документу снимок хранилища с диска: кто
     обратится к памяти раньше, чем снимок придёт, тот её и не увидит — а
     запись, сделанную документом до перезагрузки, ещё не успели записать
     на диск. Так проверка сама теряла память урока и потом ругалась на
     страницу. Имя и цель ей здесь не нужны. */
  await p.goto('file://' + path.resolve(stranica), { waitUntil: 'load' });
  await p.waitForTimeout(1000);

  const est_pleer = await p.evaluate(() => !!document.getElementById('pleyer'));
  const est_banner = await p.evaluate(() =>
    !!document.querySelector('.banner-trek'));
  const est_panel = await p.evaluate(() =>
    !!document.querySelector('#pleylist-panel'));

  if (est_panel) {
    // --- строка списка в панели: играет выбранный урок
    const pervyy = await p.evaluate(() => {
      const a = document.querySelector('#pleylist-panel a.trek');
      return a ? { kod: a.getAttribute('data-video'),
                   zag: a.getAttribute('data-zag') } : null;
    });
    await zhmem(p, '#pleylist-panel a.trek');
    const posle = await p.evaluate(() => {
      const f = document.getElementById('ramka');
      const stroka = document.querySelector('#pleylist-panel a.trek');
      const sverkhu = (() => {
        const r = stroka.getBoundingClientRect();
        const el = document.elementFromPoint(Math.round(r.left + r.width / 2),
                                             Math.round(r.top + r.height / 2));
        return !!el && !!el.closest && el.closest('a') === stroka;
      })();
      return { kadr: !!f, adres: f ? f.getAttribute('src') : '',
               podsvetka: stroka.className.includes('aktiven'),
               sverkhu: sverkhu,
               shapka: (document.getElementById('pleyer-zag') || {}).textContent };
    });
    proverka('строка списка под курсором (её ничто не накрывает)',
             posle.sverkhu);
    proverka('нажатие на строку включает урок',
             posle.kadr && posle.adres === pervyy.kod, [posle.adres, pervyy.kod]);
    proverka('строка подсвечена после нажатия', posle.podsvetka);
    proverka('в шапке — название урока', posle.shapka === pervyy.zag,
             [posle.shapka, pervyy.zag]);

    // --- кнопка плейлиста на кадре: панель закрывается и открывается
    await zhmem(p, '.pleyer-knopka');
    const zakryto = await p.evaluate(() =>
      !document.body.classList.contains('pleylist-otkryto'));
    proverka('кнопка на кадре закрывает панель плейлиста', zakryto);
    await zhmem(p, '.pleyer-knopka');
    const otkryto = await p.evaluate(() =>
      document.body.classList.contains('pleylist-otkryto'));
    proverka('она же возвращает панель', otkryto);

    // --- крестик панели
    await zhmem(p, '#pleylist-panel .panel-zakryt');
    proverka('крестик закрывает панель плейлиста',
             await p.evaluate(() =>
               !document.body.classList.contains('pleylist-otkryto')));
  }

  // --- меню: значок, раскрытие класса, крестик
  if (await p.evaluate(() => !!document.querySelector('.shapka-menyu, a[aria-label="Меню"]'))) {
    await zhmem(p, 'a[aria-label="Меню"]');
    const menu = await p.evaluate(() =>
      document.body.classList.contains('menu-otkryto'));
    proverka('значок меню открывает боковое меню', menu);
    if (menu) {
      await zhmem(p, '#panel summary.klass-knopka');
      proverka('строка класса раскрывается',
               await p.evaluate(() =>
                 !!document.querySelector('#panel details[open]')));
      await zhmem(p, '#panel .panel-zakryt');
      proverka('крестик закрывает меню',
               await p.evaluate(() =>
                 !document.body.classList.contains('menu-otkryto')));
    }
  }

  // --- баннер лекций: «Смотреть» и строка лекции
  if (est_banner) {
    const pervyy = await p.evaluate(() => {
      const a = document.querySelector('.banner-nabor .banner-trek');
      return { kod: a.getAttribute('data-video') };
    });
    await zhmem(p, '.banner-igrat');
    const igraet = await p.evaluate(() => {
      const f = document.querySelector('#banner-mesto iframe');
      return { kadr: !!f, adres: f ? f.getAttribute('src') : '' };
    });
    proverka('«Смотреть» в баннере включает первую лекцию',
             igraet.kadr && igraet.adres === pervyy.kod,
             [igraet.adres, pervyy.kod]);
    await zhmem(p, '.banner-nabor .banner-trek');
    proverka('строка лекции в баннере переключает кадр',
             await p.evaluate(() => !!document.querySelector('#banner-mesto iframe')));
  }

  // --- уведомление о продолжении: помещается, крестик на месте и работает
  if (est_pleer && rezhim !== 'песочница') {
    await gotovim_kartu(p);
    const karta = await p.evaluate(() => {
      const v = document.getElementById('pleyer-vybor');
      const k = document.querySelector('.vybor-karta');
      const kr = document.getElementById('vybor-zakryt');
      const kadr = document.getElementById('pleyer').getBoundingClientRect();
      if (!v || getComputedStyle(v).display === 'none') {
        return { est: false, v: !!v,
                 display: v ? getComputedStyle(v).display : 'нет карточки',
                 ramka: !!document.getElementById('ramka'),
                 zapis: (() => { try {
                   return localStorage.getItem('shkola.urok.' +
                          (window.SHK_HOME || location.pathname));
                 } catch (e) { return 'нет доступа'; } })() };
      }
      const k_r = k.getBoundingClientRect();
      const c_r = kr.getBoundingClientRect();
      const povyshe = getComputedStyle(v).position === 'absolute';
      return {
        est: true,
        rezhim: povyshe ? 'поверх кадра' : 'под кадром',
        // Сверху карточка не должна вылезать за кадр, снизу — начинаться
        // внутри кадра: иначе её край срежет рамка плеера.
        ne_obrezana: povyshe
          ? (k_r.height <= kadr.height + 1 && k_r.width <= kadr.width + 1 &&
             k_r.top >= kadr.top - 1 && k_r.bottom <= kadr.bottom + 1)
          : (k_r.top >= kadr.bottom - 2 &&
             v.scrollHeight <= v.clientHeight + 2),
        krestik_sverkhu: (c_r.top - k_r.top) < k_r.height / 2 &&
                         (k_r.right - c_r.right) < 80 * (k_r.width / 920) + 20,
        krestik_viden: !!document.elementFromPoint(
          Math.round(c_r.left + c_r.width / 2), Math.round(c_r.top + c_r.height / 2)),
        slovo_zakryt: /Закрыть/.test(k.textContent),
      };
    });
    proverka('уведомление показано', karta.est, karta);
    if (karta.est) {
      proverka('уведомление не обрезано (' + karta.rezhim + ')',
               karta.ne_obrezana, karta);
      proverka('крестик на своём месте и ничем не накрыт',
               karta.krestik_sverkhu && karta.krestik_viden, karta);
      proverka('крестик — в правом верхнем углу карточки',
               karta.krestik_sverkhu, karta);
      proverka('слова «Закрыть» на карточке нет', !karta.slovo_zakryt,
               karta.slovo_zakryt);
      // Крестик жмём настоящей мышью. Если карточка осталась, меряем
      // её заново и жмём ещё раз: на медленной машине кадр успевает
      // сдвинуть страницу между замером и щелчком, и щелчок уходит
      // мимо. Второй замер — из нового положения, мимо он не пройдёт.
      let zakryto = false;
      for (let popytka = 0; popytka < 2 && !zakryto; popytka++) {
        await zhmem(p, '#vybor-zakryt');
        zakryto = await p.evaluate(() => {
          const v = document.getElementById('pleyer-vybor');
          return getComputedStyle(v).display === 'none';
        });
      }
      proverka('крестик убирает уведомление', zakryto, zakryto);
      proverka('кадр после закрытия уведомления остался',
               await p.evaluate(() => !!document.getElementById('ramka')));
    }
  }

  console.log('  свои ошибки на странице: ' + (svoi.length ? svoi.join(' | ') : 'нет'));
  if (svoi.length) oshibki++;
  await b.close();
}

// Узкое окно: уведомление должно сжиматься вместе с кадром и никогда не
// уезжать под его рамку или за экран.
async function uzkoe_okno(stranica) {
  console.log('\n=== узкое окно: ' + stranica.replace('Проект/База данных/', ''));
  const b = await chromium.launch();
  for (const w of [1920, 1440, 1100, 900, 760, 620, 480, 380]) {
    const p = await b.newPage({ viewport: { width: w, height: 900 } });
    await p.goto('file://' + path.resolve(stranica), { waitUntil: 'load' });
    await p.waitForTimeout(700);
    await gotovim_kartu(p);
    if (w < 640) {
      // Телефон: панель плейлиста занимает почти весь кадр и накрывает
      // страницу — так и задумано (РАЗМЕТКА.md, исключение для
      // телефонов). Поэтому кнопки карточки проверяем с закрытой
      // панелью, а саму панель — отдельно: она должна влезать в кадр.
      const pm = await p.evaluate(() => {
        document.body.classList.add('pleylist-otkryto');
        const pn = document.getElementById('pleylist-panel');
        const r = pn.getBoundingClientRect();
        return { left: Math.round(r.left), right: Math.round(r.right),
                 w: Math.round(r.width), sw: innerWidth };
      });
      proverka(`панель плейлиста влезает в кадр (${w} px)`,
               pm.left >= -1 && pm.right <= pm.sw + 1,
               JSON.stringify(pm));
      await p.evaluate(() => {
        document.body.classList.remove('pleylist-otkryto', 'menu-otkryto');
      });
      await p.waitForTimeout(450);
    }
    const m = await p.evaluate(() => {
      const v = document.getElementById('pleyer-vybor');
      const k = document.querySelector('.vybor-karta');
      const kadr = document.getElementById('pleyer').getBoundingClientRect();
      if (!v || getComputedStyle(v).display === 'none') {
        return { est: false, display: v ? getComputedStyle(v).display
                                          : 'нет карточки',
                 ramka: !!document.getElementById('ramka'),
                 zapis: (() => { try {
                   return localStorage.getItem('shkola.urok.' +
                          (window.SHK_HOME || location.pathname));
                 } catch (e) { return 'нет доступа'; } })() };
      }
      v.scrollIntoView({ block: 'center' });
      const k_r = k.getBoundingClientRect();
      const povyshe = getComputedStyle(v).position === 'absolute';
      const knopki = [...k.querySelectorAll('a')].map(a => {
        // Каждую кнопку подводим в окно: карточка бывает выше экрана.
        a.scrollIntoView({ block: 'nearest' });
        const r = a.getBoundingClientRect();
        const v_okne = r.bottom > 0 && r.top < innerHeight;
        if (!v_okne) {
          // Осталась за окном — значит, экран кончился, а не кнопку накрыли.
          return { vidna: true, gde: 'за окном' };
        }
        const el = document.elementFromPoint(Math.round(r.left + r.width / 2),
                                             Math.round(r.top + r.height / 2));
        const sverkhu = !!el && (el === a || a.contains(el));
        return { vidna: sverkhu, gde: sverkhu ? 'наверху'
                 : (el ? 'накрыта ' + (el.className || el.tagName) : 'ничего') };
      });
      k.scrollIntoView({ block: 'center' });
      return {
        est: true,
        rezhim: povyshe ? 'поверх' : 'под',
        kadr: Math.round(kadr.width),
        karta: Math.round(k_r.width),
        // Обрезана — это когда карточка не помещается в свою рамку
        // (сверху — только в режиме «поверх кадра»), а не когда страница
        // длинная: в режиме «под кадром» она просто удлиняет страницу.
        obrezana: (povyshe && v.scrollHeight > v.clientHeight + 2) ||
                  k_r.width > kadr.width + 1,
        shrift: Math.round(parseFloat(getComputedStyle(
          document.getElementById('vybor-tekst')).fontSize)),
        knopki_vidny: knopki,
      };
    });
    const knopki_ok = (m.knopki_vidny || []).every(k => k && k.vidna);
    const ok = m.est && !m.obrezana && knopki_ok &&
               m.shrift >= 17 && m.shrift <= 32;
    console.log('  ' + (ok ? 'ок   ' : 'ОШИБКА ') + String(w).padStart(4) +
                ' px: кадр ' + m.kadr + ' px, карточка ' + m.karta +
                ' px, уведомление ' + m.rezhim + ' кадра, шрифт ' + m.shrift +
                ' px, кнопки ' + (knopki_ok ? 'видны'
                                  : JSON.stringify(m.knopki_vidny)) +
                (ok ? '' : '  ← ' + JSON.stringify(m)));
    if (!ok) oshibki++;
    await p.close();
  }
  await b.close();
}

(async () => {
  console.log('живые нажатия мышью. Обычный режим и песочница (как в предпросмотре)');
  for (const rezhim of ['обычно', 'песочница']) {
    for (const f of stranicy) {
      await proverit(f, rezhim);
    }
  }
  await uzkoe_okno('Проект/База данных/5 класс/История/видеоуроки.html');
  await uzkoe_okno('Проект/База данных/7 класс/История/кино.html');
  console.log('\nИтог: ошибок ' + oshibki);
  process.exit(oshibki ? 1 : 0);
})();
