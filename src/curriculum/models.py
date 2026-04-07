from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils.text import slugify

from core.markdown import render_markdown


def generate_curriculum_code(title):
    base = slugify(title or "curriculum").upper().replace("-", "-")[:40].strip("-")
    if not base:
        base = "CURRICULUM"
    return base


class CurriculumQuerySet(models.QuerySet):
    def visible_to(self, user):
        if user.is_authenticated:
            return self.filter(
                Q(owner=user)
                | Q(memberships__user=user)
                | Q(visibility=Curriculum.Visibility.PUBLIC)
            ).distinct()
        return self.filter(visibility=Curriculum.Visibility.PUBLIC)

    def editable_by(self, user):
        if not user.is_authenticated:
            return self.none()
        return self.filter(
            Q(owner=user)
            | Q(
                memberships__user=user,
                memberships__role=CurriculumMembership.Role.AUTHOR,
            )
        ).distinct()

    def material_viewable_by(self, user):
        if not user.is_authenticated:
            return self.none()
        return self.filter(
            Q(owner=user)
            | Q(
                memberships__user=user,
                memberships__role__in=[
                    CurriculumMembership.Role.AUTHOR,
                    CurriculumMembership.Role.STUDENT,
                ],
            )
        ).distinct()


class Curriculum(models.Model):
    class Visibility(models.TextChoices):
        PRIVATE = "private", "Private"
        AUTHORIZED = "authorized", "Authorized"
        PUBLIC = "public", "Public"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_curricula",
    )
    title = models.CharField(max_length=255)
    code = models.SlugField(max_length=60, unique=True, blank=True)
    goal = models.TextField()
    expected_results = models.TextField()
    visibility = models.CharField(
        max_length=20,
        choices=Visibility.choices,
        default=Visibility.PRIVATE,
    )
    deadline = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CurriculumQuerySet.as_manager()

    class Meta:
        ordering = ["title", "-created_at"]
        indexes = [
            models.Index(fields=["visibility", "created_at"]),
            models.Index(fields=["code"]),
        ]

    def __str__(self):
        return self.title

    def _next_generated_code(self):
        base = generate_curriculum_code(self.title)
        candidate = base
        suffix = 2
        while Curriculum.objects.exclude(pk=self.pk).filter(code=candidate).exists():
            candidate = f"{base}-{suffix}"
            suffix += 1
        return candidate

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self._next_generated_code()
        super().save(*args, **kwargs)

    def get_membership(self, user):
        if not user.is_authenticated or self.owner_id == user.id:
            return None
        cache = getattr(self, "_membership_cache", {})
        if user.id in cache:
            return cache[user.id]
        membership = self.memberships.filter(user=user).first()
        cache[user.id] = membership
        self._membership_cache = cache
        return membership

    def get_role(self, user):
        if not user.is_authenticated:
            return None
        if self.owner_id == user.id:
            return CurriculumMembership.Role.AUTHOR
        membership = self.get_membership(user)
        if membership:
            return membership.role
        return None

    def can_view_structure(self, user):
        if self.visibility == self.Visibility.PUBLIC:
            return True
        return self.get_role(user) is not None

    def can_view_materials(self, user):
        role = self.get_role(user)
        return role in {
            CurriculumMembership.Role.AUTHOR,
            CurriculumMembership.Role.STUDENT,
        }

    def can_edit_materials(self, user):
        role = self.get_role(user)
        return role == CurriculumMembership.Role.AUTHOR

    def can_manage_members(self, user):
        return self.can_edit_materials(user)

    def can_update_learning_state(self, user):
        return self.can_view_materials(user) and self.is_enrolled(user)

    def get_study_state(self, user):
        if not user.is_authenticated or not self.can_view_materials(user):
            return None
        return CurriculumUserState.objects.filter(curriculum=self, user=user).first()

    def enroll_user(self, user):
        if not user.is_authenticated or not self.can_view_materials(user):
            return None
        state, _ = CurriculumUserState.objects.get_or_create(
            curriculum=self,
            user=user,
        )
        return state

    def is_enrolled(self, user):
        return self.get_study_state(user) is not None

    def progress_percent_for(self, user):
        if not user.is_authenticated or not self.can_update_learning_state(user):
            return None
        total = Lesson.objects.filter(topic__curriculum=self).count()
        if total == 0:
            return 0
        completed = LessonProgress.objects.filter(
            lesson__topic__curriculum=self,
            user=user,
            status=LessonProgress.Status.COMPLETED,
        ).count()
        return int((completed / total) * 100)


