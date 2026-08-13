# Деплой Fusion Messenger (fusionmessenger.ru, без Docker)

## Требования

- Ubuntu/Debian с nginx и certbot
- Python 3.10+ и [uv](https://docs.astral.sh/uv/)
- Node.js 20+
- Домен с настроенными A-записями

## 1. DNS

A-запись: `fusionmessenger.ru` -> IP сервера (и при желании `www.fusionmessenger.ru`).
Отдельный поддомен для API не нужен — nginx проксирует `/api` на бэкенд того же домена.

## 2. Настройка .env

```bash
cp .env.example .env
nano .env
```

```env
DOMAIN=fusionmessenger.ru
ENVIRONMENT=production
FRONTEND_HOST=https://fusionmessenger.ru
BACKEND_CORS_ORIGINS=https://fusionmessenger.ru,http://fusionmessenger.ru
SECRET_KEY=ваш_секретный_ключ
FIRST_SUPERUSER=admin@fusionmessenger.ru
FIRST_SUPERUSER_PASSWORD=your_strong_password

# Путь к SQLite. Относительный путь считается от каталога backend/
SQLITE_DB_PATH=app.db
```

## 3. База данных

БД — это файл SQLite на сервере (по умолчанию `backend/app.db`). Он в `.gitignore`
и не хранится в репозитории, поэтому `git pull` / `./update.sh` его **не перезаписывают**.
Схема при старте только доращивается (`ensure_sqlite_schema_compatibility`), данные не удаляются.

Резервная копия перед обновлением:

```bash
cp backend/app.db backend/app.db.$(date +%F-%H%M).bak
```

## 4. Бэкенд (systemd)

`/etc/systemd/system/messenger-backend.service`:

```ini
[Unit]
Description=Fusion Messenger backend
After=network.target

[Service]
WorkingDirectory=/opt/messenger/backend
EnvironmentFile=/opt/messenger/.env
ExecStart=/usr/local/bin/uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
User=www-data

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now messenger-backend
```

## 5. Фронтенд и nginx

```bash
cd frontend && npm ci && npm run build   # результат в frontend/dist
sudo cp ../nginx-ssl.conf /etc/nginx/sites-available/fusionmessenger.ru
sudo ln -sf /etc/nginx/sites-available/fusionmessenger.ru /etc/nginx/sites-enabled/
sudo certbot --nginx -d fusionmessenger.ru -d www.fusionmessenger.ru
sudo nginx -t && sudo systemctl reload nginx
```

В `nginx-ssl.conf` статика раздаётся из `/opt/messenger/frontend/dist`, а `/api`, `/media`
и WebSocket (`/api/v1/ws`) проксируются на `127.0.0.1:8000`.

## 6. Обновление

```bash
./update.sh      # git pull + deploy.sh
# или
./deploy.sh      # uv sync + сборка фронта + restart messenger-backend + reload nginx
```

Имя systemd-юнита можно переопределить: `BACKEND_SERVICE=my-unit ./deploy.sh`.

## Доступные адреса

| Сервис | URL |
|--------|-----|
| Frontend | https://fusionmessenger.ru |
| API | https://fusionmessenger.ru/api/v1 |
| API Docs | https://fusionmessenger.ru/api/v1/docs |

## Логи

```bash
sudo journalctl -u messenger-backend -f
sudo tail -f /var/log/nginx/error.log
```

## Docker

Файлы `docker-compose*.yml` остались в репозитории от шаблона и для продакшена не используются.
