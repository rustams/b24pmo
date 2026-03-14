# Cloud-init для развёртывания VPS (PMO Hub / b24pmo)

Один сценарий подготавливает сервер под стек **frontend (Nuxt) + Python (Django) + PostgreSQL**: пакеты, пользователь `deploy`, клонирование репозитория, Nginx, systemd, скрипты `b24-deploy` / `b24-status` / `b24-logs`.

Подходит для [Timeweb Cloud](https://timeweb.cloud/docs/cloud-servers/manage-servers/cloud-init) и других облаков с поддержкой cloud-init.

## Перед использованием

В файле **`cloud-config.yml`** замени плейсхолдеры (по всему файлу):

| Плейсхолдер    | На что заменить | Пример |
|----------------|-----------------|--------|
| `YOUR_DOMAIN`  | Домен приложения (DNS A уже указывает на IP сервера) | `app.example.ru` |
| `YOUR_SSH_KEY` | Одна строка твоего **публичного** SSH-ключа | `ssh-ed25519 AAAAC3... user@host` |
| `REPO_URL`     | URL репозитория (в runcmd, в кавычках) | `https://github.com/rustams/b24pmo.git` |

Как получить ключ на Mac:
```bash
cat ~/.ssh/id_ed25519.pub
# или
cat ~/.ssh/id_rsa.pub
```

Ключ будет добавлен и для **root**, и для пользователя **deploy** — с этого же компьютера потом можно входить как `ssh root@IP` и `ssh deploy@IP`.

## Как применить в Timeweb Cloud

1. **При создании сервера**  
   В разделе сценария cloud-init вставь содержимое отредактированного `cloud-config.yml`. Параметры применятся при первой загрузке.

2. **На уже созданном сервере**  
   В панели: Конфигурация → Cloud-init → Редактировать → вставить сценарий → Сохранить. Затем на сервере выполнить:
   ```bash
   cloud-init clean --reboot
   ```
   После перезагрузки сценарий выполнится заново.

Лог выполнения: на сервере в `/var/log/cloud-init-output.log`.

## Что делает сценарий

- Устанавливает: git, make, docker, docker-compose-plugin, nginx, certbot, python3-certbot-nginx, ufw.
- Добавляет твой SSH-ключ для root и создаёт пользователя **deploy** с тем же ключом и правом запуска Docker.
- Клонирует репозиторий в `/opt/b24-ai-starter`, копирует `.env.example` в `.env`, подставляет в `.env` значение `VIRTUAL_HOST=https://YOUR_DOMAIN`.
- Создаёт конфиг Nginx для `YOUR_DOMAIN` (проксирование на 127.0.0.1:3000), включает сайт, отключает default.
- Открывает в ufw порты 22, 80, 443 и включает firewall.
- Создаёт systemd-юнит `b24-ai-starter` и скрипты `/usr/local/bin/b24-deploy`, `b24-status`, `b24-logs`.
- Запускает Docker и сервис приложения (первый запуск может занять несколько минут из-за сборки образов).

## После первой загрузки

1. **Секреты в `.env`**  
   Зайди на сервер (`ssh deploy@IP` или `ssh root@IP`) и отредактируй `/opt/b24-ai-starter/.env`: подставь реальные `JWT_SECRET`, `CLIENT_ID`, `CLIENT_SECRET`, при необходимости поправь `VIRTUAL_HOST` и другие переменные. Затем:
   ```bash
   sudo systemctl restart b24-ai-starter
   ```

2. **HTTPS (Let's Encrypt)**  
   Когда DNS указывает на сервер и по `http://YOUR_DOMAIN` открывается приложение:
   ```bash
   sudo certbot --nginx -d YOUR_DOMAIN
   ```
   Certbot сам настроит Nginx на HTTPS и редирект с HTTP.

3. **Проверка с твоего Mac**  
   В проекте в `.env.webhooks` задай:
   - `VPS_DEPLOY_HOST=<IP нового сервера>`
   - `VPS_HEALTH_URL=https://YOUR_DOMAIN`  
   После этого `./scripts/vps/verify-sync.sh` будет проверять деплой после каждого push.

## Замечания

- На Ubuntu cloud-init по умолчанию может создать пользователя `ubuntu`; в сценарии указано `users: []`, чтобы этого не делать.
- Сценарий выполняется один раз (runcmd при первой загрузке). Повторно применить можно через `cloud-init clean --reboot` (осторожно: перезагрузка).
- Webhook для авто-деплоя (GitHub → POST /deploy-webhook) в этот сценарий не входит; его можно добавить отдельно или настроить вручную по [HISTORY.md](../../HISTORY.md).
