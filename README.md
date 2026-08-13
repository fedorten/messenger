# Fusion Messenger

Веб-мессенджер с поддержкой текстовых сообщений, медиа-файлов и real-time обновлений через WebSocket.

## Возможности

- **Чаты**: Приватные и групповые беседы
- **Сообщения**: Текстовые с поддержкой медиа
- **Real-time**: Мгновенная доставка через WebSocket
- **Медиа**: Изображения, аудио, документы (до 10 МБ)
- **Хранилище**: Автоматическая очистка при лимите 1 ГБ
- **Аутентификация**: JWT токены сроком на 24 часа

## Технологии

| Компонент | Стек |
|----------|------|
| Backend | FastAPI, SQLModel, SQLite, JWT |
| Frontend | Vue 3, Vite, Axios |
| Proxy | nginx + certbot (Let's Encrypt) |
| Запуск на проде | uvicorn под systemd, без Docker |

## Структура проекта

```
messenger/
├── backend/
│   ├── app/
│   │   ├── api/routes/      # API эндпоинты
│   │   ├── core/          # Конфигурация, БД
│   │   ├── main.py       # Точка входа
│   │   └── models.py     # Модели данных
│   ├── pyproject.toml    # Зависимости Python
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── views/        # Vue компоненты
│   │   ├── services/     # API клиент, WebSocket
│   │   └── style.css    # Стили
│   ├── package.json      # Зависимости Node.js
│   └── Dockerfile
├── docker-compose.yml    # Конфигурация Docker
└── .env                # Переменные окружения
```

## Быстрый старт

```bash
cp .env.example .env
nano .env  # Настройте DOMAIN и SECRET_KEY
```

### Локальная разработка

**Backend:**
```bash
cd backend
uv venv .venv
source .venv/bin/activate
uv sync
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Конфигурация .env

```env
# Домен
DOMAIN=fusionmessenger.ru

# Окружение
ENVIRONMENT=production

# Frontend URL
FRONTEND_HOST=https://fusionmessenger.ru

# CORS
BACKEND_CORS_ORIGINS=https://fusionmessenger.ru,http://fusionmessenger.ru

# Секретный ключ (сгенерируйте: python -c "import secrets; print(secrets.token_urlsafe(32))")
SECRET_KEY=your_secret_key

# Первый суперпользователь
FIRST_SUPERUSER=admin@fusionmessenger.ru
FIRST_SUPERUSER_PASSWORD=your_strong_password

# SQLite путь (относительный путь считается от каталога backend/)
SQLITE_DB_PATH=app.db
```

## API Endpoints

### Аутентификация

| Метод | Путь | Описание |
|------|------|----------|
| POST | /api/v1/login/access-token | Вход (JWT токен) |
| POST | /api/v1/users/signup | Регистрация |
| GET | /api/v1/users/me | Текущий пользователь |
| PATCH | /api/v1/users/me | Обновить профиль |
| DELETE | /api/v1/users/me | Удалить аккаунт |

### Чаты

| Метод | Путь | Описание |
|------|------|----------|
| GET | /api/v1/chats/ | Список чатов |
| GET | /api/v1/chats/{id} | Получить чат |
| POST | /api/v1/chats/private/{user_id} | Создать приватный чат |
| POST | /api/v1/chats/group | Создать групповой чат |
| POST | /api/v1/chats/{id}/members | Добавить участников |
| POST | /api/v1/chats/{id}/read | Отметить как прочитанное |
| GET | /api/v1/chats/{id}/messages | Сообщения чата |

### Сообщения

| Метод | Путь | Описание |
|------|------|----------|
| POST | /api/v1/messages/{chat_id} | Отправить сообщение |
| PUT | /api/v1/messages/{id} | Редактировать |
| DELETE | /api/v1/messages/{id} | Удалить |

### Медиа

| Метод | Путь | Описание |
|------|------|----------|
| POST | /api/v1/media/upload | Загрузить файл |
| GET | /api/v1/media/files/{filename} | Получить файл |

### WebSocket

```
WS /api/v1/ws/{chat_id}?token={jwt_token}
```

### Пользователи

| Метод | Путь | Описание |
|------|------|----------|
| GET | /api/v1/users/search?q={query} | Поиск пользователей |

### Утилиты

| Метод | Путь | Описание |
|------|------|----------|
| GET | /api/v1/utils/health-check/ | Health check |

## Лимиты

- **Файл**: 10 МБ
- **Хранилище**: 1 ГБ (автоочистка)
- **Сообщение**: 4096 символов
- **Токен**: 24 часа
- **Rate limit**: 5 попыток входа/мин

## Безопасность

- Пароли: Bcrypt хеширование
- Аутентификация: JWT (HS256)
- Защита: Path traversal, SQL injection, XSS
- Валидация: Pydantic модели
- Ограничения: Rate limiting, размеры файлов

## Деплой

Прод крутится без Docker: uvicorn под systemd + nginx со статикой Vite.
Подробная инструкция — в [DEPLOY.md](DEPLOY.md).

### Требования

- nginx + certbot
- Python 3.10+, uv
- Node.js 20+
- Домен с A-записью на сервер

### DNS настройка

```
A запись: fusionmessenger.ru -> IP сервера
```

### Запуск и обновление

```bash
./deploy.sh   # зависимости, сборка фронта, restart messenger-backend, reload nginx
./update.sh   # git pull + deploy.sh
```

База (`backend/app.db`) и загруженные файлы лежат только на сервере и в git не попадают,
поэтому обновление кода их не перезаписывает.

## Управление

```bash
sudo systemctl restart messenger-backend
sudo journalctl -u messenger-backend -f
sudo nginx -t && sudo systemctl reload nginx
```

## Доступ после запуска

| Сервис | URL |
|--------|-----|
| Frontend | https://fusionmessenger.ru |
| API | https://fusionmessenger.ru/api/v1 |
| API Docs | https://fusionmessenger.ru/api/v1/docs |

## Лицензия

MIT
