from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.views.decorators.clickjacking import xframe_options_exempt

from ...utils.decorators import auth_required, log_errors
from ...utils import AuthorizedRequest
from .services import meetings_overview_payload


@xframe_options_exempt
@require_GET
@log_errors("meetings_overview")
@auth_required
def meetings_overview(request: AuthorizedRequest):
    return JsonResponse(meetings_overview_payload())
