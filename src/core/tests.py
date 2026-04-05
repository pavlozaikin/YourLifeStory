from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from core.models import Post, SiteSettings
from journal.models import Journal
from publications.models import Publication


class SiteSettingsTests(TestCase):
    def test_get_solo_creates_default_settings(self):
        settings = SiteSettings.get_solo()

        self.assertTrue(settings.self_signup_enabled)
        self.assertEqual(settings.pk, 1)
        self.assertEqual(settings.default_country_name, "Unknown")
        self.assertEqual(settings.default_country_emoji, "🏳")

    def test_signup_disabled_returns_not_found(self):
        settings = SiteSettings.get_solo()
        settings.self_signup_enabled = False
        settings.save()

        response = self.client.get(reverse("signup"))

        self.assertEqual(response.status_code, 404)


class AuthenticationFlowTests(TestCase):
    def test_signup_creates_user_when_enabled(self):
        response = self.client.post(
            reverse("signup"),
            {
                "username": "new-user",
                "password1": "StrongPassword123!",
                "password2": "StrongPassword123!",
            },
        )

        self.assertRedirects(response, reverse("workspace"))
        self.assertTrue(User.objects.filter(username="new-user").exists())
        self.assertTrue(Journal.objects.filter(owner__username="new-user", is_personal=True).exists())

    def test_login_page_is_available(self):
        response = self.client.get(reverse("login"))

        self.assertEqual(response.status_code, 200)

    def test_workspace_requires_login(self):
        response = self.client.get(reverse("workspace"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_login_and_logout_flow(self):
        user = User.objects.create_user(username="member", password="Password123!")

        login_response = self.client.post(
            reverse("login"),
            {"username": user.username, "password": "Password123!"},
        )
        self.assertRedirects(login_response, reverse("workspace"))

        workspace_response = self.client.get(reverse("workspace"))
        self.assertEqual(workspace_response.status_code, 200)
        self.assertContains(workspace_response, "Your workspace")

        logout_response = self.client.post(reverse("logout"))
        self.assertRedirects(logout_response, reverse("feed"))

    def test_public_feed_is_accessible_without_login(self):
        owner = User.objects.create_user(username="author", password="Password123!")
        Publication.objects.create(
            owner=owner,
            title="Visible story",
            content="Public text",
            status=Publication.Status.PUBLISHED,
            visibility=Publication.Visibility.PUBLIC,
        )

        response = self.client.get(reverse("public-feed"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Visible story")


class PostTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="author", password="Password123!")
        self.viewer = User.objects.create_user(username="viewer", password="Password123!")
        self.public_post = Post.objects.create(
            owner=self.owner,
            title="Public note",
            content="Hello public feed",
            visibility=Post.Visibility.PUBLIC,
        )
        self.auth_post = Post.objects.create(
            owner=self.owner,
            title="Auth note",
            content="Hello members",
            visibility=Post.Visibility.AUTH_ONLY,
        )

    def test_anonymous_feed_only_shows_public_posts(self):
        response = self.client.get(reverse("public-feed"))

        self.assertContains(response, "Public note")
        self.assertNotContains(response, "Auth note")

    def test_authenticated_feed_shows_auth_only_posts(self):
        self.client.login(username="viewer", password="Password123!")

        response = self.client.get(reverse("public-feed"))

        self.assertContains(response, "Public note")
        self.assertContains(response, "Auth note")

    def test_authenticated_user_can_create_post(self):
        self.client.login(username="author", password="Password123!")

        response = self.client.post(
            reverse("post-create"),
            {
                "title": "Fresh post",
                "content": "Body",
                "visibility": Post.Visibility.AUTH_ONLY,
            },
        )

        created = Post.objects.get(title="Fresh post")
        self.assertRedirects(response, reverse("post-detail", args=[created.pk]))
        self.assertEqual(created.owner, self.owner)
