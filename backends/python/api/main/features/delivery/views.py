from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.views.decorators.clickjacking import xframe_options_exempt

from ...utils.decorators import auth_required, log_errors
from ...utils import AuthorizedRequest
from .services import (
    milestones_overview_payload,
    portfolios_overview_payload,
    programs_overview_payload,
    projects_overview_payload,
)


@xframe_options_exempt
@require_GET
@log_errors("portfolios_overview")
@auth_required
def portfolios_overview(request: AuthorizedRequest):
    return JsonResponse(portfolios_overview_payload())


@xframe_options_exempt
@require_GET
@log_errors("programs_overview")
@auth_required
def programs_overview(request: AuthorizedRequest):
    return JsonResponse(programs_overview_payload())


@xframe_options_exempt
@require_GET
@log_errors("projects_overview")
@auth_required
def projects_overview(request: AuthorizedRequest):
    return JsonResponse(projects_overview_payload())


@xframe_options_exempt
@require_GET
@log_errors("milestones_overview")
@auth_required
def milestones_overview(request: AuthorizedRequest):
    return JsonResponse(milestones_overview_payload())
