from django.contrib import admin

from curriculum.models import (
    Curriculum,
    CurriculumMembership,
    CurriculumUserState,
    Lesson,
    LessonProgress,
    Resource,
    Topic,
)


@admin.register(Curriculum)
class CurriculumAdmin(admin.ModelAdmin):
    list_display = ("title", "code", "owner", "visibility", "deadline", "created_at", "updated_at")
    list_filter = ("visibility", "created_at", "updated_at")
    search_fields = ("title", "code", "goal", "expected_results", "owner__username")
    autocomplete_fields = ("owner",)
    date_hierarchy = "created_at"


@admin.register(CurriculumMembership)
class CurriculumMembershipAdmin(admin.ModelAdmin):
    list_display = ("curriculum", "user", "role", "created_at", "updated_at")
    list_filter = ("role",)
    search_fields = ("curriculum__title", "user__username")
    autocomplete_fields = ("curriculum", "user")


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ("title", "curriculum", "position", "created_at", "updated_at")
    search_fields = ("title", "summary", "curriculum__title")
    autocomplete_fields = ("curriculum",)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "topic", "position", "deadline", "created_at", "updated_at")
    search_fields = ("title", "content", "topic__title", "topic__curriculum__title")
    autocomplete_fields = ("topic",)
    date_hierarchy = "created_at"


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ("title", "curriculum", "lesson", "position", "created_at", "updated_at")
    search_fields = ("title", "url", "notes")
    autocomplete_fields = ("curriculum", "lesson")


@admin.register(CurriculumUserState)
class CurriculumUserStateAdmin(admin.ModelAdmin):
    list_display = ("curriculum", "user", "status", "created_at", "updated_at")
    list_filter = ("status",)
    autocomplete_fields = ("curriculum", "user")


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ("lesson", "user", "status", "created_at", "updated_at")
    list_filter = ("status",)
    autocomplete_fields = ("lesson", "user")

