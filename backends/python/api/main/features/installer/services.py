from datetime import datetime
from hashlib import sha256
import json
from uuid import UUID

from ...models import ApplicationInstallation
from ...utils import AuthorizedRequest

INSTALLER_CONTRACT_VERSION = "2026-03-15"
INSTALLER_MAPPING_MODEL_VERSION = "1.0"
INSTALLER_SETUP_STATE_VERSION = "1.0"
REQUIRED_INSTALLER_SCOPES = (
    "crm",
    "lists",
    "tasks",
    "user",
    "placement",
    "userfieldconfig",
)

SCOPE_HINTS_RU = {
    "crm": "Нужен для создания цифрового рабочего места и смарт-процессов.",
    "lists": "Нужен для работы со списками (риски, вехи, бюджеты и т.д.).",
    "tasks": "Нужен для интеграции задач и синхронизации прогресса.",
    "user": "Нужен для чтения пользователей и ответственных.",
    "placement": "Нужен для встраивания интерфейса в Bitrix24.",
    "userfieldconfig": "Нужен для создания и обновления пользовательских полей.",
}


def get_installer_contract() -> dict:
    return {
        "contract_version": INSTALLER_CONTRACT_VERSION,
        "endpoints": {
            "install": {
                "method": "POST",
                "path": "/api/install",
                "description": "Create/update installation record with idempotent behavior",
            },
            "installation_context": {
                "method": "GET",
                "path": "/api/pmo/installation-context",
                "description": "Read current installation and account context",
            },
            "installer_contract": {
                "method": "GET",
                "path": "/api/pmo/installer/contract",
                "description": "Read active installer contract and mapping storage model",
            },
            "installer_mapping_get": {
                "method": "GET",
                "path": "/api/pmo/installer/mapping",
                "description": "Read current Smart Processes/Lists mapping state",
            },
            "installer_mapping_save": {
                "method": "POST",
                "path": "/api/pmo/installer/mapping/save",
                "description": "Update Smart Processes/Lists mapping state",
            },
            "installer_scope_check": {
                "method": "GET",
                "path": "/api/pmo/installer/scope-check",
                "description": "Check required scopes and admin rights for installer",
            },
            "installer_setup_state_get": {
                "method": "GET",
                "path": "/api/pmo/installer/setup-state",
                "description": "Read persisted installer setup state for current installation",
            },
            "installer_setup_state_save": {
                "method": "POST",
                "path": "/api/pmo/installer/setup-state/save",
                "description": "Persist installer setup progress and created entities",
            },
        },
        "idempotency": {
            "strategy": "domain+member+normalized_payload_fingerprint",
            "replay_behavior": "returns existing record and idempotent_replay=true",
            "conflict_rule": "new fingerprint updates existing installation in-place",
        },
        "mapping_storage_model": {
            "version": INSTALLER_MAPPING_MODEL_VERSION,
            "state_container": "application_installation.status_code.mapping",
            "shape": {
                "smart_processes": {},
                "lists": {},
                "meta": {
                    "state": "not_configured",
                    "updated_at_utc": "ISO-8601",
                },
            },
            "note": "RD-102/RD-103 can evolve fields while preserving versioned container",
        },
        "setup_state_model": {
            "version": INSTALLER_SETUP_STATE_VERSION,
            "state_container": "application_installation.status_code.setup_state",
            "shape": {
                "current_step": "scope_check",
                "workplace": {
                    "title": "",
                    "id": None,
                    "link": "",
                    "status": "pending",
                },
                "goals_process": {
                    "entity_type_id": None,
                    "link": "",
                    "status": "pending",
                },
                "goals_fields": {
                    "status": "pending",
                    "created_fields": [],
                    "codes_added": [],
                },
                "goals_card_configuration": {
                    "status": "pending",
                    "common_scope_forced": False,
                },
                "completed_steps": [],
                "updated_at_utc": "ISO-8601",
            },
        },
        "required_scopes": list(REQUIRED_INSTALLER_SCOPES),
    }


