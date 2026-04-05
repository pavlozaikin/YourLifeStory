from django.conf import settings
from django.db import models
from django.db.models import Q


class SiteSettings(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True, editable=False)
    self_signup_enabled = models.BooleanField(default=True)
    default_country_name = models.CharField(max_length=120, default="Unknown")
    default_country_emoji = models.CharField(max_length=8, default="🏳")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Site setting"
        verbose_name_plural = "Site settings"

    def __str__(self):
        return "Site settings"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        settings, _ = cls.objects.get_or_create(
            pk=1,
            defaults={
                "self_signup_enabled": True,
                "default_country_name": "Unknown",
                "default_country_emoji": "🏳",
            },
        )
        return settings


class PostQuerySet(models.QuerySet):
    def search(self, term):
        if not term:
            return self
        return self.filter(Q(title__icontains=term) | Q(content__icontains=term))

    def owned_by(self, user):
        if not user.is_authenticated:
            return self.none()
        return self.filter(owner=user)

    def visible_to(self, user):
        if user.is_authenticated and user.is_staff:
            return self
        if user.is_authenticated:
            return self.filter(
                Q(owner=user)
                | Q(visibility=Post.Visibility.AUTH_ONLY)
                | Q(visibility=Post.Visibility.PUBLIC)
            )
        return self.filter(visibility=Post.Visibility.PUBLIC)

    def public_feed(self):
        return self.filter(visibility=Post.Visibility.PUBLIC)


class Post(models.Model):
    class Visibility(models.TextChoices):
        AUTH_ONLY = "auth-only", "Authenticated users"
        PUBLIC = "public", "Public"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="posts",
    )
    title = models.CharField(max_length=255)
    content = models.TextField()
    visibility = models.CharField(
        max_length=20,
        choices=Visibility.choices,
        default=Visibility.AUTH_ONLY,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = PostQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at", "-updated_at"]
        indexes = [
            models.Index(fields=["visibility", "created_at"]),
        ]

    def __str__(self):
        return self.title

    def can_view(self, user):
        if user.is_authenticated and (user.is_staff or self.owner_id == user.id):
            return True
        if self.visibility == self.Visibility.PUBLIC:
            return True
        return user.is_authenticated

    def can_edit(self, user):
        return user.is_authenticated and (user.is_staff or self.owner_id == user.id)
