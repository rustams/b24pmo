from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.views.decorators.clickjacking import xframe_options_exempt

from ...utils.decorators import auth_required, log_errors
from ...utils import AuthorizedRequest
from .services import budget_transactions_overview_payload


@xframe_options_exempt
@require_GET
@log_errors("budget_transactions_overview")
@auth_required
def budget_transactions_overview(request: AuthorizedRequest):
    return JsonResponse(budget_transactions_overview_payload())
