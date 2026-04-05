import re

from django.utils import timezone


def _filename_component(value, fallback):
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", value or "")
    cleaned = cleaned.strip("_")
    return cleaned or fallback


def publication_download_filename(publication, export_date=None):
    export_date = export_date or timezone.localdate()
    username = _filename_component(publication.owner.username, "user")
    title = _filename_component(publication.title, "publication")
    return f"{export_date:%Y-%m-%d}_{username}_{title}.md"


def publication_markdown(publication):
    lines = [
        "---",
        f'title: "{publication.title}"',
        f"author: {publication.owner.username}",
        f"visibility: {publication.get_visibility_display()}",
    ]
    if publication.keywords.exists():
        lines.append("keywords:")
        for keyword in publication.keywords.all():
            lines.append(f"  - {keyword.name}")
    lines.extend(
        [
            f"created_at: {publication.created_at:%Y-%m-%d %H:%M:%S %Z}",
            f"updated_at: {publication.updated_at:%Y-%m-%d %H:%M:%S %Z}",
            "---",
            "",
            f"# {publication.title}",
            publication.content,
        ]
    )
    return "\n".join(lines).rstrip() + "\n"

