#!/bin/bash

# Деплой fusionmessenger.ru без Docker (systemd + nginx)
# Использование: ./deploy.sh
#
# Скрипт НЕ трогает базу данных: файл SQLite (по умолчанию backend/app.db)
# и каталог backend/media остаются такими, какие есть на сервере.

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

if [ ! -f .env ]; then
    echo -e "${RED}❌ .env не найден — создайте его из .env.example${NC}"
    exit 1
fi

set -a
source .env
set +a

export DOMAIN=${DOMAIN:-fusionmessenger.ru}
BACKEND_SERVICE=${BACKEND_SERVICE:-messenger-backend}

echo -e "${GREEN}✓ Окружение загружено${NC}"
echo "  DOMAIN: $DOMAIN"
echo "  БД: ${SQLITE_DB_PATH:-backend/app.db} (не перезаписывается)"

echo -e "${YELLOW}📦 Зависимости бэкенда...${NC}"
(cd backend && uv sync --frozen)

echo -e "${YELLOW}📦 Сборка фронтенда...${NC}"
(cd frontend && npm ci && npm run build)

if systemctl list-unit-files "${BACKEND_SERVICE}.service" >/dev/null 2>&1 &&
    systemctl cat "${BACKEND_SERVICE}" >/dev/null 2>&1; then
    echo -e "${YELLOW}🔄 Перезапуск ${BACKEND_SERVICE}...${NC}"
    sudo systemctl restart "${BACKEND_SERVICE}"
else
    echo -e "${YELLOW}ℹ️  systemd-юнит ${BACKEND_SERVICE} не найден — перезапустите бэкенд вручную${NC}"
    echo "   (или задайте BACKEND_SERVICE=имя_юнита ./deploy.sh)"
fi

if command -v nginx >/dev/null 2>&1; then
    echo -e "${YELLOW}🔄 Перезагрузка nginx...${NC}"
    sudo nginx -t && sudo systemctl reload nginx
fi

echo -e "${GREEN}✅ Деплой завершён: https://${DOMAIN}${NC}"
