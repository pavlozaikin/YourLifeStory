from django.db import models


class SiteSettings(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True, editable=False)
    self_signup_enabled = models.BooleanField(default=True)
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
        settings, _ = cls.objects.get_or_create(pk=1, defaults={"self_signup_enabled": True})
        return settings
