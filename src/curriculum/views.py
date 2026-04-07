from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import redirect_to_login
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from curriculum.forms import (
    CurriculumForm,
    CurriculumMembershipForm,
    CurriculumUserStateForm,
    LessonForm,
    LessonProgressForm,
    ResourceForm,
    TopicForm,
)
from curriculum.models import (
    Curriculum,
    CurriculumMembership,
    CurriculumUserState,
    Lesson,
    LessonProgress,
    Resource,
    Topic,
)


class CurriculumStructureAccessMixin:
    model = Curriculum
    context_object_name = "curriculum"

    def get_queryset(self):
        return Curriculum.objects.select_related("owner").prefetch_related(
            "memberships__user",
            "resources",
            "topics__lessons__resources",
        )

    def get_object(self, queryset=None):
        return get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.can_view_structure(request.user):
            return super().dispatch(request, *args, **kwargs)
        if request.user.is_authenticated:
            raise Http404
        return redirect_to_login(request.get_full_path())


class CurriculumEditAccessMixin(LoginRequiredMixin):
    model = Curriculum
    context_object_name = "curriculum"

    def get_queryset(self):
        return Curriculum.objects.select_related("owner")

    def get_object(self, queryset=None):
        return get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.can_edit_materials(request.user):
            return super().dispatch(request, *args, **kwargs)
        raise Http404


class TopicEditAccessMixin(LoginRequiredMixin):
    model = Topic
    context_object_name = "topic"

    def get_queryset(self):
        return Topic.objects.select_related("curriculum", "curriculum__owner")

    def get_object(self, queryset=None):
        return get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.curriculum.can_edit_materials(request.user):
            return super().dispatch(request, *args, **kwargs)
        raise Http404


class LessonMaterialAccessMixin:
    model = Lesson
    context_object_name = "lesson"

    def get_queryset(self):
        return Lesson.objects.select_related(
            "topic",
            "topic__curriculum",
            "topic__curriculum__owner",
        ).prefetch_related("resources")

    def get_object(self, queryset=None):
        return get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.curriculum.can_view_materials(request.user):
            return super().dispatch(request, *args, **kwargs)
        if request.user.is_authenticated:
            raise Http404
        return redirect_to_login(request.get_full_path())


class LessonEditAccessMixin(LoginRequiredMixin, LessonMaterialAccessMixin):
    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.curriculum.can_edit_materials(request.user):
            return super().dispatch(request, *args, **kwargs)
        raise Http404


class ResourceEditAccessMixin(LoginRequiredMixin):
    model = Resource
    context_object_name = "resource"

    def get_queryset(self):
        return Resource.objects.select_related(
            "curriculum",
            "lesson",
            "lesson__topic",
            "lesson__topic__curriculum",
        )

    def get_object(self, queryset=None):
        return get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        curriculum = self.object.target_curriculum
        if curriculum and curriculum.can_edit_materials(request.user):
            return super().dispatch(request, *args, **kwargs)
        raise Http404


class MembershipEditAccessMixin(LoginRequiredMixin):
    model = CurriculumMembership
    context_object_name = "membership"

    def get_queryset(self):
        return CurriculumMembership.objects.select_related("curriculum", "curriculum__owner", "user")

    def get_object(self, queryset=None):
        return get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.curriculum.can_manage_members(request.user):
            return super().dispatch(request, *args, **kwargs)
        raise Http404


class CurriculumListView(LoginRequiredMixin, ListView):
    model = Curriculum
    template_name = "curriculum/curriculum_list.html"
    context_object_name = "curricula"

    def get_queryset(self):
        return Curriculum.objects.visible_to(self.request.user).select_related("owner")


