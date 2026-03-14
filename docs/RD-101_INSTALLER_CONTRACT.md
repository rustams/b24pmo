# RD-101: Контракт сервиса установщика

## Статус
- Эпик: `EPIC-INS`
- Задача: `RD-101`
- Версия контракта: `2026-03-15`

## Цель
Зафиксировать стабильный контракт установщика до начала задач `RD-102`/`RD-103`/`RD-104`, чтобы UI маппинга, проверки scope и первичная синхронизация опирались на одинаковые структуры данных.

## API-контракт

### `POST /api/install`
- Назначение: создать/обновить запись установки.
- Аутентификация: `auth_required`.
- Идемпотентность:
  - вычисляется fingerprint по `domain_url + member_id + normalized_payload`;
  - если fingerprint совпадает с сохраненным, запись не перезаписывается;
  - ответ возвращает `idempotent_replay=true`.
- Ответ:
  - `message`
  - `contract_version`
  - `idempotent_replay`
  - `installation`

### `GET /api/pmo/installation-context`
- Назначение: вернуть актуальный контекст установки и аккаунта.
- Аутентификация: `auth_required`.
- Ответ:
  - `installed`
  - `message`
  - `contract_version`
  - `account`
  - `installation`

### `GET /api/pmo/installer/contract`
- Назначение: вернуть декларативное описание активного backend-контракта.
- Аутентификация: `auth_required`.
- Ответ:
  - `contract_version`
  - `endpoints`
  - `idempotency`
  - `mapping_storage_model`

## Нормализация payload установки
Перед сохранением backend приводит входной payload к стабильной форме:
- `status`
- `portal_license_family`
- `portal_users_count`
- `application_token`
- `external_id`
- `comment`

Это делает fingerprint детерминированным и предотвращает ложные обновления из-за лишних полей.

## Модель хранения маппингов (фиксируется в RD-101)
Временный контракт хранения до выделения отдельного `app_config` слоя:

- Контейнер: `application_installation.status_code.mapping`
- Версия модели: `1.0`
- Структура:
  - `smart_processes` (dict)
  - `lists` (dict)
  - `meta.version`
  - `meta.state` (`not_configured` по умолчанию)
  - `meta.updated_at_utc`

Дополнительно в `status_code` сохраняются:
- `_contract.version`
- `_contract.idempotency_fingerprint`
- `_contract.saved_at_utc`
- `_normalized_payload`

## Ограничения и follow-up
- Полноценная миграция к выделенному `app_config` контейнеру переносится в последующие задачи этапа Installer.
- `RD-102` и `RD-103` должны использовать только версионированный контейнер `mapping` и не ломать обратную совместимость.
