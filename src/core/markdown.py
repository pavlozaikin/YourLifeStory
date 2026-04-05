import re
from html import escape

from django.utils.safestring import mark_safe


def _render_inline(text):
    text = escape(text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)

    def render_link(match):
        label = match.group(1)
        url = escape(match.group(2), quote=True)
        return (
            f'<a href="{url}" rel="nofollow noopener noreferrer" target="_blank">'
            f"{label}</a>"
        )

    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", render_link, text)
    return text


def render_markdown(value):
    if not value:
        return ""

    lines = value.splitlines()
    blocks = []
    paragraph = []
    list_type = None
    list_items = []
    quote_lines = []

    def flush_paragraph():
        nonlocal paragraph
        if paragraph:
            blocks.append(f"<p>{' '.join(_render_inline(line) for line in paragraph)}</p>")
            paragraph = []

    def flush_list():
        nonlocal list_type, list_items
        if list_items:
            tag = "ul" if list_type == "ul" else "ol"
            items = "".join(f"<li>{_render_inline(item)}</li>" for item in list_items)
            blocks.append(f"<{tag}>{items}</{tag}>")
            list_type = None
            list_items = []

    def flush_quote():
        nonlocal quote_lines
        if quote_lines:
            blocks.append(
                "<blockquote>"
                f"<p>{'<br>'.join(_render_inline(line) for line in quote_lines)}</p>"
                "</blockquote>"
            )
            quote_lines = []

    for raw_line in lines:
        line = raw_line.rstrip()
        stripped = line.strip()

        if not stripped:
            flush_paragraph()
            flush_list()
            flush_quote()
            continue

        heading_match = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if heading_match:
            flush_paragraph()
            flush_list()
            flush_quote()
            level = len(heading_match.group(1))
            blocks.append(f"<h{level}>{_render_inline(heading_match.group(2))}</h{level}>")
            continue

        quote_match = re.match(r"^>\s?(.*)$", stripped)
        if quote_match:
            flush_paragraph()
            flush_list()
            quote_lines.append(quote_match.group(1))
            continue

        unordered_match = re.match(r"^[-*+]\s+(.*)$", stripped)
        ordered_match = re.match(r"^\d+\.\s+(.*)$", stripped)
        if unordered_match or ordered_match:
            flush_paragraph()
            flush_quote()
            current_type = "ul" if unordered_match else "ol"
            if list_type and list_type != current_type:
                flush_list()
            list_type = current_type
            list_items.append((unordered_match or ordered_match).group(1))
            continue

        flush_list()
        flush_quote()
        paragraph.append(stripped)

    flush_paragraph()
    flush_list()
    flush_quote()
    return mark_safe("".join(blocks))

