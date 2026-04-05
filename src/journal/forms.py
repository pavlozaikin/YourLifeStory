from django import forms

from journal.models import JournalEntry


class JournalEntryForm(forms.ModelForm):
    class Meta:
        model = JournalEntry
        fields = ["title", "content"]
        widgets = {
            "title": forms.TextInput(attrs={"size": 60}),
            "content": forms.Textarea(attrs={"rows": 12, "cols": 80}),
        }

