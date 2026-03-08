from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.clickjacking import xframe_options_exempt

from ...utils.decorators import auth_required, log_errors
from ...utils import AuthorizedRequest
from .services import run_initial_sync_payload, sync_status_payload


@xframe_options_exempt
@require_GET
@log_errors("sync_status")
@auth_required
def sync_status(request: AuthorizedRequest):
    return JsonResponse(sync_status_payload())


@xframe_options_exempt
@csrf_exempt
@require_POST
@log_errors("run_initial_sync")
@auth_required
def run_initial_sync(request: AuthorizedRequest):
    return JsonResponse(run_initial_sync_payload())
