from .ui import build_dashboard_ui


def dashboard_ui(request):
    return {
        "dashboard_ui": build_dashboard_ui(request),
    }
