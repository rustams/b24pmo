from django.utils import timezone


def get_root_payload() -> dict:
    return {"message": "Python Backend is running"}


def get_health_payload() -> dict:
    return {
        "status": "healthy",
        "backend": "python",
        "timestamp": timezone.now().timestamp(),
    }


def get_enum_options() -> list[str]:
    return ["option 1", "option 2", "option 3"]


def get_list_elements() -> list[str]:
    return ["element 1", "element 2", "element 3"]
