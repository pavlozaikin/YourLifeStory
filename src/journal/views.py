from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from journal.forms import JournalEntryForm
from journal.models import Journal, JournalEntry


class JournalEntryListView(LoginRequiredMixin, ListView):
    model = JournalEntry
    template_name = "journal/journalentry_list.html"
    context_object_name = "entries"

    def get_journal(self):
        if not hasattr(self, "_journal"):
            self._journal = Journal.objects.get_or_create_for_user(self.request.user)
        return self._journal

    def get_queryset(self):
        journal = self.get_journal()
        return journal.entries.select_related("journal", "journal__owner").all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["journal"] = self.get_journal()
        return context


class JournalEntryAccessMixin(LoginRequiredMixin):
    model = JournalEntry
    context_object_name = "entry"

    def get_queryset(self):
        return JournalEntry.objects.select_related("journal", "journal__owner").for_user(
            self.request.user
        )

    def get_object(self, queryset=None):
        return get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])


class JournalEntryDetailView(JournalEntryAccessMixin, DetailView):
    template_name = "journal/journalentry_detail.html"


class JournalEntryCreateView(LoginRequiredMixin, CreateView):
    model = JournalEntry
    form_class = JournalEntryForm
    template_name = "journal/journalentry_form.html"

    def get_journal(self):
        if not hasattr(self, "_journal"):
            self._journal = Journal.objects.get_or_create_for_user(self.request.user)
        return self._journal

    def form_valid(self, form):
        form.instance.journal = self.get_journal()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("journal:journal-entry-detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["journal"] = self.get_journal()
        return context


class JournalEntryUpdateView(JournalEntryAccessMixin, UpdateView):
    form_class = JournalEntryForm
    template_name = "journal/journalentry_form.html"

    def get_success_url(self):
        return reverse_lazy("journal:journal-entry-detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["journal"] = self.object.journal
        return context


class JournalEntryDeleteView(JournalEntryAccessMixin, DeleteView):
    template_name = "journal/journalentry_confirm_delete.html"
    success_url = reverse_lazy("journal:journal-list")
