from django.urls import path

from .views import KioskShareCompleteAPIView, KioskShareCreateAPIView

urlpatterns = [
    path("create", KioskShareCreateAPIView.as_view(), name="kiosk-share-create"),
    path("create/", KioskShareCreateAPIView.as_view(), name="kiosk-share-create-slash"),
    path("complete", KioskShareCompleteAPIView.as_view(), name="kiosk-share-complete"),
    path("complete/", KioskShareCompleteAPIView.as_view(), name="kiosk-share-complete-slash"),
]

