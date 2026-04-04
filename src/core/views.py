from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView

from core.forms import SignUpForm
from core.models import SiteSettings
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
        return context


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
        login(self.request, user)
        messages.success(self.request, "Your account has been created.")
        return super().form_valid(form)


feed = PublicFeedView.as_view()


@login_required
def workspace(request):
    return render(request, "core/workspace.html", {"site_settings": SiteSettings.get_solo()})


signup = SignUpView.as_view()
