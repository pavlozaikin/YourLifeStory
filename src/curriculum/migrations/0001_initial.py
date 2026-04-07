from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Curriculum",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                ("code", models.SlugField(blank=True, max_length=60, unique=True)),
                ("goal", models.TextField()),
                ("expected_results", models.TextField()),
                ("visibility", models.CharField(choices=[("private", "Private"), ("authorized", "Authorized"), ("public", "Public")], default="private", max_length=20)),
                ("deadline", models.DateField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="owned_curricula", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["title", "-created_at"]},
        ),
        migrations.CreateModel(
            name="CurriculumMembership",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("role", models.CharField(choices=[("author", "Author"), ("student", "Student"), ("viewer", "Viewer")], default="viewer", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("curriculum", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="memberships", to="curriculum.curriculum")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="curriculum_memberships", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["user__username"]},
        ),
        migrations.CreateModel(
            name="CurriculumUserState",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("wishlist", "Wishlist"), ("todo", "To do"), ("in_progress", "In progress"), ("done", "Done")], default="todo", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("curriculum", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="user_states", to="curriculum.curriculum")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="curriculum_states", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["curriculum__title"]},
        ),
        migrations.CreateModel(
            name="Topic",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                ("summary", models.TextField(blank=True)),
                ("position", models.PositiveIntegerField(default=1)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("curriculum", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="topics", to="curriculum.curriculum")),
            ],
            options={"ordering": ["position", "created_at"]},
        ),
        migrations.CreateModel(
            name="Lesson",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                ("content", models.TextField()),
                ("deadline", models.DateField(blank=True, null=True)),
                ("position", models.PositiveIntegerField(default=1)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("topic", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="lessons", to="curriculum.topic")),
            ],
            options={"ordering": ["position", "created_at"]},
        ),
        migrations.CreateModel(
            name="LessonProgress",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("not_started", "Not started"), ("in_progress", "In progress"), ("completed", "Completed"), ("needs_more_learning", "Needs more learning")], default="not_started", max_length=24)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("lesson", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="progress_records", to="curriculum.lesson")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="lesson_progress_records", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["lesson__topic__position", "lesson__position"]},
        ),
        migrations.CreateModel(
            name="Resource",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                ("url", models.URLField()),
                ("notes", models.TextField(blank=True)),
                ("position", models.PositiveIntegerField(default=1)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("curriculum", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="resources", to="curriculum.curriculum")),
                ("lesson", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="resources", to="curriculum.lesson")),
            ],
            options={"ordering": ["position", "created_at"]},
        ),
        migrations.AddIndex(
            model_name="curriculum",
            index=models.Index(fields=["visibility", "created_at"], name="curriculum__visibil_2f8484_idx"),
        ),
        migrations.AddIndex(
            model_name="curriculum",
            index=models.Index(fields=["code"], name="curriculum__code_7452cb_idx"),
        ),
        migrations.AddConstraint(
            model_name="curriculummembership",
            constraint=models.UniqueConstraint(fields=("curriculum", "user"), name="unique_curriculum_membership"),
        ),
        migrations.AddConstraint(
            model_name="curriculumuserstate",
            constraint=models.UniqueConstraint(fields=("curriculum", "user"), name="unique_curriculum_user_state"),
        ),
        migrations.AddConstraint(
            model_name="topic",
            constraint=models.UniqueConstraint(fields=("curriculum", "position"), name="unique_topic_position_per_curriculum"),
        ),
        migrations.AddConstraint(
            model_name="lesson",
            constraint=models.UniqueConstraint(fields=("topic", "position"), name="unique_lesson_position_per_topic"),
        ),
        migrations.AddConstraint(
            model_name="lessonprogress",
            constraint=models.UniqueConstraint(fields=("lesson", "user"), name="unique_lesson_progress_per_user"),
        ),
    ]

