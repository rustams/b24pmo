import json
import os
from collections import Counter, deque
from datetime import datetime, timezone as dt_timezone
from pathlib import Path

from django.contrib import admin
from django.db import connection
from django.db.models import Count, Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils.html import format_html
from django.utils import timezone
from django.urls import path
from unfold.admin import ModelAdmin

from .models import ApplicationInstallation, Bitrix24Account


def _to_chart_rows(rows: list[dict], label_key: str = "status", value_key: str = "count") -> list[dict]:
    total = sum(int(item.get(value_key, 0) or 0) for item in rows) or 1
    chart = []
    for item in rows:
        value = int(item.get(value_key, 0) or 0)
        label = str(item.get(label_key) or "unknown")
        chart.append(
            {
                "label": label,
                "value": value,
                "percent": round((value / total) * 100, 2),
            }
        )
    return chart


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
            "Аккаунт",
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
            "Авторизация и токены",
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
            "Временные метки",
            {"fields": ("created_at_utc", "updated_at_utc")},
        ),
    )

    @admin.display(boolean=True, description="Токены есть")
    def has_valid_tokens(self, obj: Bitrix24Account) -> bool:
        return bool(obj.access_token and obj.refresh_token)

    @admin.display(description="Статус")
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

    @admin.display(description="TTL токена (ч)")
    def token_ttl_hours(self, obj: Bitrix24Account):
        if not obj.expires:
            return "unknown"
        try:
            ttl_seconds = obj.expires - int(timezone.now().timestamp())
        except (TypeError, ValueError):
            return "invalid"
        return round(ttl_seconds / 3600, 2)

    @admin.display(description="Токен истекает")
    def token_expires_at(self, obj: Bitrix24Account):
        if not obj.expires:
            return "unknown"
        try:
            return datetime.fromtimestamp(obj.expires, tz=dt_timezone.utc).isoformat()
        except (TypeError, ValueError, OSError):
            return "invalid"

    @admin.display(description="Текущий scope")
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
            "Установка",
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
            "Аналитика портала",
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
            "Диагностический payload",
            {"fields": ("status_payload_preview",)},
        ),
    )

    def get_queryset(self, request):
        # Some environments return JSON as native dict for this legacy table,
        # while Django JSONField loader expects text and crashes in admin list.
        return super().get_queryset(request).defer("status_code")

    @admin.display(description="Домен портала", ordering="bitrix_24_account__domain_url")
    def domain_url(self, obj: ApplicationInstallation) -> str:
        if not obj.bitrix_24_account:
            return "-"
        return obj.bitrix_24_account.domain_url

    @admin.display(description="Статус")
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

    @admin.display(description="Статус аккаунта", ordering="bitrix_24_account__status")
    def account_status(self, obj: ApplicationInstallation) -> str:
        if not obj.bitrix_24_account:
            return "missing_account"
        return obj.bitrix_24_account.status or "unknown"

    @admin.display(description="Аккаунт")
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

    @admin.display(description="Состояние авторизации")
    def auth_health(self, obj: ApplicationInstallation) -> str:
        account = obj.bitrix_24_account
        if not account:
            return "error:no_account"
        if not account.access_token or not account.refresh_token:
            return "error:missing_tokens"
        if account.expires and account.expires < int(timezone.now().timestamp()):
            return "warn:expired_token"
        return "ok"

    @admin.display(description="Состояние авторизации")
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

    @admin.display(description="Размер портала")
    def portal_size_tier(self, obj: ApplicationInstallation) -> str:
        users = obj.portal_users_count or 0
        if users <= 0:
            return "unknown"
        if users < 50:
            return "small (<50)"
        if users < 250:
            return "medium (50-249)"
        return "large (250+)"

    @admin.display(description="Сводка портала")
    def portal_overview(self, obj: ApplicationInstallation) -> str:
        return (
            f"domain={self.domain_url(obj)}; "
            f"license={obj.portal_license_family or '-'}; "
            f"users={obj.portal_users_count if obj.portal_users_count is not None else '-'}; "
            f"tier={self.portal_size_tier(obj)}"
        )

    @admin.display(description="TTL токена (ч)")
    def token_ttl_hours(self, obj: ApplicationInstallation):
        account = obj.bitrix_24_account
        if not account or not account.expires:
            return "unknown"
        try:
            ttl_seconds = account.expires - int(timezone.now().timestamp())
        except (TypeError, ValueError):
            return "invalid"
        return round(ttl_seconds / 3600, 2)

    @admin.display(description="Токен истекает")
    def token_expires_at(self, obj: ApplicationInstallation):
        account = obj.bitrix_24_account
        if not account or not account.expires:
            return "unknown"
        try:
            return datetime.fromtimestamp(account.expires, tz=dt_timezone.utc).isoformat()
        except (TypeError, ValueError, OSError):
            return "invalid"

    @admin.display(description="Возраст установки (часы)")
    def installation_age_hours(self, obj: ApplicationInstallation):
        if not obj.created_at_utc:
            return "unknown"
        created_at = obj.created_at_utc
        if timezone.is_naive(created_at):
            created_at = timezone.make_aware(created_at, timezone=dt_timezone.utc)
        delta = timezone.now() - created_at
        return round(delta.total_seconds() / 3600, 2)

    @admin.display(description="Таймлайн авторизации")
    def auth_timeline(self, obj: ApplicationInstallation) -> str:
        health = self.auth_health(obj)
        expires_at = self.token_expires_at(obj)
        ttl_hours = self.token_ttl_hours(obj)
        return f"health={health}; token_expires_at={expires_at}; token_ttl_h={ttl_hours}"

    @admin.display(description="Предпросмотр payload статуса")
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