def upsert_installation(request: AuthorizedRequest) -> dict:
    bitrix24_account = request.bitrix24_account
    payload = request.data or {}
    normalized_payload = _normalize_installation_payload(payload, bitrix24_account)
    idempotency_fingerprint = _build_fingerprint(
        domain_url=bitrix24_account.domain_url,
        member_id=bitrix24_account.member_id,
        normalized_payload=normalized_payload,
    )

    existing_installation = ApplicationInstallation.objects.filter(bitrix_24_account=bitrix24_account).first()
    if existing_installation is not None:
        existing_fingerprint = _extract_fingerprint(existing_installation.status_code)
        if existing_fingerprint == idempotency_fingerprint:
            return {
                "message": "Установка уже сохранена, повторная запись не требуется",
                "contract_version": INSTALLER_CONTRACT_VERSION,
                "idempotent_replay": True,
                "installation": _serialize_installation(existing_installation),
            }

    existing_status_code = existing_installation.status_code if (existing_installation and isinstance(existing_installation.status_code, dict)) else {}
    status_payload = _build_status_payload(
        raw_payload=payload,
        normalized_payload=normalized_payload,
        idempotency_fingerprint=idempotency_fingerprint,
        existing_status_code=existing_status_code,
    )

    installation, _ = ApplicationInstallation.objects.update_or_create(
        bitrix_24_account=bitrix24_account,
        defaults={
            "status": normalized_payload["status"],
            "portal_license_family": normalized_payload["portal_license_family"],
            "portal_users_count": normalized_payload["portal_users_count"],
            "application_token": normalized_payload["application_token"],
            "external_id": normalized_payload["external_id"],
            "comment": normalized_payload["comment"],
            "status_code": status_payload,
        },
    )

    return {
        "message": "Установка успешно сохранена",
        "contract_version": INSTALLER_CONTRACT_VERSION,
        "idempotent_replay": False,
        "installation": _serialize_installation(installation),
    }


def get_installation_context(request: AuthorizedRequest) -> dict:
    bitrix24_account = request.bitrix24_account
    installation = ApplicationInstallation.objects.filter(bitrix_24_account=bitrix24_account).first()

    if installation is None:
        return {
            "installed": False,
            "message": "Запись об установке не найдена",
            "account": _serialize_account(bitrix24_account),
            "installation": None,
        }

    return {
        "installed": True,
        "message": "Поздравляю, установка прошла успешно. Это страница настройки приложения.",
        "contract_version": INSTALLER_CONTRACT_VERSION,
        "account": _serialize_account(bitrix24_account),
        "installation": _serialize_installation(installation),
    }


def issue_jwt(request: AuthorizedRequest) -> dict:
    return {"token": request.bitrix24_account.create_jwt_token()}


def get_installer_mapping(request: AuthorizedRequest) -> dict:
    installation = _get_or_create_installation(request)
    return {
        "contract_version": INSTALLER_CONTRACT_VERSION,
        "mapping": _extract_mapping(installation.status_code),
    }


def save_installer_mapping(request: AuthorizedRequest) -> dict:
    installation = _get_or_create_installation(request)
    payload = request.data or {}
    if not isinstance(payload, dict):
        payload = {}

    current_status_code = installation.status_code if isinstance(installation.status_code, dict) else {}
    mapping_payload = payload.get("mapping")
    if not isinstance(mapping_payload, dict):
        mapping_payload = payload

    normalized_mapping = _normalize_mapping_payload(mapping_payload)
    current_status_code["mapping"] = normalized_mapping
    installation.status_code = current_status_code
    installation.save(update_fields=["status_code", "update_at_utc"])

    return {
        "message": "Маппинг успешно сохранен",
        "contract_version": INSTALLER_CONTRACT_VERSION,
        "mapping": normalized_mapping,
    }


