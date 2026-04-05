from django.urls import path

from journal.views import (
    JournalEntryCreateView,
    JournalEntryDeleteView,
    JournalEntryDetailView,
    JournalEntryListView,
    JournalEntryUpdateView,
)


app_name = "journal"

urlpatterns = [
    path("", JournalEntryListView.as_view(), name="journal-list"),
    path("entries/create/", JournalEntryCreateView.as_view(), name="journal-entry-create"),
    path("entries/<int:pk>/", JournalEntryDetailView.as_view(), name="journal-entry-detail"),
    path(
        "entries/<int:pk>/edit/",
        JournalEntryUpdateView.as_view(),
        name="journal-entry-edit",
    ),
    path(
        "entries/<int:pk>/delete/",
        JournalEntryDeleteView.as_view(),
        name="journal-entry-delete",
    ),
]