class CurriculumDetailView(CurriculumStructureAccessMixin, DetailView):
    template_name = "curriculum/curriculum_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        curriculum = self.object
        user = self.request.user
        role = curriculum.get_role(user)
        state = curriculum.get_study_state(user)
        topics = curriculum.topics.all().prefetch_related("lessons__resources")
        lesson_progress = {}
        if user.is_authenticated and curriculum.can_update_learning_state(user):
            lesson_progress = {
                progress.lesson_id: progress.get_status_display()
                for progress in LessonProgress.objects.filter(
                    lesson__topic__curriculum=curriculum,
                    user=user,
                )
            }
        context.update(
            {
                "role": role,
                "topics": topics,
                "study_state": state,
                "progress_percent": curriculum.progress_percent_for(user),
                "can_edit_materials": curriculum.can_edit_materials(user),
                "can_manage_members": curriculum.can_manage_members(user),
                "can_view_lesson_content": curriculum.can_view_materials(user),
                "can_enroll": user.is_authenticated and curriculum.can_view_materials(user) and state is None,
                "lesson_progress": lesson_progress,
                "memberships": curriculum.memberships.all(),
            }
        )
        return context


class CurriculumCreateView(LoginRequiredMixin, CreateView):
    model = Curriculum
    form_class = CurriculumForm
    template_name = "curriculum/curriculum_form.html"

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("curriculum:curriculum-detail", kwargs={"pk": self.object.pk})


class CurriculumUpdateView(CurriculumEditAccessMixin, UpdateView):
    form_class = CurriculumForm
    template_name = "curriculum/curriculum_form.html"

    def get_success_url(self):
        return reverse_lazy("curriculum:curriculum-detail", kwargs={"pk": self.object.pk})


class CurriculumDeleteView(CurriculumEditAccessMixin, DeleteView):
    template_name = "curriculum/curriculum_confirm_delete.html"
    success_url = reverse_lazy("curriculum:curriculum-list")


