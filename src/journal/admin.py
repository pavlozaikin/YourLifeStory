from django.contrib import admin

from journal.models import Journal, JournalEntry


@admin.register(Journal)
class JournalAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "is_personal", "created_at", "updated_at")
    search_fields = ("title", "owner__username")
    list_select_related = ("owner",)
    ordering = ("owner__username", "is_personal", "title")


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = (
        "entry_title",
        "visibility",
        "journal_summary",
        "shared_user_count",
        "created_at",
        "updated_at",
    )
    search_fields = ("title", "content", "journals__title", "shared_with__username")
    filter_horizontal = ("journals", "shared_with")
    date_hierarchy = "created_at"

    @admin.display(description="Title")
    def entry_title(self, obj):
        return obj.display_title

    @admin.display(description="Journals")
    def journal_summary(self, obj):
        return ", ".join(obj.journals.values_list("title", flat=True))

    @admin.display(description="Shared with")
    def shared_user_count(self, obj):
        return obj.shared_with.count()
