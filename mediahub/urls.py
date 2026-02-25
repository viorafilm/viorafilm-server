from django.urls import path

from .views import SharePublicPageView

urlpatterns = [
    path("<str:token>", SharePublicPageView.as_view(), name="mediahub-share-page"),
    path("<str:token>/", SharePublicPageView.as_view(), name="mediahub-share-page-slash"),
]

