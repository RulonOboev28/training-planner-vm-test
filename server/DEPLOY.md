# Деплой на Reg.cloud (Ubuntu 20.04)

Сервер: **HP C2-M2-D40**, регион **spb1**, IP **публичный** (из вкладки «Сеть»).

## 1. Первый вход

1. В Reg.cloud: **⋮ → Сбросить пароль** (если пароль root не сохранили) или используйте пароль из письма.
2. На Windows (PowerShell):

```powershell
ssh root@ВАШ_IP
```

При первом входе подтвердите fingerprint (`yes`).

Опционально: в панели Reg.cloud добавьте **SSH-ключ** и отключите вход по паролю позже.

## 2. Подготовка сервера (один раз)

На сервере под `root`:

```bash
apt update && apt upgrade -y
apt install -y git docker.io docker-compose-plugin
systemctl enable --now docker
```

Firewall (если `ufw` установлен):

```bash
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
```

## 3. Код на сервер

**Вариант A — git** (если репозиторий на GitHub):

```bash
cd /opt
git clone https://github.com/RulonOboev28/training-planner-vm-test.git training
cd training/server
```

**Вариант B — архив с ПК** (если git приватный):

На ПК из корня проекта:

```powershell
git archive -o training_server.zip HEAD server core
```

Загрузить на сервер через WinSCP/FileZilla в `/opt/training/`, распаковать.

## 4. Настройка окружения

```bash
cd /opt/training/server
cp .env.production.example .env
nano .env
```

Задайте длинные случайные `POSTGRES_PASSWORD` и `JWT_SECRET`.

## 5. Запуск

```bash
cd /opt/training/server
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml ps
```

Проверка:

- `http://ВАШ_IP/health` → `{"status":"ok"}`
- `http://ВАШ_IP/web/` — вход спортсmena
- `http://ВАШ_IP/docs` — Swagger (на prod позже можно закрыть)

## 6. Публикация плана

1. Swagger: `POST /auth/coach/register` и `/auth/coach/login`.
2. `POST /coach/plan/publish` — JSON из конструктора.
3. Спортсmen: `/web/` с login и `temp_password` из ответа publish.

## 7. HTTPS и домен (позже)

Когда будет домен, A-запись на IP → certbot + nginx (отдельный шаг).

## Обновление версии

```bash
cd /opt/training
git pull
cd server
docker compose -f docker-compose.prod.yml up -d --build
```
