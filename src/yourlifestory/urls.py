"""
URL configuration for yourlifestory project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path

from core import views as core_views
from publications import views as publication_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", core_views.feed, name="public-feed"),
    path("feed/", core_views.feed, name="feed"),
    path("workspace/", core_views.workspace, name="workspace"),
    path("accounts/signup/", core_views.signup, name="signup"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("journal/", include(("journal.urls", "journal"), namespace="journal")),
    path("publications/", publication_views.MyPublicationListView.as_view(), name="my-publications"),
    path("publications/all/", publication_views.AllPublicationListView.as_view(), name="publication-all"),
    path("publications/create/", publication_views.PublicationCreateView.as_view(), name="publication-create"),
    path("publications/<int:pk>/", publication_views.PublicationDetailView.as_view(), name="publication-detail"),
    path("publications/<int:pk>/edit/", publication_views.PublicationUpdateView.as_view(), name="publication-edit"),
    path("publications/<int:pk>/delete/", publication_views.PublicationDeleteView.as_view(), name="publication-delete"),
    path("publications/keywords/", publication_views.KeywordListView.as_view(), name="keyword-list"),
    path("publications/keywords/create/", publication_views.KeywordCreateView.as_view(), name="keyword-create"),
    path("publications/keywords/<int:pk>/edit/", publication_views.KeywordUpdateView.as_view(), name="keyword-edit"),
    path("publications/keywords/<int:pk>/delete/", publication_views.KeywordDeleteView.as_view(), name="keyword-delete"),
]
