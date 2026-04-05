from django.contrib import admin

from journal.models import Journal, JournalEntry


@admin.register(Journal)
class JournalAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "created_at", "updated_at")
    search_fields = ("title", "owner__username")
    list_select_related = ("owner",)
    ordering = ("owner__username", "title")


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ("entry_title", "journal", "owner_username", "created_at", "updated_at")
    search_fields = ("title", "content", "journal__owner__username", "journal__title")
    list_select_related = ("journal", "journal__owner")
    date_hierarchy = "created_at"

    @admin.display(description="Title")
    def entry_title(self, obj):
        return obj.display_title

    @admin.display(description="Owner")
    def owner_username(self, obj):
        return obj.journal.owner.username
