from django.urls import include, path
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


@api_view(["GET"])
def api_root(_request):
    return Response({"status": "ok", "message": "kiosk api scaffold ready"})


urlpatterns = [
    path("auth/token/", TokenObtainPairView.as_view(), name="token-obtain-pair"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("kiosk/", include("kiosk_api.urls")),
    path("", api_root, name="api-root"),
]