class CurriculumMembership(models.Model):
    class Role(models.TextChoices):
        AUTHOR = "author", "Author"
        STUDENT = "student", "Student"
        VIEWER = "viewer", "Viewer"

    curriculum = models.ForeignKey(
        Curriculum,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="curriculum_memberships",
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.VIEWER,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["user__username"]
        constraints = [
            models.UniqueConstraint(
                fields=["curriculum", "user"],
                name="unique_curriculum_membership",
            ),
        ]

    def __str__(self):
        return f"{self.user} -> {self.curriculum} ({self.role})"

    def clean(self):
        super().clean()
        if self.curriculum_id and self.user_id and self.curriculum.owner_id == self.user_id:
            raise ValidationError("The curriculum owner is already the primary author.")


class Topic(models.Model):
    curriculum = models.ForeignKey(
        Curriculum,
        on_delete=models.CASCADE,
        related_name="topics",
    )
    title = models.CharField(max_length=255)
    summary = models.TextField(blank=True)
    position = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["position", "created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["curriculum", "position"],
                name="unique_topic_position_per_curriculum",
            ),
        ]

    def __str__(self):
        return self.title


class Lesson(models.Model):
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name="lessons",
    )
    title = models.CharField(max_length=255)
    content = models.TextField()
    deadline = models.DateField(blank=True, null=True)
    position = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["position", "created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["topic", "position"],
                name="unique_lesson_position_per_topic",
            ),
        ]

    def __str__(self):
        return self.title

    @property
    def rendered_content(self):
        return render_markdown(self.content)

    @property
    def curriculum(self):
        return self.topic.curriculum


class Resource(models.Model):
    curriculum = models.ForeignKey(
        Curriculum,
        on_delete=models.CASCADE,
        related_name="resources",
        blank=True,
        null=True,
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name="resources",
        blank=True,
        null=True,
    )
    title = models.CharField(max_length=255)
    url = models.URLField()
    notes = models.TextField(blank=True)
    position = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["position", "created_at"]

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        has_curriculum = bool(self.curriculum_id)
        has_lesson = bool(self.lesson_id)
        if has_curriculum == has_lesson:
            raise ValidationError("A resource must belong to exactly one curriculum or lesson.")

    @property
    def target_curriculum(self):
        if self.curriculum_id:
            return self.curriculum
        if self.lesson_id:
            return self.lesson.topic.curriculum
        return None


class CurriculumUserState(models.Model):
    class Status(models.TextChoices):
        WISHLIST = "wishlist", "Wishlist"
        TODO = "todo", "To do"
        IN_PROGRESS = "in_progress", "In progress"
        DONE = "done", "Done"

    curriculum = models.ForeignKey(
        Curriculum,
        on_delete=models.CASCADE,
        related_name="user_states",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="curriculum_states",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.TODO,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["curriculum__title"]
        constraints = [
            models.UniqueConstraint(
                fields=["curriculum", "user"],
                name="unique_curriculum_user_state",
            ),
        ]

    def __str__(self):
        return f"{self.user} / {self.curriculum}: {self.status}"


class LessonProgress(models.Model):
    class Status(models.TextChoices):
        NOT_STARTED = "not_started", "Not started"
        IN_PROGRESS = "in_progress", "In progress"
        COMPLETED = "completed", "Completed"
        NEEDS_MORE_LEARNING = "needs_more_learning", "Needs more learning"

    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name="progress_records",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="lesson_progress_records",
    )
    status = models.CharField(
        max_length=24,
        choices=Status.choices,
        default=Status.NOT_STARTED,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["lesson__topic__position", "lesson__position"]
        constraints = [
            models.UniqueConstraint(
                fields=["lesson", "user"],
                name="unique_lesson_progress_per_user",
            ),
        ]

    def __str__(self):
        return f"{self.user} / {self.lesson}: {self.status}"
