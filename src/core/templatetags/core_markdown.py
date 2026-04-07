from django import template

from core.markdown import render_markdown


register = template.Library()


@register.filter
def markdown(value):
    return render_markdown(value)


@register.filter
def get_item(mapping, key):
    if mapping is None:
        return None
    return mapping.get(key)
