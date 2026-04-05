from django.contrib import admin

from core.models import Post, SiteSettings


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ("self_signup_enabled", "default_country_name", "default_country_emoji", "updated_at")

    def has_add_permission(self, request):
        if SiteSettings.objects.exists():
            return False
        return super().has_add_permission(request)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "visibility", "created_at", "updated_at")
    list_filter = ("visibility", "created_at", "updated_at")
    search_fields = ("title", "content", "owner__username")
    autocomplete_fields = ("owner",)
    date_hierarchy = "created_at"
