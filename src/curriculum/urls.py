from django.urls import path

from curriculum import views


app_name = "curriculum"


urlpatterns = [
    path("", views.CurriculumListView.as_view(), name="curriculum-list"),
    path("create/", views.CurriculumCreateView.as_view(), name="curriculum-create"),
    path("<int:pk>/", views.CurriculumDetailView.as_view(), name="curriculum-detail"),
    path("<int:pk>/enroll/", views.CurriculumEnrollView.as_view(), name="curriculum-enroll"),
    path("<int:pk>/edit/", views.CurriculumUpdateView.as_view(), name="curriculum-edit"),
    path("<int:pk>/delete/", views.CurriculumDeleteView.as_view(), name="curriculum-delete"),
    path("<int:pk>/topics/create/", views.TopicCreateView.as_view(), name="topic-create"),
    path("<int:pk>/members/create/", views.MembershipCreateView.as_view(), name="membership-create"),
    path("<int:pk>/resources/create/", views.CurriculumResourceCreateView.as_view(), name="curriculum-resource-create"),
    path("<int:pk>/state/", views.CurriculumUserStateUpdateView.as_view(), name="user-state-edit"),
    path("topics/<int:pk>/edit/", views.TopicUpdateView.as_view(), name="topic-edit"),
    path("topics/<int:pk>/delete/", views.TopicDeleteView.as_view(), name="topic-delete"),
    path("topics/<int:pk>/lessons/create/", views.LessonCreateView.as_view(), name="lesson-create"),
    path("lessons/<int:pk>/", views.LessonDetailView.as_view(), name="lesson-detail"),
    path("lessons/<int:pk>/edit/", views.LessonUpdateView.as_view(), name="lesson-edit"),
    path("lessons/<int:pk>/delete/", views.LessonDeleteView.as_view(), name="lesson-delete"),
    path("lessons/<int:pk>/progress/", views.LessonProgressUpdateView.as_view(), name="lesson-progress-edit"),
    path("lessons/<int:pk>/resources/create/", views.LessonResourceCreateView.as_view(), name="lesson-resource-create"),
    path("resources/<int:pk>/edit/", views.ResourceUpdateView.as_view(), name="resource-edit"),
    path("resources/<int:pk>/delete/", views.ResourceDeleteView.as_view(), name="resource-delete"),
    path("members/<int:pk>/edit/", views.MembershipUpdateView.as_view(), name="membership-edit"),
    path("members/<int:pk>/delete/", views.MembershipDeleteView.as_view(), name="membership-delete"),
]
