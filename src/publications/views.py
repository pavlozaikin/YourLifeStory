from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import redirect_to_login
from django.http import HttpResponse
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from publications.forms import KeywordForm, PublicationForm
from publications.models import Keyword, Publication
from publications.utils import publication_download_filename, publication_markdown


def _publication_filters(queryset, request):
    term = request.GET.get("q", "").strip()
    keyword_id = request.GET.get("keyword", "").strip()
    if term:
        queryset = queryset.search(term)
    if keyword_id:
        queryset = queryset.with_keyword(keyword_id)
    return queryset.distinct()


class PublicationAccessMixin:
    model = Publication
    context_object_name = "publication"

    def get_queryset(self):
        return Publication.objects.select_related("owner").prefetch_related("keywords")

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.can_view(request.user):
            return super().dispatch(request, *args, **kwargs)
        if request.user.is_authenticated:
            raise Http404
        return redirect_to_login(request.get_full_path())

    def get_object(self, queryset=None):
        return get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])


class PublicationOwnerMixin(LoginRequiredMixin, UserPassesTestMixin):
    raise_exception = True

    def test_func(self):
        return self.get_object().can_edit(self.request.user)


class MyPublicationListView(LoginRequiredMixin, ListView):
    model = Publication
    template_name = "publications/publication_list.html"
    context_object_name = "publications"

    def get_queryset(self):
        queryset = (
            Publication.objects.owned_by(self.request.user)
            .select_related("owner")
            .prefetch_related("keywords")
        )
        return _publication_filters(queryset, self.request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["keywords"] = Keyword.objects.order_by("name")
        return context


class AllPublicationListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Publication
    template_name = "publications/publication_all_list.html"
    context_object_name = "publications"

    def test_func(self):
        return self.request.user.is_staff

    def get_queryset(self):
        queryset = Publication.objects.select_related("owner").prefetch_related("keywords")
        return _publication_filters(queryset, self.request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["keywords"] = Keyword.objects.order_by("name")
        return context


class PublicationDetailView(PublicationAccessMixin, DetailView):
    template_name = "publications/publication_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_edit"] = self.object.can_edit(self.request.user)
        return context


class PublicationDownloadView(PublicationAccessMixin, View):
    def get(self, request, *args, **kwargs):
        response = HttpResponse(
            publication_markdown(self.object),
            content_type="text/markdown; charset=utf-8",
        )
        response["Content-Disposition"] = (
            f'attachment; filename="{publication_download_filename(self.object)}"'
        )
        return response


class PublicationCreateView(LoginRequiredMixin, CreateView):
    model = Publication
    form_class = PublicationForm
    template_name = "publications/publication_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("publication-detail", kwargs={"pk": self.object.pk})


class PublicationUpdateView(PublicationOwnerMixin, UpdateView):
    model = Publication
    form_class = PublicationForm
    template_name = "publications/publication_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse_lazy("publication-detail", kwargs={"pk": self.object.pk})

    def get_object(self, queryset=None):
        return get_object_or_404(
            Publication.objects.select_related("owner").prefetch_related("keywords"),
            pk=self.kwargs["pk"],
        )


class PublicationDeleteView(PublicationOwnerMixin, DeleteView):
    model = Publication
    template_name = "publications/publication_confirm_delete.html"
    success_url = reverse_lazy("my-publications")

    def get_object(self, queryset=None):
        return get_object_or_404(
            Publication.objects.select_related("owner"),
            pk=self.kwargs["pk"],
        )


class KeywordListView(LoginRequiredMixin, ListView):
    model = Keyword
    template_name = "publications/keyword_list.html"
    context_object_name = "keywords"

    def get_queryset(self):
        return Keyword.objects.all().prefetch_related("publications")


class KeywordCreateView(LoginRequiredMixin, CreateView):
    model = Keyword
    form_class = KeywordForm
    template_name = "publications/keyword_form.html"
    success_url = reverse_lazy("keyword-list")


class KeywordUpdateView(LoginRequiredMixin, UpdateView):
    model = Keyword
    form_class = KeywordForm
    template_name = "publications/keyword_form.html"
    success_url = reverse_lazy("keyword-list")


class KeywordDeleteView(LoginRequiredMixin, DeleteView):
    model = Keyword
    template_name = "publications/keyword_confirm_delete.html"
    success_url = reverse_lazy("keyword-list")
