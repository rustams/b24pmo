from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.views.decorators.clickjacking import xframe_options_exempt

from ...utils.decorators import auth_required, log_errors
from ...utils import AuthorizedRequest
from .services import goals_overview_payload, initiatives_overview_payload


@xframe_options_exempt
@require_GET
@log_errors("goals_overview")
@auth_required
def goals_overview(request: AuthorizedRequest):
    return JsonResponse(goals_overview_payload())


@xframe_options_exempt
@require_GET
@log_errors("initiatives_overview")
@auth_required
def initiatives_overview(request: AuthorizedRequest):
    return JsonResponse(initiatives_overview_payload())
