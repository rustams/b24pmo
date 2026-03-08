from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.views.decorators.clickjacking import xframe_options_exempt

from ...utils.decorators import auth_required, log_errors
from ...utils import AuthorizedRequest
from .services import allocations_overview_payload, capacity_overview_payload


@xframe_options_exempt
@require_GET
@log_errors("allocations_overview")
@auth_required
def allocations_overview(request: AuthorizedRequest):
    return JsonResponse(allocations_overview_payload())


@xframe_options_exempt
@require_GET
@log_errors("capacity_overview")
@auth_required
def capacity_overview(request: AuthorizedRequest):
    return JsonResponse(capacity_overview_payload())
