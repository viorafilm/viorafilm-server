from django.urls import path

from .views import share_page

urlpatterns = [
    path("s/<str:token>", share_page, name="share_page_noslash"),
    path("s/<str:token>/", share_page, name="share_page"),
]
