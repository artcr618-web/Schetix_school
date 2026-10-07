#!/bin/bash
# Ставит playwright и chromium для проверок со страницами.
#
#   bash Инструменты/поставить_плейрайт.sh
#
# Зачем отдельный файл: сторонние пакеты в песочнице не сохраняются —
# после каждого перезапуска среды браузер приходится ставить заново.
# Пакет живёт в «Инструменты/внешнее/nodejs» (в корне проекта ничего
# служебного не лежит, см. §15 правил), а скрипты проверок берут его
# через «Временные/плейрайт.js».
set -e
cd "$(dirname "$0")/.."

echo '1) пакет playwright'
npm --prefix "Инструменты/внешнее/nodejs" install --no-audit --no-fund >/dev/null

echo '2) браузер chromium'
npx --prefix "Инструменты/внешнее/nodejs" playwright install chromium >/dev/null

echo '3) системные библиотеки'
npx --prefix "Инструменты/внешнее/nodejs" playwright install-deps chromium >/dev/null

node -e "require('./Временные/плейрайт.js'); console.log('готово: playwright на месте')"
