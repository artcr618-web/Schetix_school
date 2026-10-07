// Куда на самом деле ведёт адрес: код ответа, конечный адрес и первые
// слова страницы. Нужно там, где одного кода мало: 000 и 403 одинаково
// выглядят у живого сайта, у чужой заглушки и у сайта с истёкшим
// сертификатом, а для человека это разные вещи.
//
//   node Временные/проверка_адреса.js https://drops.com/ https://languagedrops.com/
const { chromium } = require('./плейрайт.js');

const adresa = process.argv.slice(2);
if (!adresa.length) {
  console.log('Укажите адреса: node Временные/проверка_адреса.js <адрес> [ещё адреса]');
  process.exit(1);
}

(async () => {
  const b = await chromium.launch();
  for (const u of adresa) {
    const p = await b.newPage();
    let stroka = '';
    try {
      const o = await p.goto(u, { waitUntil: 'commit', timeout: 25000 });
      await p.waitForTimeout(2500);
      const tekst = (await p.evaluate(() =>
        document.body ? document.body.innerText.slice(0, 120) : ''))
        .replace(/\s+/g, ' ').trim();
      const kod = o ? o.status() : '?';
      const kuda = p.url() !== u ? ' → уводит на ' + p.url() : '';
      stroka = `код ${kod}${kuda}\n     первые слова: ${JSON.stringify(tekst)}`;
    } catch (e) {
      // Ошибка сертификата — это беда страницы, а не сети: браузер
      // покажет человеку предупреждение и дальше не пустит.
      stroka = 'не открылось: ' + String(e).split('\n')[0].slice(0, 130);
    }
    console.log(u + '\n     ' + stroka);
    await p.close();
  }
  await b.close();
})();
