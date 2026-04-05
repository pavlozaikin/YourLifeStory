app_name = "publications"

from django.urls import path

from publications.views import (
    AllPublicationListView,
    KeywordCreateView,
    KeywordDeleteView,
    KeywordListView,
    KeywordUpdateView,
    MyPublicationListView,
    PublicationCreateView,
    PublicationDeleteView,
    PublicationDownloadView,
    PublicationDetailView,
    PublicationUpdateView,
)


urlpatterns = [
    path("", MyPublicationListView.as_view(), name="my-publications"),
    path("", MyPublicationListView.as_view(), name="my-list"),
    path("all/", AllPublicationListView.as_view(), name="publication-all"),
    path("all/", AllPublicationListView.as_view(), name="all-list"),
    path("create/", PublicationCreateView.as_view(), name="publication-create"),
    path("create/", PublicationCreateView.as_view(), name="create"),
    path("<int:pk>/", PublicationDetailView.as_view(), name="publication-detail"),
    path("<int:pk>/", PublicationDetailView.as_view(), name="detail"),
    path("<int:pk>/download/", PublicationDownloadView.as_view(), name="publication-download"),
    path("<int:pk>/edit/", PublicationUpdateView.as_view(), name="publication-edit"),
    path("<int:pk>/edit/", PublicationUpdateView.as_view(), name="edit"),
    path("<int:pk>/delete/", PublicationDeleteView.as_view(), name="publication-delete"),
    path("<int:pk>/delete/", PublicationDeleteView.as_view(), name="delete"),
    path("keywords/", KeywordListView.as_view(), name="keyword-list"),
    path("keywords/create/", KeywordCreateView.as_view(), name="keyword-create"),
    path("keywords/<int:pk>/edit/", KeywordUpdateView.as_view(), name="keyword-edit"),
    path("keywords/<int:pk>/delete/", KeywordDeleteView.as_view(), name="keyword-delete"),
]
