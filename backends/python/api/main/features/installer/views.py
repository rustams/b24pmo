from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.clickjacking import xframe_options_exempt

from ...utils.decorators import auth_required, log_errors
from ...utils import AuthorizedRequest
from .services import (
    issue_jwt,
    upsert_installation,
    get_installation_context,
    get_installer_contract,
    get_installer_mapping,
    save_installer_mapping,
    get_scope_check,
    get_installer_setup_state,
    save_installer_setup_state,
)


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


@xframe_options_exempt
@csrf_exempt
@require_GET
@log_errors("installation_context")
@auth_required
def installation_context(request: AuthorizedRequest):
    return JsonResponse(get_installation_context(request))


@xframe_options_exempt
@csrf_exempt
@require_GET
@log_errors("installer_contract")
@auth_required
def installer_contract(request: AuthorizedRequest):
    return JsonResponse(get_installer_contract())


@xframe_options_exempt
@csrf_exempt
@require_GET
@log_errors("installer_mapping_get")
@auth_required
def installer_mapping_get(request: AuthorizedRequest):
    return JsonResponse(get_installer_mapping(request))


@xframe_options_exempt
@csrf_exempt
@require_POST
@log_errors("installer_mapping_save")
@auth_required
def installer_mapping_save(request: AuthorizedRequest):
    return JsonResponse(save_installer_mapping(request))


@xframe_options_exempt
@csrf_exempt
@require_GET
@log_errors("installer_scope_check")
@auth_required
def installer_scope_check(request: AuthorizedRequest):
    return JsonResponse(get_scope_check(request))


@xframe_options_exempt
@csrf_exempt
@require_GET
@log_errors("installer_setup_state_get")
@auth_required
def installer_setup_state_get(request: AuthorizedRequest):
    return JsonResponse(get_installer_setup_state(request))


@xframe_options_exempt
@csrf_exempt
@require_POST
@log_errors("installer_setup_state_save")
@auth_required
def installer_setup_state_save(request: AuthorizedRequest):
    return JsonResponse(save_installer_setup_state(request))
