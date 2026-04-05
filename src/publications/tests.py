from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from core.models import SiteSettings
from publications.models import Keyword, Publication


class PublicationModelTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="Password123!")
        self.other_user = User.objects.create_user(username="other", password="Password123!")
        self.admin = User.objects.create_superuser(
            username="admin",
            password="Password123!",
            email="admin@example.com",
        )
        self.keyword = Keyword.objects.create(owner=self.owner, name="history")

    def test_owner_can_view_private_draft(self):
        publication = Publication.objects.create(
            owner=self.owner,
            title="Draft",
            content="Draft content",
            status=Publication.Status.DRAFT,
            visibility=Publication.Visibility.PRIVATE,
        )

        self.assertTrue(publication.can_view(self.owner))
        self.assertFalse(publication.can_view(self.other_user))
        self.assertTrue(publication.can_view(self.admin))

    def test_publication_timestamps_are_populated(self):
        publication = Publication.objects.create(
            owner=self.owner,
            title="Timed",
            content="Has timestamps",
        )

        self.assertIsNotNone(publication.created_at)
        self.assertIsNotNone(publication.updated_at)

    def test_keywords_are_scoped_per_owner(self):
        other_keyword = Keyword.objects.create(owner=self.other_user, name="history")

        self.assertNotEqual(self.keyword.pk, other_keyword.pk)


class PublicationViewTests(TestCase):
    def setUp(self):
        SiteSettings.get_solo()
        self.owner = User.objects.create_user(username="owner", password="Password123!")
        self.viewer = User.objects.create_user(username="viewer", password="Password123!")
        self.admin = User.objects.create_superuser(
            username="admin",
            password="Password123!",
            email="admin@example.com",
        )
        self.keyword = Keyword.objects.create(owner=self.owner, name="history")
        self.publication = Publication.objects.create(
            owner=self.owner,
            title="Family archive",
            content="Research notes about family history.",
            status=Publication.Status.PUBLISHED,
            visibility=Publication.Visibility.AUTH_ONLY,
        )
        self.publication.keywords.add(self.keyword)

    def test_protected_list_redirects_anonymous_users(self):
        response = self.client.get(reverse("my-publications"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_authenticated_user_can_create_publication(self):
        self.client.login(username="owner", password="Password123!")

        response = self.client.post(
            reverse("publication-create"),
            {
                "title": "My paper",
                "content": "A body of research",
                "status": Publication.Status.DRAFT,
                "visibility": Publication.Visibility.PRIVATE,
                "keywords": [self.keyword.pk],
            },
        )

        created = Publication.objects.get(title="My paper")
        self.assertRedirects(response, reverse("publication-detail", args=[created.pk]))
        self.assertEqual(created.owner, self.owner)
        self.assertEqual(created.keywords.get(), self.keyword)

    def test_publication_editor_creates_new_keywords_for_current_user(self):
        self.client.login(username="owner", password="Password123!")

        response = self.client.post(
            reverse("publication-create"),
            {
                "title": "Tagged paper",
                "content": "A body of research",
                "status": Publication.Status.DRAFT,
                "visibility": Publication.Visibility.PRIVATE,
                "new_keywords": "memoir, archives",
            },
        )

        created = Publication.objects.get(title="Tagged paper")
        self.assertRedirects(response, reverse("publication-detail", args=[created.pk]))
        self.assertQuerySetEqual(
            created.keywords.order_by("name").values_list("name", flat=True),
            ["archives", "memoir"],
            transform=lambda value: value,
        )
        self.assertTrue(Keyword.objects.filter(owner=self.owner, name="memoir").exists())

    def test_owner_can_update_publication(self):
        self.client.login(username="owner", password="Password123!")

        response = self.client.post(
            reverse("publication-edit", args=[self.publication.pk]),
            {
                "title": "Updated archive",
                "content": "Updated content",
                "status": Publication.Status.PUBLISHED,
                "visibility": Publication.Visibility.PUBLIC,
                "keywords": [self.keyword.pk],
            },
        )

        self.publication.refresh_from_db()
        self.assertRedirects(response, reverse("publication-detail", args=[self.publication.pk]))
        self.assertEqual(self.publication.title, "Updated archive")
        self.assertEqual(self.publication.visibility, Publication.Visibility.PUBLIC)

    def test_non_owner_cannot_edit_publication(self):
        self.client.login(username="viewer", password="Password123!")

        response = self.client.get(reverse("publication-edit", args=[self.publication.pk]))

        self.assertEqual(response.status_code, 403)

    def test_admin_can_access_all_publications_view(self):
        self.client.login(username="admin", password="Password123!")

        response = self.client.get(reverse("publication-all"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.publication.title)

    def test_authenticated_user_can_view_auth_only_publication(self):
        self.client.login(username="viewer", password="Password123!")

        response = self.client.get(reverse("publication-detail", args=[self.publication.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.publication.title)

    def test_anonymous_user_cannot_view_auth_only_publication(self):
        response = self.client.get(reverse("publication-detail", args=[self.publication.pk]))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_public_feed_only_shows_public_published_publications(self):
        Publication.objects.create(
            owner=self.owner,
            title="Private draft",
            content="Should stay hidden",
            status=Publication.Status.DRAFT,
            visibility=Publication.Visibility.PUBLIC,
        )
        Publication.objects.create(
            owner=self.owner,
            title="Published public note",
            content="Should be visible",
            status=Publication.Status.PUBLISHED,
            visibility=Publication.Visibility.PUBLIC,
        )

        response = self.client.get(reverse("public-feed"))

        self.assertContains(response, "Published public note")
        self.assertNotContains(response, "Private draft")
        self.assertNotContains(response, self.publication.title)

    def test_search_filters_publications_by_title_and_content(self):
        self.client.login(username="owner", password="Password123!")
        Publication.objects.create(
            owner=self.owner,
            title="Notebook",
            content="Contains manuscript references",
            status=Publication.Status.DRAFT,
            visibility=Publication.Visibility.PRIVATE,
        )

        response = self.client.get(reverse("my-publications"), {"q": "manuscript"})

        self.assertContains(response, "Notebook")
        self.assertNotContains(response, self.publication.title)

    def test_keyword_filter_limits_results(self):
        other_keyword = Keyword.objects.create(owner=self.owner, name="science")
        second_publication = Publication.objects.create(
            owner=self.owner,
            title="Lab notes",
            content="Experiments",
            status=Publication.Status.DRAFT,
            visibility=Publication.Visibility.PRIVATE,
        )
        second_publication.keywords.add(other_keyword)
        self.client.login(username="owner", password="Password123!")

        response = self.client.get(reverse("my-publications"), {"keyword": self.keyword.pk})

        self.assertContains(response, self.publication.title)
        self.assertNotContains(response, "Lab notes")

    def test_keyword_list_is_scoped_to_current_user(self):
        Keyword.objects.create(owner=self.viewer, name="private-tag")
        self.client.login(username="owner", password="Password123!")

        response = self.client.get(reverse("keyword-list"))

        self.assertContains(response, self.keyword.name)
        self.assertNotContains(response, "private-tag")

    def test_publication_download_uses_expected_filename(self):
        self.client.login(username="owner", password="Password123!")

        response = self.client.get(reverse("publication-download", args=[self.publication.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/markdown", response["Content-Type"])
        self.assertIn("owner_Family_archive.md", response["Content-Disposition"])

    def test_keyword_management_requires_authentication(self):
        response = self.client.get(reverse("keyword-list"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)
