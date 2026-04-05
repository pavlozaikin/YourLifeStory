from django import template

from core.markdown import render_markdown


register = template.Library()


@register.filter
def markdown(value):
    return render_markdown(value)

