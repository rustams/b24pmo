from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.views.decorators.clickjacking import xframe_options_exempt

from ...utils.decorators import auth_required, log_errors
from ...utils import AuthorizedRequest
from .services import risks_overview_payload


@xframe_options_exempt
@require_GET
@log_errors("risks_overview")
@auth_required
def risks_overview(request: AuthorizedRequest):
    return JsonResponse(risks_overview_payload())
