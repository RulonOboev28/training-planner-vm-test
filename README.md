# Деплой на VPS (VM test)

Репозиторий / ветка для **виртуальной машины**: только backend (`server/`) и общий код плана (`core/`).

## Быстрый старт на Ubuntu

```bash
cd /opt
git clone https://github.com/RulonOboev28/training-planner-vm-test.git training
cd training/server
cp .env.production.example .env
nano .env   # POSTGRES_PASSWORD, JWT_SECRET
docker compose -f docker-compose.prod.yml up -d --build
curl -s http://127.0.0.1/health
```

Подробнее: [server/DEPLOY.md](server/DEPLOY.md)

## Структура

| Путь | Назначение |
|------|------------|
| `server/` | FastAPI, статика `/web/`, Docker, nginx |
| `core/` | Модели и publish_pack (общие с конструктором) |

Базы данных в git **не хранятся** — на VM PostgreSQL в Docker (`pgdata` volume).

## Метка релиза

Сборки для VM помечайте тегом **`vm-test`** (или веткой `vm/test`).