def get_scope_check(request: AuthorizedRequest) -> dict:
    account = request.bitrix24_account
    current_scope_raw = account.current_scope
    if isinstance(current_scope_raw, list):
        current_scopes = [str(item) for item in current_scope_raw if item]
    elif isinstance(current_scope_raw, str):
        current_scopes = [part.strip() for part in current_scope_raw.split(",") if part.strip()]
    else:
        current_scopes = []

    current_scope_set = set(current_scopes)
    required_scope_set = set(REQUIRED_INSTALLER_SCOPES)
    missing_scopes = sorted(required_scope_set - current_scope_set)
    has_required_scopes = len(missing_scopes) == 0
    is_admin = bool(account.is_b24_user_admin)

    scope_recommendations = [
        {
            "scope": scope,
            "hint": SCOPE_HINTS_RU.get(scope, "Требуется для корректной работы мастера настройки."),
        }
        for scope in missing_scopes
    ]

    next_steps = []
    if not is_admin:
        next_steps.append("Откройте приложение под учетной записью администратора Bitrix24.")
    if missing_scopes:
        next_steps.append("Выдайте приложению недостающие разрешения и переустановите приложение.")
    if is_admin and has_required_scopes:
        next_steps.append("Разрешения в норме. Можно переходить к следующим шагам настройки.")

    return {
        "contract_version": INSTALLER_CONTRACT_VERSION,
        "required_scopes": list(REQUIRED_INSTALLER_SCOPES),
        "current_scopes": sorted(current_scope_set),
        "missing_scopes": missing_scopes,
        "scope_recommendations": scope_recommendations,
        "is_admin": is_admin,
        "is_ready": bool(is_admin and has_required_scopes),
        "next_steps": next_steps,
    }


def get_installer_setup_state(request: AuthorizedRequest) -> dict:
    installation = _get_or_create_installation(request)
    return {
        "contract_version": INSTALLER_CONTRACT_VERSION,
        "setup_state": _extract_setup_state(installation.status_code),
    }


def save_installer_setup_state(request: AuthorizedRequest) -> dict:
    installation = _get_or_create_installation(request)
    payload = request.data or {}
    if not isinstance(payload, dict):
        payload = {}

    setup_payload = payload.get("setup_state")
    if not isinstance(setup_payload, dict):
        setup_payload = payload

    current_status_code = installation.status_code if isinstance(installation.status_code, dict) else {}
    existing_setup = _extract_setup_state(current_status_code)
    normalized_setup = _normalize_setup_state_payload(setup_payload, existing_setup=existing_setup)
    current_status_code["setup_state"] = normalized_setup

    installation.status_code = current_status_code
    installation.save(update_fields=["status_code", "update_at_utc"])

    return {
        "message": "Состояние мастера сохранено",
        "contract_version": INSTALLER_CONTRACT_VERSION,
        "setup_state": normalized_setup,
    }


def _to_iso(value):
    if isinstance(value, datetime):
        return value.isoformat()
    return None


def _to_int(value):
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None


def _to_text(value):
    if value is None:
        return None
    return str(value)


def _to_uuid(value):
    if isinstance(value, UUID):
        return str(value)
    return _to_text(value)


def _serialize_account(account) -> dict:
    return {
        "id": _to_uuid(account.id),
        "domain_url": account.domain_url,
        "b24_user_id": account.b24_user_id,
        "member_id": account.member_id,
        "status": account.status,
        "application_version": account.application_version,
        "application_token": account.application_token,
        "access_token": account.access_token,
        "refresh_token": account.refresh_token,
        "expires": account.expires,
        "expires_in": account.expires_in,
        "is_b24_user_admin": account.is_b24_user_admin,
        "current_scope": account.current_scope,
        "created_at_utc": _to_iso(account.created_at_utc),
        "updated_at_utc": _to_iso(account.updated_at_utc),
    }


def _serialize_installation(installation) -> dict:
    return {
        "id": _to_uuid(installation.id),
        "status": installation.status,
        "portal_license_family": installation.portal_license_family,
        "portal_users_count": installation.portal_users_count,
        "application_token": installation.application_token,
        "external_id": installation.external_id,
        "comment": installation.comment,
        "status_code": installation.status_code,
        "created_at_utc": _to_iso(installation.created_at_utc),
        "update_at_utc": _to_iso(installation.update_at_utc),
    }


def _get_or_create_installation(request: AuthorizedRequest) -> ApplicationInstallation:
    account = request.bitrix24_account
    installation, _ = ApplicationInstallation.objects.get_or_create(
        bitrix_24_account=account,
        defaults={
            "status": account.status or "installed",
            "portal_license_family": "unknown",
            "application_token": account.application_token or "",
            "external_id": account.member_id or None,
            "status_code": {},
        },
    )
    return installation


