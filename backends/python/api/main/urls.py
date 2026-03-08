from django.urls import path

from .features.common.views import root, health, get_enum, get_list
from .features.installer.views import install, get_token
from .features.strategy.views import goals_overview, initiatives_overview
from .features.delivery.views import (
    portfolios_overview,
    programs_overview,
    projects_overview,
    milestones_overview,
)
from .features.resources.views import allocations_overview, capacity_overview
from .features.risks.views import risks_overview
from .features.budget.views import budget_transactions_overview
from .features.meetings.views import meetings_overview
from .features.sync.views import sync_status, run_initial_sync
from .features.rbac.views import roles_overview

urlpatterns = [
    # Legacy/health endpoints
    path("api", root, name="root"),
    path("api/health", health, name="health"),
    path("api/enum", get_enum, name="enum"),
    path("api/list", get_list, name="list"),
    path("api/install", install, name="install"),
    path("api/getToken", get_token, name="get_token"),

    # PMO feature endpoints (scaffold)
    path("api/pmo/goals", goals_overview, name="pmo_goals"),
    path("api/pmo/initiatives", initiatives_overview, name="pmo_initiatives"),
    path("api/pmo/portfolios", portfolios_overview, name="pmo_portfolios"),
    path("api/pmo/programs", programs_overview, name="pmo_programs"),
    path("api/pmo/projects", projects_overview, name="pmo_projects"),
    path("api/pmo/milestones", milestones_overview, name="pmo_milestones"),
    path("api/pmo/resources/allocations", allocations_overview, name="pmo_allocations"),
    path("api/pmo/resources/capacity", capacity_overview, name="pmo_capacity"),
    path("api/pmo/risks", risks_overview, name="pmo_risks"),
    path("api/pmo/budgets/transactions", budget_transactions_overview, name="pmo_budget_transactions"),
    path("api/pmo/meetings", meetings_overview, name="pmo_meetings"),
    path("api/pmo/sync/status", sync_status, name="pmo_sync_status"),
    path("api/pmo/sync/run-initial", run_initial_sync, name="pmo_sync_run_initial"),
    path("api/pmo/rbac/roles", roles_overview, name="pmo_rbac_roles"),
]
