from django import forms
from django.contrib.auth import get_user_model

from core.widgets import MarkdownTextarea
from journal.models import Journal, JournalEntry


User = get_user_model()


class JournalForm(forms.ModelForm):
    class Meta:
        model = Journal
        fields = ["title"]
        widgets = {
            "title": forms.TextInput(attrs={"size": 60}),
        }


class JournalEntryForm(forms.ModelForm):
    journals = forms.ModelMultipleChoiceField(
        queryset=Journal.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Additional journals",
    )
    shared_with = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = JournalEntry
        fields = ["title", "content", "visibility", "shared_with", "journals"]
        widgets = {
            "title": forms.TextInput(attrs={"size": 60}),
            "content": MarkdownTextarea(),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if self.user and self.user.is_authenticated:
            personal_journal = Journal.objects.get_or_create_personal_journal(self.user)
            self.personal_journal = personal_journal
            self.fields["journals"].queryset = Journal.objects.for_user(self.user).exclude(
                pk=personal_journal.pk
            )
            self.fields["shared_with"].queryset = User.objects.all()
        else:
            self.personal_journal = None
            self.fields["journals"].queryset = Journal.objects.none()
            self.fields["shared_with"].queryset = User.objects.none()

        if self.instance and self.instance.pk:
            self.fields["journals"].initial = self.instance.journals.exclude(
                pk=getattr(self.personal_journal, "pk", None)
            )

    def clean(self):
        cleaned_data = super().clean()
        visibility = cleaned_data.get("visibility")
        shared_with = cleaned_data.get("shared_with")
        if shared_with and visibility != JournalEntry.Visibility.SHARED:
            cleaned_data["visibility"] = JournalEntry.Visibility.SHARED
        if cleaned_data.get("visibility") == JournalEntry.Visibility.SHARED and not shared_with:
            self.add_error("shared_with", "Select at least one user for a shared entry.")
        return cleaned_data

    def save(self, commit=True):
        is_new = self.instance.pk is None
        should_keep_personal_journal = bool(
            self.personal_journal
            and (
                is_new
                or self.instance.journals.filter(pk=self.personal_journal.pk).exists()
            )
        )
        instance = super().save(commit=False)
        if commit:
            instance.save()
            self.save_m2m()
            if should_keep_personal_journal:
                instance.journals.add(self.personal_journal)
        return instance
