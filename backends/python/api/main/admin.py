import json
from datetime import datetime, timezone as dt_timezone

from django.contrib import admin
from django.db import connection
from django.utils import timezone

from .models import ApplicationInstallation, Bitrix24Account


@admin.register(Bitrix24Account)
class Bitrix24AccountAdmin(admin.ModelAdmin):
    list_display = (
        "domain_url",
        "b24_user_id",
        "status",
        "is_b24_user_admin",
        "has_valid_tokens",
        "token_expires_at",
        "updated_at_utc",
    )
    list_filter = ("status", "is_b24_user_admin", "created_at_utc", "updated_at_utc")
    search_fields = ("domain_url", "member_id", "b24_user_id")
    ordering = ("-updated_at_utc",)
    readonly_fields = (
        "id",
        "has_valid_tokens",
        "token_expires_at",
        "scope_preview",
        "created_at_utc",
        "updated_at_utc",
    )

    fieldsets = (
        (
            "Account",
            {
                "fields": (
                    "id",
                    "domain_url",
                    "b24_user_id",
                    "member_id",
                    "status",
                    "is_b24_user_admin",
                    "application_version",
                )
            },
        ),
        (
            "Auth Analytics",
            {
                "fields": (
                    "has_valid_tokens",
                    "token_expires_at",
                    "access_token",
                    "refresh_token",
                    "expires",
                    "expires_in",
                    "scope_preview",
                )
            },
        ),
        (
            "Timestamps",
            {"fields": ("created_at_utc", "updated_at_utc")},
        ),
    )

    @admin.display(boolean=True, description="Has tokens")
    def has_valid_tokens(self, obj: Bitrix24Account) -> bool:
        return bool(obj.access_token and obj.refresh_token)

    @admin.display(description="Token expires at")
    def token_expires_at(self, obj: Bitrix24Account):
        if not obj.expires:
            return "unknown"
        try:
            return datetime.fromtimestamp(obj.expires, tz=dt_timezone.utc).isoformat()
        except (TypeError, ValueError, OSError):
            return "invalid"

    @admin.display(description="Current scope")
    def scope_preview(self, obj: Bitrix24Account) -> str:
        if not obj.current_scope:
            return "-"
        if isinstance(obj.current_scope, list):
            return ", ".join(str(value) for value in obj.current_scope)
        return str(obj.current_scope)


@admin.register(ApplicationInstallation)
class ApplicationInstallationAdmin(admin.ModelAdmin):
    list_display = (
        "domain_url",
        "status",
        "portal_license_family",
        "portal_users_count",
        "account_status",
        "auth_health",
        "update_at_utc",
    )
    list_filter = (
        "status",
        "portal_license_family",
        "bitrix_24_account__status",
        "created_at_utc",
        "update_at_utc",
    )
    search_fields = (
        "external_id",
        "application_token",
        "comment",
        "bitrix_24_account__domain_url",
        "bitrix_24_account__member_id",
    )
    ordering = ("-update_at_utc",)
    list_select_related = ("bitrix_24_account",)
    readonly_fields = (
        "id",
        "domain_url",
        "account_status",
        "account_member_id",
        "auth_health",
        "token_expires_at",
        "status_payload_preview",
        "installation_age_hours",
        "created_at_utc",
        "update_at_utc",
    )

    fieldsets = (
        (
            "Installation",
            {
                "fields": (
                    "id",
                    "status",
                    "portal_license_family",
                    "portal_users_count",
                    "external_id",
                    "application_token",
                    "comment",
                    "created_at_utc",
                    "update_at_utc",
                )
            },
        ),
        (
            "Portal Analytics",
            {
                "fields": (
                    "domain_url",
                    "account_member_id",
                    "account_status",
                    "auth_health",
                    "token_expires_at",
                    "installation_age_hours",
                )
            },
        ),
        (
            "Diagnostic Payload",
            {"fields": ("status_payload_preview",)},
        ),
    )

    def get_queryset(self, request):
        # Some environments return JSON as native dict for this legacy table,
        # while Django JSONField loader expects text and crashes in admin list.
        return super().get_queryset(request).defer("status_code")

    @admin.display(description="Portal domain", ordering="bitrix_24_account__domain_url")
    def domain_url(self, obj: ApplicationInstallation) -> str:
        if not obj.bitrix_24_account:
            return "-"
        return obj.bitrix_24_account.domain_url

    @admin.display(description="Account status", ordering="bitrix_24_account__status")
    def account_status(self, obj: ApplicationInstallation) -> str:
        if not obj.bitrix_24_account:
            return "missing_account"
        return obj.bitrix_24_account.status or "unknown"

    @admin.display(description="Member ID", ordering="bitrix_24_account__member_id")
    def account_member_id(self, obj: ApplicationInstallation) -> str:
        if not obj.bitrix_24_account:
            return "-"
        return obj.bitrix_24_account.member_id or "-"

    @admin.display(description="Auth health")
    def auth_health(self, obj: ApplicationInstallation) -> str:
        account = obj.bitrix_24_account
        if not account:
            return "error:no_account"
        if not account.access_token or not account.refresh_token:
            return "error:missing_tokens"
        if account.expires and account.expires < int(timezone.now().timestamp()):
            return "warn:expired_token"
        return "ok"

    @admin.display(description="Token expires at")
    def token_expires_at(self, obj: ApplicationInstallation):
        account = obj.bitrix_24_account
        if not account or not account.expires:
            return "unknown"
        try:
            return datetime.fromtimestamp(account.expires, tz=dt_timezone.utc).isoformat()
        except (TypeError, ValueError, OSError):
            return "invalid"

    @admin.display(description="Installation age (hours)")
    def installation_age_hours(self, obj: ApplicationInstallation):
        if not obj.created_at_utc:
            return "unknown"
        created_at = obj.created_at_utc
        if timezone.is_naive(created_at):
            created_at = timezone.make_aware(created_at, timezone=dt_timezone.utc)
        delta = timezone.now() - created_at
        return round(delta.total_seconds() / 3600, 2)

    @admin.display(description="Status payload preview")
    def status_payload_preview(self, obj: ApplicationInstallation) -> str:
        raw_payload = self._fetch_status_payload_text(obj)
        if not raw_payload:
            return "-"
        return raw_payload[:2000]

    def _fetch_status_payload_text(self, obj: ApplicationInstallation) -> str:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT status_code::text FROM application_installation WHERE id = %s",
                [str(obj.id)],
            )
            row = cursor.fetchone()
        if not row or row[0] in (None, ""):
            return ""
        raw = row[0]
        if isinstance(raw, str):
            return raw
        try:
            return json.dumps(raw, ensure_ascii=True, indent=2)
        except (TypeError, ValueError):
            return str(raw)
