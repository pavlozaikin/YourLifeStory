from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from core.models import Post
from core.widgets import MarkdownTextarea


class SignUpForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username",)


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ("title", "content", "visibility")
        widgets = {
            "title": forms.TextInput(attrs={"size": 60}),
            "content": MarkdownTextarea(),
        }
