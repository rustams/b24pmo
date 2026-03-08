from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.decorators.clickjacking import xframe_options_exempt

from ...utils.decorators import auth_required, log_errors
from ...utils import AuthorizedRequest
from .services import issue_jwt, upsert_installation


@xframe_options_exempt
@csrf_exempt
@require_POST
@log_errors("install")
@auth_required
def install(request: AuthorizedRequest):
    return JsonResponse(upsert_installation(request))


@xframe_options_exempt
@csrf_exempt
@require_POST
@log_errors("get_token")
@auth_required
def get_token(request: AuthorizedRequest):
    return JsonResponse(issue_jwt(request))
