from django import forms


class MarkdownTextarea(forms.Textarea):
    def __init__(self, attrs=None):
        base_attrs = {
            "rows": 14,
            "class": "markdown-editor-input",
            "data-markdown-editor": "true",
            "spellcheck": "true",
        }
        if attrs:
            base_attrs.update(attrs)
        super().__init__(base_attrs)

