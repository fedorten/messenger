#!/bin/bash

# Быстрое обновление: подтянуть код и переразвернуть (без Docker)
# Использование: ./update.sh

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "🔄 Обновление..."

if [ ! -f "deploy.sh" ]; then
    echo "❌ Запустите скрипт из корня проекта (нет deploy.sh)"
    exit 1
fi

# База данных и загруженные файлы живут вне git (backend/app.db в .gitignore),
# поэтому git pull их не перезаписывает.
if [ -d ".git" ]; then
    read -p "Подтянуть изменения из Git? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}📥 git pull...${NC}"
        git pull
    fi
fi

echo -e "${YELLOW}🚀 Переразвёртывание...${NC}"
./deploy.sh

echo -e "${GREEN}✅ Готово${NC}"
