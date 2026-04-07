from django.conf import settings
from django.db import models
from django.db.models import Q


class Keyword(models.Model):
    name = models.CharField(max_length=120, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class PublicationQuerySet(models.QuerySet):
    def search(self, term):
        if not term:
            return self
        return self.filter(
            Q(title__icontains=term) | Q(content__icontains=term)
        )

    def with_keyword(self, keyword_id):
        if not keyword_id:
            return self
        return self.filter(keywords__id=keyword_id)

    def owned_by(self, user):
        if not user.is_authenticated:
            return self.none()
        return self.filter(owner=user)

    def editable_by(self, user):
        if not user.is_authenticated:
            return self.none()
        if user.is_staff:
            return self
        return self.filter(owner=user)

    def visible_to(self, user):
        if user.is_authenticated and user.is_staff:
            return self
        if user.is_authenticated:
            return self.filter(
                Q(owner=user)
                | Q(visibility=Publication.Visibility.AUTH_ONLY, status=Publication.Status.PUBLISHED)
                | Q(visibility=Publication.Visibility.PUBLIC, status=Publication.Status.PUBLISHED)
            )
        return self.filter(
            visibility=Publication.Visibility.PUBLIC,
            status=Publication.Status.PUBLISHED,
        )

    def public_feed(self):
        return self.filter(
            visibility=Publication.Visibility.PUBLIC,
            status=Publication.Status.PUBLISHED,
        )


class Publication(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'

    class Visibility(models.TextChoices):
        PRIVATE = 'private', 'Private'
        AUTH_ONLY = 'auth-only', 'Authenticated users'
        PUBLIC = 'public', 'Public'

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='publications',
    )
    title = models.CharField(max_length=255)
    content = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    visibility = models.CharField(
        max_length=20,
        choices=Visibility.choices,
        default=Visibility.PRIVATE,
    )
    keywords = models.ManyToManyField(Keyword, blank=True, related_name='publications')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = PublicationQuerySet.as_manager()

    class Meta:
        ordering = ['-created_at', '-updated_at']
        indexes = [
            models.Index(fields=['status', 'visibility']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return self.title

    def can_view(self, user):
        if user.is_authenticated and (user.is_staff or self.owner_id == user.id):
            return True
        if self.visibility == self.Visibility.PUBLIC:
            return self.status == self.Status.PUBLISHED
        if not user.is_authenticated:
            return False
        return self.visibility == self.Visibility.AUTH_ONLY and self.status == self.Status.PUBLISHED

    def can_edit(self, user):
        if not user.is_authenticated:
            return False
        return user.is_staff or self.owner_id == user.id