def _normalize_installation_payload(payload: dict, bitrix24_account) -> dict:
    return {
        "status": str(payload.get("status") or bitrix24_account.status or "installed"),
        "portal_license_family": str(payload.get("LICENSE_FAMILY") or payload.get("license_family") or "unknown"),
        "portal_users_count": _to_int(payload.get("portal_users_count")),
        "application_token": str(
            payload.get("APP_SID")
            or payload.get("application_token")
            or bitrix24_account.application_token
            or ""
        ),
        "external_id": _to_text(payload.get("member_id")),
        "comment": _to_text(payload.get("comment")),
    }


def _build_status_payload(raw_payload: dict, normalized_payload: dict, idempotency_fingerprint: str, existing_status_code: dict | None = None) -> dict:
    now_iso = datetime.utcnow().isoformat() + "Z"
    status_payload = dict(raw_payload)
    current_existing = existing_status_code if isinstance(existing_status_code, dict) else {}

    mapping = status_payload.get("mapping")
    if not isinstance(mapping, dict):
        mapping = current_existing.get("mapping") if isinstance(current_existing.get("mapping"), dict) else {}

    status_payload["mapping"] = _normalize_mapping_payload(mapping, now_iso=now_iso)
    status_payload["setup_state"] = _normalize_setup_state_payload(
        status_payload.get("setup_state") if isinstance(status_payload.get("setup_state"), dict) else {},
        existing_setup=_extract_setup_state(current_existing),
    )
    status_payload["_contract"] = {
        "version": INSTALLER_CONTRACT_VERSION,
        "idempotency_fingerprint": idempotency_fingerprint,
        "saved_at_utc": now_iso,
    }
    status_payload["_normalized_payload"] = normalized_payload
    return status_payload


