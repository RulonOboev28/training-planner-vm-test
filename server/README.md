# Training Planner API (roadmap, пункт 5)

Backend для сайта спортсmenов: отдельно от PyQt-конструктора.

## Быстрый старт (SQLite, без Docker)

```powershell
cd server
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- Документация: http://127.0.0.1:8000/docs  
- Проверка: http://127.0.0.1:8000/health  

## PostgreSQL (Docker)

```powershell
cd server
docker compose up -d
copy .env.example .env
# отредактируйте JWT_SECRET в .env
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Тесты

```powershell
cd server
pip install -r requirements.txt
pytest tests -q
```

## Основные эндпоинты

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/health` | Жив ли сервер |
| POST | `/auth/coach/register` | Регистрация тренера |
| POST | `/auth/coach/login` | JWT для тренера |
| GET/POST | `/athletes` | Список / создание спортсmena (JWT) |
| GET/PATCH/DELETE | `/athletes/{id}` | Карточка спортсmena |
| GET/POST | `/athletes/{id}/logs` | Журнал тренировок (скелет) |
| POST | `/coach/plan/publish` | Импорт JSON из конструктора (JWT) |
| GET | `/coach/plan/latest` | Последняя публикация + спортсmenы |
| GET | `/coach/plan/latest/athletes/{plan_athlete_id}/view` | План для id из `.tplan` |
| POST | `/auth/athlete/login` | JWT спортсmena |
| GET | `/athlete/plan/today` | Тренировки на сегодня |
| GET | `/athlete/plan/week` | Тренировки на текущую неделю (пн–вс) |
| POST/GET | `/athlete/log` | Дневник спортсmena (upsert по дате+упражнению) |
| GET | `/athletes/{id}/logs?from=&to=` | Журнал для тренера |

### Сайт на ПК (пункты 9–10, черновик)

После запуска uvicorn откройте **http://127.0.0.1:8000/web/** — вход спортсmena и «Сегодня» с галочками выполнения.

Цепочка локально: опубликовать план (Swagger) → войти на `/web/` → отметить упражнения.

**Деплой на Reg.ru** — после проверки на ПК (отдельный этап: Docker, nginx, HTTPS).

### Импорт из конструктора (пункт 6)

1. В десктопе: **Файл → Экспорт пакета для сайта (JSON)** → `publish_pack.json`.
2. В Swagger: **Authorize** → JWT тренера → **POST `/coach/plan/publish`** → вставить содержимое JSON.
3. В ответе — `new_athlete_credentials` для **новых** logins (временный пароль для входа на сайте, шаг 7).

Если после обновления с шага 5 ошибка БД про колонку — удалите `training_dev.db` и перезапустите API.