def _api_metrics_log_path() -> Path:
    return Path(os.getenv("API_METRICS_LOG_PATH", "/tmp/b24_api_metrics.log"))


def _load_api_metrics_snapshot():
    log_path = _api_metrics_log_path()
    if not log_path.exists():
        return {
            "source": str(log_path),
            "total": 0,
            "last_hour": 0,
            "avg_latency_ms": 0,
            "error_rate": 0,
            "top_paths": [],
            "latest_events": [],
        }

    recent_records = deque(maxlen=3000)
    with log_path.open("r", encoding="utf-8", errors="ignore") as metrics_file:
        for line in metrics_file:
            line = line.strip()
            if not line:
                continue
            try:
                recent_records.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    now_dt = timezone.now()
    one_hour_ago = now_dt - timezone.timedelta(hours=1)
    path_counter = Counter()
    statuses_5xx = 0
    latency_sum = 0.0
    latest_events = []
    last_hour = 0

    for record in recent_records:
        path_counter[record.get("path", "-")] += 1
        status_code = int(record.get("status_code", 0) or 0)
        if status_code >= 500:
            statuses_5xx += 1
        latency_sum += float(record.get("duration_ms", 0.0) or 0.0)
        timestamp_raw = record.get("timestamp")
        if timestamp_raw:
            try:
                ts = datetime.fromisoformat(timestamp_raw.replace("Z", "+00:00"))
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=dt_timezone.utc)
                if ts >= one_hour_ago:
                    last_hour += 1
            except ValueError:
                pass

    for record in list(recent_records)[-10:]:
        latest_events.append(
            {
                "timestamp": record.get("timestamp", "-"),
                "method": record.get("method", "-"),
                "path": record.get("path", "-"),
                "status_code": int(record.get("status_code", 0) or 0),
                "duration_ms": round(float(record.get("duration_ms", 0.0) or 0.0), 2),
            }
        )

    total = len(recent_records)
    avg_latency = round(latency_sum / total, 2) if total else 0
    error_rate = round((statuses_5xx / total) * 100, 2) if total else 0
    top_paths = [{"path": path, "count": count} for path, count in path_counter.most_common(8)]

    return {
        "source": str(log_path),
        "total": total,
        "last_hour": last_hour,
        "avg_latency_ms": avg_latency,
        "error_rate": error_rate,
        "top_paths": top_paths,
        "top_paths_chart": _to_chart_rows(top_paths, label_key="path", value_key="count"),
        "latest_events": list(reversed(latest_events)),
    }


def _server_stats_snapshot():
    try:
        import psutil
    except Exception:
        return {
            "available": False,
            "message": "psutil is not available yet",
            "cpu_percent": None,
            "memory_percent": None,
            "disk_percent": None,
            "load_avg": None,
            "boot_time": None,
        }

    disk_usage = psutil.disk_usage("/")
    load_avg = os.getloadavg() if hasattr(os, "getloadavg") else (None, None, None)
    return {
        "available": True,
        "message": "",
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": disk_usage.percent,
        "load_avg": [round(value, 2) for value in load_avg] if load_avg else None,
        "boot_time": datetime.fromtimestamp(psutil.boot_time(), tz=dt_timezone.utc).isoformat(),
    }


def _app_stats_snapshot():
    now_ts = int(timezone.now().timestamp())
    installations_qs = ApplicationInstallation.objects.select_related("bitrix_24_account")
    accounts_qs = Bitrix24Account.objects.all()

    installation_totals = installations_qs.aggregate(
        total=Count("id"),
        with_account=Count("id", filter=Q(bitrix_24_account__isnull=False)),
    )
    token_totals = accounts_qs.aggregate(
        total=Count("id"),
        with_tokens=Count("id", filter=Q(access_token__isnull=False) & Q(refresh_token__isnull=False)),
        expired=Count("id", filter=Q(expires__lt=now_ts)),
    )

    status_distribution = list(
        installations_qs.values("status")
        .annotate(count=Count("id"))
        .order_by("-count", "status")
    )
    account_status_distribution = list(
        accounts_qs.values("status")
        .annotate(count=Count("id"))
        .order_by("-count", "status")
    )

    return {
        "installations_total": installation_totals.get("total", 0),
        "installations_with_account": installation_totals.get("with_account", 0),
        "accounts_total": token_totals.get("total", 0),
        "accounts_with_tokens": token_totals.get("with_tokens", 0),
        "accounts_expired_tokens": token_totals.get("expired", 0),
        "installation_status_distribution": status_distribution,
        "account_status_distribution": account_status_distribution,
        "installation_status_chart": _to_chart_rows(status_distribution),
        "account_status_chart": _to_chart_rows(account_status_distribution),
    }


def app_dashboard_view(request: HttpRequest) -> HttpResponse:
    app_stats = _app_stats_snapshot()
    api_stats = _load_api_metrics_snapshot()
    server_stats = _server_stats_snapshot()
    context = {
        **admin.site.each_context(request),
        "title": "Дашборд приложения",
        "app_stats": app_stats,
        "api_stats": api_stats,
        "server_stats": server_stats,
        "tokens_health_percent": round(
            ((app_stats["accounts_with_tokens"] / app_stats["accounts_total"]) * 100)
            if app_stats["accounts_total"]
            else 0,
            2,
        ),
        "api_success_percent": round(100 - float(api_stats["error_rate"]), 2),
    }
    return render(request, "admin/app_dashboard.html", context)


_default_admin_get_urls = admin.site.get_urls


def _admin_get_urls_with_dashboard():
    custom_urls = [
        path("dashboard/", admin.site.admin_view(app_dashboard_view), name="application-dashboard"),
    ]
    return custom_urls + _default_admin_get_urls()


admin.site.get_urls = _admin_get_urls_with_dashboard
