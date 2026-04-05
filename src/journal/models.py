from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from core.markdown import render_markdown
from core.models import SiteSettings


class JournalQuerySet(models.QuerySet):
    def for_user(self, user):
        if not user.is_authenticated:
            return self.none()
        return self.filter(owner=user)


class JournalManager(models.Manager):
    def get_queryset(self):
        return JournalQuerySet(self.model, using=self._db)

    def for_user(self, user):
        return self.get_queryset().for_user(user)

    def get_or_create_personal_journal(self, user):
        if not user.is_authenticated:
            raise ValueError("An authenticated user is required.")
        journal, _ = self.get_or_create(
            owner=user,
            is_personal=True,
            defaults={"title": "Personal Journal"},
        )
        return journal

    def get_personal_journal(self, user):
        return self.get_or_create_personal_journal(user)


class Journal(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="journals",
    )
    title = models.CharField(max_length=255, default="Personal Journal")
    is_personal = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = JournalManager()

    class Meta:
        ordering = ["title", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["owner"],
                condition=Q(is_personal=True),
                name="unique_personal_journal_per_owner",
            ),
        ]

    def __str__(self):
        return self.title

    @property
    def display_title(self):
        return self.title

    def can_edit(self, user):
        return user.is_authenticated and self.owner_id == user.id

    def can_delete(self, user):
        return self.can_edit(user) and not self.is_personal


class JournalEntryQuerySet(models.QuerySet):
    def for_user(self, user):
        if not user.is_authenticated:
            return self.none()
        return self.filter(
            Q(journals__owner=user)
            | Q(shared_with=user)
            | Q(visibility=JournalEntry.Visibility.PUBLIC)
        ).distinct()


class JournalEntry(models.Model):
    class Visibility(models.TextChoices):
        PRIVATE = "private", "Private"
        PUBLIC = "public", "Public"
        SHARED = "shared", "Shared"

    journals = models.ManyToManyField(
        Journal,
        related_name="entries",
        blank=True,
    )
    title = models.CharField(max_length=255, blank=True, default="")
    content = models.TextField()
    visibility = models.CharField(
        max_length=20,
        choices=Visibility.choices,
        default=Visibility.PRIVATE,
    )
    shared_with = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="shared_journal_entries",
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = JournalEntryQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at", "-updated_at"]
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["visibility"]),
        ]

    def __str__(self):
        return self.title or "Untitled entry"

    @property
    def display_title(self):
        return self.title or "Untitled entry"

    def can_view(self, user):
        if self.visibility == self.Visibility.PUBLIC:
            return True
        if not user.is_authenticated:
            return False
        if self.journals.filter(owner=user).exists():
            return True
        return self.shared_with.filter(pk=user.pk).exists()

    def can_edit(self, user):
        if not user.is_authenticated:
            return False
        if self.journals.filter(owner=user).exists():
            return True
        return self.shared_with.filter(pk=user.pk).exists()

    @property
    def rendered_content(self):
        return render_markdown(self.content)

    def export_filename(self):
        export_date = (self.created_at or timezone.now()).date()
        return export_date.strftime("%Y-%m-%d.md")

    def to_markdown(self):
        export_dt = self.created_at or timezone.now()
        month_number = export_dt.strftime("%m")
        month_name = export_dt.strftime("%B")
        year = export_dt.year
        site_settings = SiteSettings.get_solo()
        return "\n".join(
            [
                "---",
                "aliases:",
                'Journal: "[[Journal.base]]"',
                f'Country: "[[{site_settings.default_country_name}|{site_settings.default_country_emoji}]]"',
                f"Year: {year}",
                "Month:",
                f"  - {month_number} — {month_name}",
                "---",
                f"# {self.display_title}",
                self.content.rstrip(),
            ]
        ).rstrip() + "\n"
