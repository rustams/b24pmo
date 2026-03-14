import json
from datetime import datetime, timezone as dt_timezone

from django.contrib import admin
from django.db import connection
from django.utils.html import format_html
from django.utils import timezone
from unfold.admin import ModelAdmin

from .models import ApplicationInstallation, Bitrix24Account


@admin.register(Bitrix24Account)
class Bitrix24AccountAdmin(ModelAdmin):
    list_display = (
        "domain_url",
        "b24_user_id",
        "status_badge",
        "is_b24_user_admin",
        "has_valid_tokens",
        "token_ttl_hours",
        "token_expires_at",
        "updated_at_utc",
    )
    list_filter = ("status", "is_b24_user_admin", "created_at_utc", "updated_at_utc")
    search_fields = ("domain_url", "member_id", "b24_user_id")
    ordering = ("-updated_at_utc",)
    list_per_page = 50
    readonly_fields = (
        "id",
        "status_badge",
        "has_valid_tokens",
        "token_ttl_hours",
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
                    "status_badge",
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
                    "token_ttl_hours",
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

    @admin.display(description="Status")
    def status_badge(self, obj: Bitrix24Account) -> str:
        status_value = (obj.status or "unknown").lower()
        colors = {
            "active": ("#14532d", "#dcfce7"),
            "installed": ("#14532d", "#dcfce7"),
            "new": ("#1e3a8a", "#dbeafe"),
            "blocked": ("#7c2d12", "#ffedd5"),
            "error": ("#7f1d1d", "#fee2e2"),
            "deleted": ("#334155", "#e2e8f0"),
        }
        fg, bg = colors.get(status_value, ("#3f3f46", "#f4f4f5"))
        return format_html(
            '<span style="display:inline-block;padding:2px 10px;border-radius:999px;'
            "font-weight:600;color:{};background:{};\">{}</span>",
            fg,
            bg,
            obj.status or "unknown",
        )

    @admin.display(description="Token TTL (h)")
    def token_ttl_hours(self, obj: Bitrix24Account):
        if not obj.expires:
            return "unknown"
        try:
            ttl_seconds = obj.expires - int(timezone.now().timestamp())
        except (TypeError, ValueError):
            return "invalid"
        return round(ttl_seconds / 3600, 2)

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
class ApplicationInstallationAdmin(ModelAdmin):
    list_display = (
        "domain_url",
        "status_badge",
        "auth_health_badge",
        "portal_license_family",
        "portal_size_tier",
        "portal_users_count",
        "account_status_badge",
        "token_ttl_hours",
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
    list_per_page = 50
    readonly_fields = (
        "id",
        "domain_url",
        "status_badge",
        "account_status_badge",
        "auth_health_badge",
        "portal_size_tier",
        "portal_overview",
        "account_status",
        "account_member_id",
        "auth_health",
        "token_ttl_hours",
        "token_expires_at",
        "auth_timeline",
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
                    "status_badge",
                    "status",
                    "portal_license_family",
                    "portal_size_tier",
                    "portal_users_count",
                    "portal_overview",
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
                    "account_status_badge",
                    "account_status",
                    "auth_health_badge",
                    "auth_health",
                    "token_ttl_hours",
                    "token_expires_at",
                    "auth_timeline",
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

    @admin.display(description="Status")
    def status_badge(self, obj: ApplicationInstallation) -> str:
        status_value = (obj.status or "unknown").lower()
        colors = {
            "active": ("#14532d", "#dcfce7"),
            "installed": ("#14532d", "#dcfce7"),
            "new": ("#1e3a8a", "#dbeafe"),
            "blocked": ("#7c2d12", "#ffedd5"),
            "error": ("#7f1d1d", "#fee2e2"),
            "deleted": ("#334155", "#e2e8f0"),
        }
        fg, bg = colors.get(status_value, ("#3f3f46", "#f4f4f5"))
        return format_html(
            '<span style="display:inline-block;padding:2px 10px;border-radius:999px;'
            "font-weight:600;color:{};background:{};\">{}</span>",
            fg,
            bg,
            obj.status or "unknown",
        )

    @admin.display(description="Account status", ordering="bitrix_24_account__status")
    def account_status(self, obj: ApplicationInstallation) -> str:
        if not obj.bitrix_24_account:
            return "missing_account"
        return obj.bitrix_24_account.status or "unknown"

    @admin.display(description="Account")
    def account_status_badge(self, obj: ApplicationInstallation) -> str:
        value = self.account_status(obj)
        status_value = value.lower()
        colors = {
            "active": ("#14532d", "#dcfce7"),
            "new": ("#1e3a8a", "#dbeafe"),
            "blocked": ("#7c2d12", "#ffedd5"),
            "error": ("#7f1d1d", "#fee2e2"),
            "missing_account": ("#7f1d1d", "#fee2e2"),
        }
        fg, bg = colors.get(status_value, ("#3f3f46", "#f4f4f5"))
        return format_html(
            '<span style="display:inline-block;padding:2px 10px;border-radius:999px;'
            "font-weight:600;color:{};background:{};\">{}</span>",
            fg,
            bg,
            value,
        )

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

    @admin.display(description="Auth health")
    def auth_health_badge(self, obj: ApplicationInstallation) -> str:
        value = self.auth_health(obj)
        colors = {
            "ok": ("#14532d", "#dcfce7"),
            "warn:expired_token": ("#7c2d12", "#ffedd5"),
            "error:no_account": ("#7f1d1d", "#fee2e2"),
            "error:missing_tokens": ("#7f1d1d", "#fee2e2"),
        }
        fg, bg = colors.get(value, ("#3f3f46", "#f4f4f5"))
        return format_html(
            '<span style="display:inline-block;padding:2px 10px;border-radius:999px;'
            "font-weight:600;color:{};background:{};\">{}</span>",
            fg,
            bg,
            value,
        )

    @admin.display(description="Portal tier")
    def portal_size_tier(self, obj: ApplicationInstallation) -> str:
        users = obj.portal_users_count or 0
        if users <= 0:
            return "unknown"
        if users < 50:
            return "small (<50)"
        if users < 250:
            return "medium (50-249)"
        return "large (250+)"

    @admin.display(description="Portal overview")
    def portal_overview(self, obj: ApplicationInstallation) -> str:
        return (
            f"domain={self.domain_url(obj)}; "
            f"license={obj.portal_license_family or '-'}; "
            f"users={obj.portal_users_count if obj.portal_users_count is not None else '-'}; "
            f"tier={self.portal_size_tier(obj)}"
        )

    @admin.display(description="Token TTL (h)")
    def token_ttl_hours(self, obj: ApplicationInstallation):
        account = obj.bitrix_24_account
        if not account or not account.expires:
            return "unknown"
        try:
            ttl_seconds = account.expires - int(timezone.now().timestamp())
        except (TypeError, ValueError):
            return "invalid"
        return round(ttl_seconds / 3600, 2)

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

    @admin.display(description="Auth timeline")
    def auth_timeline(self, obj: ApplicationInstallation) -> str:
        health = self.auth_health(obj)
        expires_at = self.token_expires_at(obj)
        ttl_hours = self.token_ttl_hours(obj)
        return f"health={health}; token_expires_at={expires_at}; token_ttl_h={ttl_hours}"

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
