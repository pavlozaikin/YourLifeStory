from django import forms

from publications.models import Keyword, Publication


class PublicationForm(forms.ModelForm):
    keywords = forms.ModelMultipleChoiceField(
        queryset=Keyword.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Publication
        fields = ['title', 'content', 'status', 'visibility', 'keywords']
        widgets = {
            'title': forms.TextInput(attrs={'size': 60}),
            'content': forms.Textarea(attrs={'rows': 12, 'cols': 80}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['keywords'].queryset = Keyword.objects.order_by('name')


class KeywordForm(forms.ModelForm):
    class Meta:
        model = Keyword
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'size': 40}),
        }
