from django.urls import path

from journal.views import (
    JournalCreateView,
    JournalDeleteView,
    JournalDetailView,
    JournalEntryCreateView,
    JournalEntryDeleteView,
    JournalEntryDetailView,
    JournalEntryDownloadView,
    JournalEntryUpdateView,
    JournalListView,
    JournalUpdateView,
)


app_name = "journal"

urlpatterns = [
    path("", JournalListView.as_view(), name="journal-list"),
    path("create/", JournalCreateView.as_view(), name="journal-create"),
    path("<int:pk>/", JournalDetailView.as_view(), name="journal-detail"),
    path("<int:pk>/edit/", JournalUpdateView.as_view(), name="journal-edit"),
    path("<int:pk>/delete/", JournalDeleteView.as_view(), name="journal-delete"),
    path("entries/create/", JournalEntryCreateView.as_view(), name="journal-entry-create"),
    path("entries/<int:pk>/", JournalEntryDetailView.as_view(), name="journal-entry-detail"),
    path("entries/<int:pk>/download/", JournalEntryDownloadView.as_view(), name="journal-entry-download"),
    path("entries/<int:pk>/edit/", JournalEntryUpdateView.as_view(), name="journal-entry-edit"),
    path("entries/<int:pk>/delete/", JournalEntryDeleteView.as_view(), name="journal-entry-delete"),
]
