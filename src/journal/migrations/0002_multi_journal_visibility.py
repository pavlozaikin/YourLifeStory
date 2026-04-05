# Generated manually for multi-journal entries and entry sharing.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
from django.db.models import Q


def migrate_existing_entries(apps, schema_editor):
    Journal = apps.get_model("journal", "Journal")
    JournalEntry = apps.get_model("journal", "JournalEntry")

    for journal in Journal.objects.all():
        journal.is_personal = True
        if not journal.title:
            journal.title = "Personal Journal"
        journal.save(update_fields=["is_personal", "title"])

    for entry in JournalEntry.objects.exclude(journal_id=None):
        entry.journals.add(entry.journal_id)


class Migration(migrations.Migration):
    dependencies = [
        ("journal", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="journal",
            name="is_personal",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="journal",
            name="title",
            field=models.CharField(default="Personal Journal", max_length=255),
        ),
        migrations.RemoveConstraint(
            model_name="journal",
            name="unique_journal_owner",
        ),
        migrations.AddConstraint(
            model_name="journal",
            constraint=models.UniqueConstraint(
                condition=Q(is_personal=True),
                fields=("owner",),
                name="unique_personal_journal_per_owner",
            ),
        ),
        migrations.AddField(
            model_name="journalentry",
            name="journals",
            field=models.ManyToManyField(blank=True, related_name="journal_entry_links", to="journal.journal"),
        ),
        migrations.AddField(
            model_name="journalentry",
            name="shared_with",
            field=models.ManyToManyField(blank=True, related_name="shared_journal_entries", to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name="journalentry",
            name="visibility",
            field=models.CharField(
                choices=[("private", "Private"), ("public", "Public"), ("shared", "Shared")],
                default="private",
                max_length=20,
            ),
        ),
        migrations.RunPython(migrate_existing_entries, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="journalentry",
            name="journal",
        ),
        migrations.AlterField(
            model_name="journalentry",
            name="journals",
            field=models.ManyToManyField(blank=True, related_name="entries", to="journal.journal"),
        ),
        migrations.AddIndex(
            model_name="journalentry",
            index=models.Index(fields=["visibility"], name="journal_jou_visibil_2454d8_idx"),
        ),
    ]
