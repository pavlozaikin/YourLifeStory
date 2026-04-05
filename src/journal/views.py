from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import redirect_to_login
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from journal.forms import JournalEntryForm, JournalForm
from journal.models import Journal, JournalEntry


class JournalOwnershipMixin:
    def ensure_personal_journal(self):
        return Journal.objects.get_or_create_personal_journal(self.request.user)


class JournalListView(LoginRequiredMixin, JournalOwnershipMixin, ListView):
    model = Journal
    template_name = "journal/journal_list.html"
    context_object_name = "journals"

    def get_queryset(self):
        self.ensure_personal_journal()
        return Journal.objects.for_user(self.request.user).prefetch_related("entries")


class JournalAccessMixin(LoginRequiredMixin, JournalOwnershipMixin):
    model = Journal
    context_object_name = "journal"

    def get_queryset(self):
        return Journal.objects.for_user(self.request.user).prefetch_related("entries")

    def get_object(self, queryset=None):
        return get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])


class JournalDetailView(JournalAccessMixin, DetailView):
    template_name = "journal/journal_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entries"] = self.object.entries.prefetch_related("journals", "shared_with")
        context["create_entry_journal"] = self.object
        return context


class JournalCreateView(LoginRequiredMixin, JournalOwnershipMixin, CreateView):
    model = Journal
    form_class = JournalForm
    template_name = "journal/journal_form.html"

    def form_valid(self, form):
        form.instance.owner = self.request.user
        form.instance.is_personal = False
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("journal:journal-detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["personal_journal"] = self.ensure_personal_journal()
        return context


class JournalUpdateView(JournalAccessMixin, UpdateView):
    form_class = JournalForm
    template_name = "journal/journal_form.html"

    def get_success_url(self):
        return reverse_lazy("journal:journal-detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["personal_journal"] = self.ensure_personal_journal()
        return context


class JournalDeleteView(JournalAccessMixin, DeleteView):
    template_name = "journal/journal_confirm_delete.html"
    success_url = reverse_lazy("journal:journal-list")

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.can_delete(request.user):
            if request.user.is_authenticated:
                raise Http404
            return redirect_to_login(request.get_full_path())
        return super().dispatch(request, *args, **kwargs)


class JournalEntryPermissionMixin:
    model = JournalEntry
    context_object_name = "entry"
    permission_method = "can_view"

    def get_queryset(self):
        return JournalEntry.objects.prefetch_related("journals", "shared_with")

    def get_object(self, queryset=None):
        return get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if getattr(self.object, self.permission_method)(request.user):
            return super().dispatch(request, *args, **kwargs)
        if request.user.is_authenticated:
            raise Http404
        return redirect_to_login(request.get_full_path())


class JournalEntryCreateView(LoginRequiredMixin, JournalOwnershipMixin, CreateView):
    model = JournalEntry
    form_class = JournalEntryForm
    template_name = "journal/journalentry_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        journal_id = self.request.GET.get("journal")
        if journal_id:
            journal = Journal.objects.filter(owner=self.request.user, pk=journal_id).first()
            personal_journal = self.ensure_personal_journal()
            if journal and not journal.is_personal:
                initial["journals"] = [journal]
            else:
                initial["journals"] = []
            initial["personal_journal"] = personal_journal
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        journal_id = self.request.GET.get("journal")
        context["journal"] = Journal.objects.filter(
            owner=self.request.user,
            pk=journal_id,
        ).first() or self.ensure_personal_journal()
        context["personal_journal"] = self.ensure_personal_journal()
        return context

    def get_success_url(self):
        return reverse_lazy("journal:journal-entry-detail", kwargs={"pk": self.object.pk})


class JournalEntryDetailView(JournalEntryPermissionMixin, DetailView):
    template_name = "journal/journalentry_detail.html"


class JournalEntryDownloadView(JournalEntryPermissionMixin, View):
    permission_method = "can_view"

    def get(self, request, *args, **kwargs):
        response = HttpResponse(self.object.to_markdown(), content_type="text/markdown; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="{self.object.export_filename()}"'
        return response


class JournalEntryUpdateView(JournalEntryPermissionMixin, UpdateView):
    form_class = JournalEntryForm
    template_name = "journal/journalentry_form.html"
    permission_method = "can_edit"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        personal_journal = self.object.journals.filter(is_personal=True).first()
        context["journal"] = personal_journal or self.object.journals.first()
        context["personal_journal"] = personal_journal
        return context

    def get_success_url(self):
        return reverse_lazy("journal:journal-entry-detail", kwargs={"pk": self.object.pk})


class JournalEntryDeleteView(JournalEntryPermissionMixin, DeleteView):
    template_name = "journal/journalentry_confirm_delete.html"
    success_url = reverse_lazy("journal:journal-list")
    permission_method = "can_edit"
