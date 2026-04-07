from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from curriculum.models import (
    Curriculum,
    CurriculumMembership,
    CurriculumUserState,
    Lesson,
    LessonProgress,
    Resource,
    Topic,
)


class CurriculumModelTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="Password123!")
        self.student = User.objects.create_user(username="student", password="Password123!")

    def test_code_is_generated_when_missing(self):
        curriculum = Curriculum.objects.create(
            owner=self.owner,
            title="Python Basics",
            goal="Learn Python.",
            expected_results="Read and write scripts.",
        )

        self.assertEqual(curriculum.code, "PYTHON-BASICS")

    def test_duplicate_titles_receive_unique_codes(self):
        first = Curriculum.objects.create(
            owner=self.owner,
            title="Data Science",
            goal="Learn data science.",
            expected_results="Build models.",
        )
        second = Curriculum.objects.create(
            owner=self.owner,
            title="Data Science",
            goal="Learn more data science.",
            expected_results="Build better models.",
        )

        self.assertNotEqual(first.code, second.code)

    def test_resource_requires_exactly_one_parent(self):
        curriculum = Curriculum.objects.create(
            owner=self.owner,
            title="History",
            goal="Study history.",
            expected_results="Understand eras.",
        )
        topic = Topic.objects.create(curriculum=curriculum, title="Ancient", position=1)
        lesson = Lesson.objects.create(topic=topic, title="Egypt", content="Notes", position=1)
        resource = Resource(title="Link", url="https://example.com", curriculum=curriculum, lesson=lesson)

        with self.assertRaises(ValidationError):
            resource.full_clean()

    def test_progress_percent_is_computed_from_completed_lessons(self):
        curriculum = Curriculum.objects.create(
            owner=self.owner,
            title="Math",
            goal="Study math.",
            expected_results="Solve problems.",
        )
        topic = Topic.objects.create(curriculum=curriculum, title="Algebra", position=1)
        lesson_one = Lesson.objects.create(topic=topic, title="Lesson 1", content="A", position=1)
        lesson_two = Lesson.objects.create(topic=topic, title="Lesson 2", content="B", position=2)
        CurriculumMembership.objects.create(
            curriculum=curriculum,
            user=self.student,
            role=CurriculumMembership.Role.STUDENT,
        )
        curriculum.enroll_user(self.student)
        LessonProgress.objects.create(
            lesson=lesson_one,
            user=self.student,
            status=LessonProgress.Status.COMPLETED,
        )
        LessonProgress.objects.create(
            lesson=lesson_two,
            user=self.student,
            status=LessonProgress.Status.IN_PROGRESS,
        )

        self.assertEqual(curriculum.progress_percent_for(self.student), 50)

    def test_owner_membership_is_still_not_used_for_dual_role(self):
        curriculum = Curriculum.objects.create(
            owner=self.owner,
            title="Writing",
            goal="Write better.",
            expected_results="Publish text.",
        )
        membership = CurriculumMembership(
            curriculum=curriculum,
            user=self.owner,
            role=CurriculumMembership.Role.AUTHOR,
        )

        with self.assertRaises(ValidationError):
            membership.full_clean()


class CurriculumViewTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="Password123!")
        self.author = User.objects.create_user(username="author", password="Password123!")
        self.student = User.objects.create_user(username="student", password="Password123!")
        self.viewer = User.objects.create_user(username="viewer", password="Password123!")
        self.stranger = User.objects.create_user(username="stranger", password="Password123!")
        self.curriculum = Curriculum.objects.create(
            owner=self.owner,
            title="Spanish",
            goal="Learn Spanish.",
            expected_results="Hold basic conversations.",
            visibility=Curriculum.Visibility.AUTHORIZED,
        )
        self.topic = Topic.objects.create(
            curriculum=self.curriculum,
            title="Grammar",
            summary="Core grammar topics",
            position=1,
        )
        self.lesson = Lesson.objects.create(
            topic=self.topic,
            title="Present tense",
            content="Study conjugation patterns.",
            position=1,
        )
        self.lesson_resource = Resource.objects.create(
            lesson=self.lesson,
            title="Conjugation chart",
            url="https://example.com/chart",
            position=1,
        )
        Resource.objects.create(
            curriculum=self.curriculum,
            title="Roadmap",
            url="https://example.com/roadmap",
            position=1,
        )
        CurriculumMembership.objects.create(
            curriculum=self.curriculum,
            user=self.author,
            role=CurriculumMembership.Role.AUTHOR,
        )
        CurriculumMembership.objects.create(
            curriculum=self.curriculum,
            user=self.student,
            role=CurriculumMembership.Role.STUDENT,
        )
        CurriculumMembership.objects.create(
            curriculum=self.curriculum,
            user=self.viewer,
            role=CurriculumMembership.Role.VIEWER,
        )

    def test_workspace_exposes_curriculum_module(self):
        self.client.login(username="owner", password="Password123!")

        response = self.client.get(reverse("workspace"))

        self.assertContains(response, "Curriculums")

    def test_authenticated_user_can_create_curriculum(self):
        self.client.login(username="owner", password="Password123!")

        response = self.client.post(
            reverse("curriculum:curriculum-create"),
            {
                "title": "Rust",
                "goal": "Learn Rust",
                "expected_results": "Ship a CLI tool",
                "visibility": Curriculum.Visibility.PRIVATE,
                "code": "",
            },
        )

        created = Curriculum.objects.get(title="Rust")
        self.assertRedirects(response, reverse("curriculum:curriculum-detail", args=[created.pk]))
        self.assertEqual(created.owner, self.owner)

    def test_author_can_edit_curriculum_materials(self):
        self.client.login(username="author", password="Password123!")

        response = self.client.post(
            reverse("curriculum:topic-create", args=[self.curriculum.pk]),
            {
                "title": "Vocabulary",
                "summary": "Words",
                "position": 2,
            },
        )

        self.assertRedirects(response, reverse("curriculum:curriculum-detail", args=[self.curriculum.pk]))
        self.assertTrue(Topic.objects.filter(curriculum=self.curriculum, title="Vocabulary").exists())

    def test_student_can_view_lesson_and_update_own_progress(self):
        self.client.login(username="student", password="Password123!")
        self.client.post(reverse("curriculum:curriculum-enroll", args=[self.curriculum.pk]))

        detail_response = self.client.get(reverse("curriculum:lesson-detail", args=[self.lesson.pk]))
        progress_response = self.client.post(
            reverse("curriculum:lesson-progress-edit", args=[self.lesson.pk]),
            {"status": LessonProgress.Status.COMPLETED},
        )

        progress = LessonProgress.objects.get(lesson=self.lesson, user=self.student)
        self.assertEqual(detail_response.status_code, 200)
        self.assertRedirects(progress_response, reverse("curriculum:lesson-detail", args=[self.lesson.pk]))
        self.assertEqual(progress.status, LessonProgress.Status.COMPLETED)

    def test_owner_can_enroll_as_student_and_complete_lessons(self):
        self.client.login(username="owner", password="Password123!")

        enroll_response = self.client.post(reverse("curriculum:curriculum-enroll", args=[self.curriculum.pk]))
        progress_response = self.client.post(
            reverse("curriculum:lesson-progress-edit", args=[self.lesson.pk]),
            {"status": LessonProgress.Status.COMPLETED},
        )

        study_state = CurriculumUserState.objects.get(curriculum=self.curriculum, user=self.owner)
        progress = LessonProgress.objects.get(lesson=self.lesson, user=self.owner)
        self.assertRedirects(enroll_response, reverse("curriculum:curriculum-detail", args=[self.curriculum.pk]))
        self.assertRedirects(progress_response, reverse("curriculum:lesson-detail", args=[self.lesson.pk]))
        self.assertEqual(study_state.status, CurriculumUserState.Status.TODO)
        self.assertEqual(progress.status, LessonProgress.Status.COMPLETED)

    def test_student_cannot_edit_materials(self):
        self.client.login(username="student", password="Password123!")

        response = self.client.get(reverse("curriculum:lesson-edit", args=[self.lesson.pk]))

        self.assertEqual(response.status_code, 404)

    def test_viewer_can_see_structure_but_not_lesson_content(self):
        self.client.login(username="viewer", password="Password123!")

        detail_response = self.client.get(reverse("curriculum:curriculum-detail", args=[self.curriculum.pk]))
        lesson_response = self.client.get(reverse("curriculum:lesson-detail", args=[self.lesson.pk]))

        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, self.lesson.title)
        self.assertNotContains(detail_response, self.lesson.content)
        self.assertEqual(lesson_response.status_code, 404)

    def test_stranger_cannot_view_authorized_curriculum(self):
        self.client.login(username="stranger", password="Password123!")

        response = self.client.get(reverse("curriculum:curriculum-detail", args=[self.curriculum.pk]))

        self.assertEqual(response.status_code, 404)

    def test_public_curriculum_shows_structure_to_anonymous_user(self):
        self.curriculum.visibility = Curriculum.Visibility.PUBLIC
        self.curriculum.save()

        response = self.client.get(reverse("curriculum:curriculum-detail", args=[self.curriculum.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.curriculum.title)
        self.assertContains(response, self.lesson.title)
        self.assertNotContains(response, self.lesson.content)

    def test_anonymous_user_cannot_view_public_lesson_material(self):
        self.curriculum.visibility = Curriculum.Visibility.PUBLIC
        self.curriculum.save()

        response = self.client.get(reverse("curriculum:lesson-detail", args=[self.lesson.pk]))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_user_state_is_isolated_per_user(self):
        self.client.login(username="student", password="Password123!")
        self.client.post(reverse("curriculum:curriculum-enroll", args=[self.curriculum.pk]))
        self.client.post(
            reverse("curriculum:user-state-edit", args=[self.curriculum.pk]),
            {"status": CurriculumUserState.Status.IN_PROGRESS},
        )
        self.client.logout()
        self.client.login(username="author", password="Password123!")
        self.client.post(reverse("curriculum:curriculum-enroll", args=[self.curriculum.pk]))
        self.client.post(
            reverse("curriculum:user-state-edit", args=[self.curriculum.pk]),
            {"status": CurriculumUserState.Status.DONE},
        )

        student_state = CurriculumUserState.objects.get(curriculum=self.curriculum, user=self.student)
        author_state = CurriculumUserState.objects.get(curriculum=self.curriculum, user=self.author)
        self.assertEqual(student_state.status, CurriculumUserState.Status.IN_PROGRESS)
        self.assertEqual(author_state.status, CurriculumUserState.Status.DONE)

    def test_owner_can_manage_memberships(self):
        extra = User.objects.create_user(username="extra", password="Password123!")
        self.client.login(username="owner", password="Password123!")

        response = self.client.post(
            reverse("curriculum:membership-create", args=[self.curriculum.pk]),
            {
                "user": extra.pk,
                "role": CurriculumMembership.Role.VIEWER,
            },
        )

        self.assertRedirects(response, reverse("curriculum:curriculum-detail", args=[self.curriculum.pk]))
        self.assertTrue(
            CurriculumMembership.objects.filter(curriculum=self.curriculum, user=extra).exists()
        )
