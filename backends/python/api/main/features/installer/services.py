from datetime import datetime
from uuid import UUID

from ...models import ApplicationInstallation
from ...utils import AuthorizedRequest


def upsert_installation(request: AuthorizedRequest) -> dict:
    bitrix24_account = request.bitrix24_account
    payload = request.data or {}

    installation, _ = ApplicationInstallation.objects.update_or_create(
        bitrix_24_account=bitrix24_account,
        defaults={
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
            "status_code": payload,
        },
    )

    return {
        "message": "Установка успешно сохранена",
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
        "account": _serialize_account(bitrix24_account),
        "installation": _serialize_installation(installation),
    }


def issue_jwt(request: AuthorizedRequest) -> dict:
    return {"token": request.bitrix24_account.create_jwt_token()}


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
