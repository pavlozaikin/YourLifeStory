from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import redirect_to_login
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, FormView, ListView, TemplateView, UpdateView

from core.forms import PostForm, SignUpForm
from core.models import Post, SiteSettings
from journal.models import Journal
from publications.models import Publication


class PublicFeedView(TemplateView):
    template_name = "core/public_feed.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["publications"] = (
            Publication.objects.public_feed()
            .select_related("owner")
            .prefetch_related("keywords")
        )
        context["posts"] = Post.objects.visible_to(self.request.user).select_related("owner")
        return context


class PostAccessMixin:
    model = Post
    context_object_name = "post"

    def get_queryset(self):
        return Post.objects.select_related("owner")

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.can_view(request.user):
            return super().dispatch(request, *args, **kwargs)
        if request.user.is_authenticated:
            raise Http404
        return redirect_to_login(request.get_full_path())

    def get_object(self, queryset=None):
        return self.get_queryset().get(pk=self.kwargs["pk"])


class PostOwnerMixin(LoginRequiredMixin, UserPassesTestMixin):
    raise_exception = True

    def test_func(self):
        return self.get_object().can_edit(self.request.user)


class MyPostListView(LoginRequiredMixin, ListView):
    model = Post
    template_name = "core/post_list.html"
    context_object_name = "posts"

    def get_queryset(self):
        term = self.request.GET.get("q", "").strip()
        queryset = Post.objects.owned_by(self.request.user).select_related("owner")
        return queryset.search(term)


class PostDetailView(PostAccessMixin, DetailView):
    template_name = "core/post_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_edit"] = self.object.can_edit(self.request.user)
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = "core/post_form.html"

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("post-detail", kwargs={"pk": self.object.pk})


class PostUpdateView(PostOwnerMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = "core/post_form.html"

    def get_success_url(self):
        return reverse_lazy("post-detail", kwargs={"pk": self.object.pk})

    def get_object(self, queryset=None):
        return Post.objects.select_related("owner").get(pk=self.kwargs["pk"])


class PostDeleteView(PostOwnerMixin, DeleteView):
    model = Post
    template_name = "core/post_confirm_delete.html"
    success_url = reverse_lazy("post-list")

    def get_object(self, queryset=None):
        return Post.objects.select_related("owner").get(pk=self.kwargs["pk"])


class SignUpView(FormView):
    form_class = SignUpForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("workspace")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("workspace")
        if not SiteSettings.get_solo().self_signup_enabled:
            raise Http404("Signup is disabled.")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        Journal.objects.get_or_create_personal_journal(user)
        login(self.request, user)
        messages.success(self.request, "Your account has been created.")
        return super().form_valid(form)


feed = PublicFeedView.as_view()


@login_required
def workspace(request):
    return render(request, "core/workspace.html", {"site_settings": SiteSettings.get_solo()})


signup = SignUpView.as_view()
