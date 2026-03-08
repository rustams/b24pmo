from ...models import ApplicationInstallation
from ...utils import AuthorizedRequest


def upsert_installation(request: AuthorizedRequest) -> dict:
    bitrix24_account = request.bitrix24_account

    ApplicationInstallation.objects.update_or_create(
        bitrix_24_account=bitrix24_account,
        defaults={
            "status": bitrix24_account.status,
            "portal_license_family": "",
            "application_token": bitrix24_account.application_token,
        },
    )

    return {"message": "Installation successful"}


def issue_jwt(request: AuthorizedRequest) -> dict:
    return {"token": request.bitrix24_account.create_jwt_token()}
