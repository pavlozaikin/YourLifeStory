from django.urls import path

from . import views


urlpatterns = [
    path("", views.feed, name="public-feed"),
    path("feed/", views.feed, name="feed"),
    path("workspace/", views.workspace, name="workspace"),
    path("accounts/signup/", views.signup, name="signup"),
]