class TopicCreateView(CurriculumEditAccessMixin, CreateView):
    model = Topic
    form_class = TopicForm
    template_name = "curriculum/topic_form.html"

    def form_valid(self, form):
        form.instance.curriculum = self.get_object()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("curriculum:curriculum-detail", kwargs={"pk": self.object.curriculum.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["curriculum"] = self.object
        return context


class TopicUpdateView(TopicEditAccessMixin, UpdateView):
    form_class = TopicForm
    template_name = "curriculum/topic_form.html"

    def get_success_url(self):
        return reverse_lazy("curriculum:curriculum-detail", kwargs={"pk": self.object.curriculum.pk})


class TopicDeleteView(TopicEditAccessMixin, DeleteView):
    template_name = "curriculum/topic_confirm_delete.html"

    def get_success_url(self):
        return reverse_lazy("curriculum:curriculum-detail", kwargs={"pk": self.object.curriculum.pk})


class LessonDetailView(LessonMaterialAccessMixin, DetailView):
    template_name = "curriculum/lesson_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        curriculum = self.object.curriculum
        progress = None
        if curriculum.can_update_learning_state(self.request.user):
            progress, _ = LessonProgress.objects.get_or_create(
                lesson=self.object,
                user=self.request.user,
            )
        context["progress"] = progress
        context["can_edit_materials"] = curriculum.can_edit_materials(self.request.user)
        return context


class LessonCreateView(TopicEditAccessMixin, CreateView):
    model = Lesson
    form_class = LessonForm
    template_name = "curriculum/lesson_form.html"

    def form_valid(self, form):
        form.instance.topic = self.get_object()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("curriculum:curriculum-detail", kwargs={"pk": self.object.topic.curriculum.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["topic"] = self.object
        return context


class LessonUpdateView(LessonEditAccessMixin, UpdateView):
    form_class = LessonForm
    template_name = "curriculum/lesson_form.html"

    def get_success_url(self):
        return reverse_lazy("curriculum:lesson-detail", kwargs={"pk": self.object.pk})


class LessonDeleteView(LessonEditAccessMixin, DeleteView):
    template_name = "curriculum/lesson_confirm_delete.html"

    def get_success_url(self):
        return reverse_lazy("curriculum:curriculum-detail", kwargs={"pk": self.object.topic.curriculum.pk})


class CurriculumResourceCreateView(CurriculumEditAccessMixin, CreateView):
    model = Resource
    form_class = ResourceForm
    template_name = "curriculum/resource_form.html"

    def form_valid(self, form):
        form.instance.curriculum = self.get_object()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("curriculum:curriculum-detail", kwargs={"pk": self.object.curriculum.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["curriculum"] = self.object
        return context


class LessonResourceCreateView(LessonEditAccessMixin, CreateView):
    model = Resource
    form_class = ResourceForm
    template_name = "curriculum/resource_form.html"

    def form_valid(self, form):
        form.instance.lesson = self.get_object()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("curriculum:lesson-detail", kwargs={"pk": self.object.lesson.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["lesson"] = self.object
        return context


class ResourceUpdateView(ResourceEditAccessMixin, UpdateView):
    form_class = ResourceForm
    template_name = "curriculum/resource_form.html"

    def get_success_url(self):
        curriculum = self.object.target_curriculum
        if self.object.lesson_id:
            return reverse_lazy("curriculum:lesson-detail", kwargs={"pk": self.object.lesson.pk})
        return reverse_lazy("curriculum:curriculum-detail", kwargs={"pk": curriculum.pk})


class ResourceDeleteView(ResourceEditAccessMixin, DeleteView):
    template_name = "curriculum/resource_confirm_delete.html"

    def get_success_url(self):
        curriculum = self.object.target_curriculum
        if self.object.lesson_id:
            return reverse_lazy("curriculum:lesson-detail", kwargs={"pk": self.object.lesson.pk})
        return reverse_lazy("curriculum:curriculum-detail", kwargs={"pk": curriculum.pk})


class MembershipCreateView(CurriculumEditAccessMixin, CreateView):
    model = CurriculumMembership
    template_name = "curriculum/membership_form.html"

    def get_form_class(self):
        return CurriculumMembershipForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["curriculum"] = self.get_object()
        return kwargs

    def get_success_url(self):
        return reverse_lazy("curriculum:curriculum-detail", kwargs={"pk": self.object.curriculum.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["curriculum"] = self.object
        return context


class MembershipUpdateView(MembershipEditAccessMixin, UpdateView):
    template_name = "curriculum/membership_form.html"

    def get_form_class(self):
        return CurriculumMembershipForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["curriculum"] = self.object.curriculum
        return kwargs

    def get_success_url(self):
        return reverse_lazy("curriculum:curriculum-detail", kwargs={"pk": self.object.curriculum.pk})


class MembershipDeleteView(MembershipEditAccessMixin, DeleteView):
    template_name = "curriculum/membership_confirm_delete.html"

    def get_success_url(self):
        return reverse_lazy("curriculum:curriculum-detail", kwargs={"pk": self.object.curriculum.pk})


class CurriculumEnrollView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        curriculum = get_object_or_404(Curriculum.objects.select_related("owner"), pk=kwargs["pk"])
        if not curriculum.can_view_materials(request.user):
            raise Http404
        curriculum.enroll_user(request.user)
        return redirect("curriculum:curriculum-detail", pk=curriculum.pk)


class CurriculumUserStateUpdateView(LoginRequiredMixin, UpdateView):
    form_class = CurriculumUserStateForm
    template_name = "curriculum/user_state_form.html"

    def get_object(self, queryset=None):
        curriculum = get_object_or_404(Curriculum.objects.select_related("owner"), pk=self.kwargs["pk"])
        if not curriculum.can_update_learning_state(self.request.user):
            raise Http404
        return curriculum.get_study_state(self.request.user)

    def get_success_url(self):
        return reverse_lazy("curriculum:curriculum-detail", kwargs={"pk": self.object.curriculum.pk})


class LessonProgressUpdateView(LoginRequiredMixin, UpdateView):
    form_class = LessonProgressForm
    template_name = "curriculum/lesson_progress_form.html"

    def get_object(self, queryset=None):
        lesson = get_object_or_404(
            Lesson.objects.select_related("topic", "topic__curriculum", "topic__curriculum__owner"),
            pk=self.kwargs["pk"],
        )
        if not lesson.curriculum.can_update_learning_state(self.request.user):
            raise Http404
        progress, _ = LessonProgress.objects.get_or_create(lesson=lesson, user=self.request.user)
        return progress

    def get_success_url(self):
        return reverse_lazy("curriculum:lesson-detail", kwargs={"pk": self.object.lesson.pk})
