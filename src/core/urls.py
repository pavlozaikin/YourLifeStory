from django.urls import path

from . import views


urlpatterns = [
    path("", views.feed, name="public-feed"),
    path("feed/", views.feed, name="feed"),
    path("workspace/", views.workspace, name="workspace"),
    path("accounts/signup/", views.signup, name="signup"),
    path("posts/", views.MyPostListView.as_view(), name="post-list"),
    path("posts/create/", views.PostCreateView.as_view(), name="post-create"),
    path("posts/<int:pk>/", views.PostDetailView.as_view(), name="post-detail"),
    path("posts/<int:pk>/edit/", views.PostUpdateView.as_view(), name="post-edit"),
    path("posts/<int:pk>/delete/", views.PostDeleteView.as_view(), name="post-delete"),
]
