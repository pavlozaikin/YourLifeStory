from django import forms
from django.contrib.auth import get_user_model

from core.widgets import MarkdownTextarea
from curriculum.models import (
    Curriculum,
    CurriculumMembership,
    CurriculumUserState,
    Lesson,
    LessonProgress,
    Resource,
    Topic,
)


User = get_user_model()


class CurriculumForm(forms.ModelForm):
    class Meta:
        model = Curriculum
        fields = ["title", "code", "goal", "expected_results", "visibility", "deadline"]
        widgets = {
            "title": forms.TextInput(attrs={"size": 60}),
            "code": forms.TextInput(attrs={"size": 30}),
            "goal": forms.Textarea(attrs={"rows": 4}),
            "expected_results": forms.Textarea(attrs={"rows": 5}),
            "deadline": forms.DateInput(attrs={"type": "date"}),
        }
        help_texts = {
            "code": "Optional. Leave blank to generate a unique code automatically.",
        }


class TopicForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ["title", "summary", "position"]
        widgets = {
            "title": forms.TextInput(attrs={"size": 60}),
            "summary": forms.Textarea(attrs={"rows": 4}),
        }


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ["title", "content", "deadline", "position"]
        widgets = {
            "title": forms.TextInput(attrs={"size": 60}),
            "content": MarkdownTextarea(),
            "deadline": forms.DateInput(attrs={"type": "date"}),
        }


class ResourceForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = ["title", "url", "notes", "position"]
        widgets = {
            "title": forms.TextInput(attrs={"size": 60}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class CurriculumMembershipForm(forms.ModelForm):
    class Meta:
        model = CurriculumMembership
        fields = ["user", "role"]

    def __init__(self, *args, **kwargs):
        curriculum = kwargs.pop("curriculum")
        super().__init__(*args, **kwargs)
        self.curriculum = curriculum
        used_users = curriculum.memberships.exclude(pk=getattr(self.instance, "pk", None)).values_list(
            "user_id", flat=True
        )
        self.fields["user"].queryset = User.objects.exclude(pk__in=list(used_users) + [curriculum.owner_id])

    def save(self, commit=True):
        membership = super().save(commit=False)
        membership.curriculum = self.curriculum
        if commit:
            membership.save()
        return membership


class CurriculumUserStateForm(forms.ModelForm):
    class Meta:
        model = CurriculumUserState
        fields = ["status"]


class LessonProgressForm(forms.ModelForm):
    class Meta:
        model = LessonProgress
        fields = ["status"]

