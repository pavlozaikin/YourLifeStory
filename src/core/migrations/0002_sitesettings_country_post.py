# Generated manually for site settings defaults and feed posts.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="sitesettings",
            name="default_country_emoji",
            field=models.CharField(default="🏳", max_length=8),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="default_country_name",
            field=models.CharField(default="Unknown", max_length=120),
        ),
        migrations.CreateModel(
            name="Post",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=255)),
                ("content", models.TextField()),
                (
                    "visibility",
                    models.CharField(
                        choices=[
                            ("auth-only", "Authenticated users"),
                            ("public", "Public"),
                        ],
                        default="auth-only",
                        max_length=20,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "owner",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="posts",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at", "-updated_at"],
                "indexes": [
                    models.Index(fields=["visibility", "created_at"], name="core_post_visibil_2e7424_idx"),
                ],
            },
        ),
    ]
