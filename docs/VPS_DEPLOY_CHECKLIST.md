# Чеклист деплоя на новый VPS

Актуальный стек в репозитории: **frontend (Nuxt) + Python (Django) + PostgreSQL**. Публичный доступ — через Nginx, TLS (Let's Encrypt).

## Данные, которые нужны от тебя

| Данные | Пример | Зачем |
|--------|--------|--------|
| **IP или hostname сервера** | `1.2.3.4` или `vps.example.com` | Подключение по SSH |
| **Доступ по SSH** | root по ключу или паролю (временно) | Первичная настройка; потом — пользователь `deploy` по ключу |
| **Домен** | `app.example.ru` | Nginx + Let's Encrypt; DNS A-запись должна указывать на IP сервера |
| **Путь приложения на VPS** | `/opt/b24-ai-starter` (по умолчанию) | Куда клонировать репозиторий |
| **Репозиторий** | `git@github.com:rustams/b24pmo.git` или твой fork | Откуда тянуть код |
| **Ветка для деплоя** | `master` | Как в текущем workflow |

Опционально (для авто-деплоя по push):

| Данные | Зачем |
|--------|--------|
| Секрет webhook (GitHub) | Проверка подписи запросов на `/deploy-webhook` |

После деплоя для проверки с твоего Mac в `.env.webhooks` нужны: `VPS_DEPLOY_HOST` (IP нового сервера), `VPS_HEALTH_URL` (https://твой-домен).

## Этапы развёртывания (что делаю я при наличии доступа)

1. **Базовые пакеты** (на VPS): git, make, docker.io, docker compose plugin, nginx, certbot, python3-certbot-nginx, ufw.
2. **Клонирование**: репозиторий в выбранный путь (например `/opt/b24-ai-starter`), ветка `master`.
3. **Окружение**: создать `.env` на VPS из `.env.example` (JWT, Bitrix CLIENT_ID/SECRET, VIRTUAL_HOST=https://твой-домен, SERVER_HOST, DB_*, без CloudPub при прямом деплое).
4. **Docker Compose**: профили `frontend`, `python`, `db-postgres`. Frontend слушает только localhost (127.0.0.1:3000), наружу — через Nginx.
5. **Nginx**: виртуальный хост для домена, проксирование на 127.0.0.1:3000, редирект HTTP → HTTPS.
6. **Let's Encrypt**: сертификат для домена.
7. **systemd**: юнит для приложения (запуск docker compose при загрузке).
8. **Пользователь deploy**: создать пользователя, добавить ключ с твоего Mac в `~deploy/.ssh/authorized_keys`, скрипты `b24-deploy`, `b24-status`, `b24-logs` в `/usr/local/bin/`, при необходимости — webhook-сервис.
9. **Проверка**: `curl -s -o /dev/null -w '%{http_code}' https://твой-домен` → 200.

После этого: push в `master` → (при настроенном webhook) авто-деплой, либо вручную `ssh deploy@IP 'b24-deploy master'`; локально `./scripts/vps/verify-sync.sh` при заданных `VPS_DEPLOY_HOST` и `VPS_HEALTH_URL`.

## Разовый запуск через cloud-init (Timeweb и др.)

Чтобы подготовить новый VPS одной вставкой сценария при создании сервера или переустановке:

1. Открой `infrastructure/cloud-init/cloud-config.yml`.
2. Замени по всему файлу: `YOUR_DOMAIN` → твой домен, `YOUR_SSH_KEY` → строка публичного ключа (из `cat ~/.ssh/id_ed25519.pub`), `REPO_URL` → `https://github.com/rustams/b24pmo.git` (или свой fork).
3. В панели Timeweb при создании сервера (или в Конфигурации → Cloud-init) вставь содержимое файла.
4. После первой загрузки: дописать секреты в `/opt/b24-ai-starter/.env`, при необходимости запустить `certbot --nginx -d YOUR_DOMAIN`.

Подробно: `infrastructure/cloud-init/README.md`.
