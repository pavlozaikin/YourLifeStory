from django.contrib import admin

from publications.models import Keyword, Publication


@admin.register(Keyword)
class KeywordAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at", "updated_at")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'status', 'visibility', 'created_at', 'updated_at')
    list_filter = ('status', 'visibility', 'created_at', 'updated_at')
    search_fields = ('title', 'content', 'owner__username', 'keywords__name')
    autocomplete_fields = ('owner',)
    filter_horizontal = ('keywords',)
    date_hierarchy = 'created_at'
