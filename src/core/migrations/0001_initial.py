# Generated manually for the auth/core MVP.

from django.db import migrations, models


def create_default_site_settings(apps, schema_editor):
    SiteSettings = apps.get_model('core', 'SiteSettings')
    SiteSettings.objects.get_or_create(pk=1, defaults={'self_signup_enabled': True})


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='SiteSettings',
            fields=[
                ('id', models.PositiveSmallIntegerField(editable=False, primary_key=True, serialize=False)),
                ('self_signup_enabled', models.BooleanField(default=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Site setting',
                'verbose_name_plural': 'Site settings',
            },
        ),
        migrations.RunPython(create_default_site_settings, migrations.RunPython.noop),
    ]
