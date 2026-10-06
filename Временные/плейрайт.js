// Откуда проверкам брать playwright.
//
// Сам пакет живёт в «Инструменты/внешнее/nodejs» — инструменты не
// разбрасываются по корню проекта. Здесь только дорога к нему, одна на
// все проверки: путь считается от этого файла, поэтому работает и на
// другой машине, и после переустановки пакета.
//
// Установка (один раз):  npm --prefix "Инструменты/внешнее/nodejs" install
// Браузер для проверок:  npx --prefix "Инструменты/внешнее/nodejs" playwright install --with-deps chromium
const path = require('path');
module.exports = require(path.join(__dirname, '..', 'Инструменты', 'внешнее',
                                   'nodejs', 'node_modules', 'playwright'));
