from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.views.decorators.clickjacking import xframe_options_exempt

from ...utils.decorators import auth_required, log_errors
from ...utils import AuthorizedRequest
from .services import (
    get_enum_options,
    get_health_payload,
    get_list_elements,
    get_root_payload,
)


@xframe_options_exempt
@require_GET
@log_errors("root")
@auth_required
def root(request: AuthorizedRequest):
    return JsonResponse(get_root_payload())


@xframe_options_exempt
@require_GET
@log_errors("health")
@auth_required
def health(request: AuthorizedRequest):
    return JsonResponse(get_health_payload())


@xframe_options_exempt
@require_GET
@log_errors("get_enum")
@auth_required
def get_enum(request: AuthorizedRequest):
    return JsonResponse(get_enum_options(), safe=False)


@xframe_options_exempt
@require_GET
@log_errors("get_list")
@auth_required
def get_list(request: AuthorizedRequest):
    return JsonResponse(get_list_elements(), safe=False)
