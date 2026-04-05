import re

from django import forms

from core.widgets import MarkdownTextarea
from publications.models import Keyword, Publication


class PublicationForm(forms.ModelForm):
    keywords = forms.ModelMultipleChoiceField(
        queryset=Keyword.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    new_keywords = forms.CharField(
        required=False,
        label="New keywords",
        help_text="Add comma-separated keywords and they will be created automatically.",
    )

    class Meta:
        model = Publication
        fields = ["title", "content", "status", "visibility", "keywords"]
        widgets = {
            "title": forms.TextInput(attrs={"size": 60}),
            "content": MarkdownTextarea(),
        }

    def __init__(self, *args, **kwargs):
        kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.fields["keywords"].queryset = Keyword.objects.order_by("name")

    def _resolve_keywords(self):
        keywords = list(self.cleaned_data.get("keywords", []))
        new_keywords = self.cleaned_data.get("new_keywords", "")
        for raw_name in re.split(r"[,\n]", new_keywords):
            name = raw_name.strip()
            if not name:
                continue
            keyword, _ = Keyword.objects.get_or_create(name=name)
            keywords.append(keyword)
        unique_keywords = []
        seen_ids = set()
        for keyword in keywords:
            if keyword.pk in seen_ids:
                continue
            seen_ids.add(keyword.pk)
            unique_keywords.append(keyword)
        return unique_keywords

    def save(self, commit=True):
        publication = super().save(commit=False)
        if commit:
            publication.save()
            publication.keywords.set(self._resolve_keywords())
        return publication


class KeywordForm(forms.ModelForm):
    class Meta:
        model = Keyword
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(attrs={"size": 40}),
        }