def _build_fingerprint(domain_url: str, member_id: str | None, normalized_payload: dict) -> str:
    source = {
        "domain_url": domain_url,
        "member_id": member_id,
        "normalized_payload": normalized_payload,
    }
    encoded = json.dumps(source, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _extract_fingerprint(status_code) -> str | None:
    if not isinstance(status_code, dict):
        return None
    contract = status_code.get("_contract")
    if not isinstance(contract, dict):
        return None
    value = contract.get("idempotency_fingerprint")
    if not value:
        return None
    return str(value)


def _extract_mapping(status_code) -> dict:
    if not isinstance(status_code, dict):
        return _normalize_mapping_payload({})
    mapping = status_code.get("mapping")
    return _normalize_mapping_payload(mapping if isinstance(mapping, dict) else {})


def _normalize_mapping_payload(mapping: dict, now_iso: str | None = None) -> dict:
    current_now_iso = now_iso or (datetime.utcnow().isoformat() + "Z")
    meta = mapping.get("meta") if isinstance(mapping.get("meta"), dict) else {}
    return {
        "smart_processes": mapping.get("smart_processes") if isinstance(mapping.get("smart_processes"), dict) else {},
        "lists": mapping.get("lists") if isinstance(mapping.get("lists"), dict) else {},
        "meta": {
            "version": INSTALLER_MAPPING_MODEL_VERSION,
            "state": _to_text(meta.get("state")) or "not_configured",
            "updated_at_utc": current_now_iso,
        },
    }


def _extract_setup_state(status_code) -> dict:
    if not isinstance(status_code, dict):
        return _normalize_setup_state_payload({})
    setup_state = status_code.get("setup_state")
    if not isinstance(setup_state, dict):
        return _normalize_setup_state_payload({})
    return _normalize_setup_state_payload(setup_state)


def _normalize_setup_state_payload(setup_state: dict, existing_setup: dict | None = None) -> dict:
    current_now_iso = datetime.utcnow().isoformat() + "Z"
    existing = existing_setup if isinstance(existing_setup, dict) else {}

    workplace_src = setup_state.get("workplace") if isinstance(setup_state.get("workplace"), dict) else {}
    existing_workplace = existing.get("workplace") if isinstance(existing.get("workplace"), dict) else {}
    goals_src = setup_state.get("goals_process") if isinstance(setup_state.get("goals_process"), dict) else {}
    existing_goals = existing.get("goals_process") if isinstance(existing.get("goals_process"), dict) else {}
    goals_fields_src = setup_state.get("goals_fields") if isinstance(setup_state.get("goals_fields"), dict) else {}
    existing_goals_fields = existing.get("goals_fields") if isinstance(existing.get("goals_fields"), dict) else {}
    goals_card_src = (
        setup_state.get("goals_card_configuration")
        if isinstance(setup_state.get("goals_card_configuration"), dict)
        else {}
    )
    existing_goals_card = (
        existing.get("goals_card_configuration")
        if isinstance(existing.get("goals_card_configuration"), dict)
        else {}
    )

    current_step = _to_text(setup_state.get("current_step")) or _to_text(existing.get("current_step")) or "scope_check"
    completed_steps_raw = setup_state.get("completed_steps")
    if isinstance(completed_steps_raw, list):
        completed_steps = [str(step) for step in completed_steps_raw if step]
    else:
        fallback_steps = existing.get("completed_steps")
        completed_steps = [str(step) for step in fallback_steps] if isinstance(fallback_steps, list) else []

    return {
        "version": INSTALLER_SETUP_STATE_VERSION,
        "current_step": current_step,
        "workplace": {
            "title": _to_text(workplace_src.get("title")) or _to_text(existing_workplace.get("title")) or "",
            "id": _to_int(workplace_src.get("id")) if workplace_src.get("id") is not None else _to_int(existing_workplace.get("id")),
            "link": _to_text(workplace_src.get("link")) or _to_text(existing_workplace.get("link")) or "",
            "status": _to_text(workplace_src.get("status")) or _to_text(existing_workplace.get("status")) or "pending",
        },
        "goals_process": {
            "entity_type_id": _to_int(goals_src.get("entity_type_id")) if goals_src.get("entity_type_id") is not None else _to_int(existing_goals.get("entity_type_id")),
            "link": _to_text(goals_src.get("link")) or _to_text(existing_goals.get("link")) or "",
            "status": _to_text(goals_src.get("status")) or _to_text(existing_goals.get("status")) or "pending",
        },
        "goals_fields": {
            "status": _to_text(goals_fields_src.get("status")) or _to_text(existing_goals_fields.get("status")) or "pending",
            "created_fields": _normalize_created_fields(goals_fields_src.get("created_fields"), existing_goals_fields.get("created_fields")),
            "codes_added": _normalize_code_list(goals_fields_src.get("codes_added"), existing_goals_fields.get("codes_added")),
        },
        "goals_card_configuration": {
            "status": _to_text(goals_card_src.get("status")) or _to_text(existing_goals_card.get("status")) or "pending",
            "common_scope_forced": _to_bool(goals_card_src.get("common_scope_forced"), fallback=_to_bool(existing_goals_card.get("common_scope_forced"), fallback=False)),
            "details": _normalize_flat_dict(goals_card_src.get("details"), existing_goals_card.get("details")),
        },
        "completed_steps": completed_steps,
        "updated_at_utc": current_now_iso,
    }


def _to_bool(value, fallback: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"y", "yes", "true", "1"}:
            return True
        if lowered in {"n", "no", "false", "0"}:
            return False
    if isinstance(value, int):
        return value != 0
    return fallback


def _normalize_flat_dict(value, fallback) -> dict:
    if isinstance(value, dict):
        return dict(value)
    if isinstance(fallback, dict):
        return dict(fallback)
    return {}


def _normalize_code_list(value, fallback) -> list[str]:
    source = value if isinstance(value, list) else fallback
    if not isinstance(source, list):
        return []
    return [str(item) for item in source if item]


def _normalize_created_fields(value, fallback) -> list[dict]:
    source = value if isinstance(value, list) else fallback
    if not isinstance(source, list):
        return []
    normalized: list[dict] = []
    for item in source:
        if not isinstance(item, dict):
            continue
        normalized.append(
            {
                "title": _to_text(item.get("title")) or "",
                "code": _to_text(item.get("code")) or "",
                "field_id": _to_int(item.get("field_id")),
                "status": _to_text(item.get("status")) or "created",
            }
        )
    return normalized
