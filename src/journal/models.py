from django.conf import settings
from django.db import models


class JournalQuerySet(models.QuerySet):
    def for_user(self, user):
        if not user.is_authenticated:
            return self.none()
        return self.filter(owner=user)


class JournalManager(models.Manager):
    def get_queryset(self):
        return JournalQuerySet(self.model, using=self._db)

    def get_or_create_for_user(self, user):
        if not user.is_authenticated:
            raise ValueError("An authenticated user is required.")
        journal, _ = self.get_or_create(
            owner=user,
            defaults={"title": "My Journal"},
        )
        return journal


class Journal(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="journals",
    )
    title = models.CharField(max_length=255, default="My Journal")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = JournalManager()

    class Meta:
        ordering = ["title", "-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["owner"], name="unique_journal_owner"),
        ]

    def __str__(self):
        return self.title


class JournalEntryQuerySet(models.QuerySet):
    def for_user(self, user):
        if not user.is_authenticated:
            return self.none()
        return self.filter(journal__owner=user)


class JournalEntry(models.Model):
    journal = models.ForeignKey(
        Journal,
        on_delete=models.CASCADE,
        related_name="entries",
    )
    title = models.CharField(max_length=255, blank=True, default="")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = JournalEntryQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at", "-updated_at"]
        indexes = [
            models.Index(fields=["journal"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return self.title or "Untitled entry"

    @property
    def display_title(self):
        return self.title or "Untitled entry"

    def can_view(self, user):
        return user.is_authenticated and self.journal.owner_id == user.id

    def can_edit(self, user):
        return self.can_view(user)

