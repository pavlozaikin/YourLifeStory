from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from core.models import SiteSettings
from journal.models import Journal, JournalEntry


class JournalModelTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="Password123!")
        self.collaborator = User.objects.create_user(username="collab", password="Password123!")

    def test_journal_can_be_created_for_user(self):
        journal = Journal.objects.get_or_create_personal_journal(self.owner)

        self.assertEqual(journal.owner, self.owner)
        self.assertEqual(journal.title, "Personal Journal")
        self.assertTrue(journal.is_personal)

    def test_only_one_personal_journal_is_created_for_owner(self):
        first = Journal.objects.get_or_create_personal_journal(self.owner)
        second = Journal.objects.get_or_create_personal_journal(self.owner)

        self.assertEqual(first.pk, second.pk)

    def test_user_can_have_multiple_non_personal_journals(self):
        Journal.objects.get_or_create_personal_journal(self.owner)
        Journal.objects.create(owner=self.owner, title="Travel notes")
        Journal.objects.create(owner=self.owner, title="Research log")

        self.assertEqual(Journal.objects.filter(owner=self.owner).count(), 3)

    def test_entry_timestamps_are_populated(self):
        journal = Journal.objects.get_or_create_personal_journal(self.owner)
        entry = JournalEntry.objects.create(title="Note", content="Body")
        entry.journals.add(journal)

        self.assertIsNotNone(entry.created_at)
        self.assertIsNotNone(entry.updated_at)

    def test_entry_ordering_is_newest_first(self):
        journal = Journal.objects.get_or_create_personal_journal(self.owner)
        older = JournalEntry.objects.create(title="Older", content="First")
        older.journals.add(journal)
        newer = JournalEntry.objects.create(title="Newer", content="Second")
        newer.journals.add(journal)

        entries = list(JournalEntry.objects.all())

        self.assertEqual(entries[0], newer)
        self.assertEqual(entries[1], older)

    def test_shared_entry_can_be_viewed_by_invited_user(self):
        journal = Journal.objects.get_or_create_personal_journal(self.owner)
        entry = JournalEntry.objects.create(
            title="Shared",
            content="Body",
            visibility=JournalEntry.Visibility.SHARED,
        )
        entry.journals.add(journal)
        entry.shared_with.add(self.collaborator)

        self.assertTrue(entry.can_view(self.collaborator))
        self.assertTrue(entry.can_edit(self.collaborator))


class JournalViewTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="Password123!")
        self.other_user = User.objects.create_user(username="other", password="Password123!")
        self.staff = User.objects.create_superuser(
            username="admin",
            password="Password123!",
            email="admin@example.com",
        )
        self.journal = Journal.objects.create(owner=self.owner, title="Personal Journal", is_personal=True)
        self.extra_journal = Journal.objects.create(owner=self.owner, title="Travel Journal")
        self.entry = JournalEntry.objects.create(
            title="Daily note",
            content="Private thoughts",
        )
        self.entry.journals.add(self.journal)

    def test_anonymous_users_are_redirected_to_login(self):
        response = self.client.get(reverse("journal:journal-list"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_first_authenticated_visit_creates_personal_journal_automatically(self):
        self.client.login(username="other", password="Password123!")

        response = self.client.get(reverse("journal:journal-list"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Journal.objects.filter(owner=self.other_user, is_personal=True).exists())
        self.assertContains(response, "Personal Journal")

    def test_authenticated_user_can_create_entry_in_their_personal_journal(self):
        self.client.login(username="other", password="Password123!")
        other_personal = Journal.objects.get_or_create_personal_journal(self.other_user)

        response = self.client.post(
            reverse("journal:journal-entry-create"),
            {
                "title": "My entry",
                "content": "A new thought",
                "visibility": JournalEntry.Visibility.PRIVATE,
            },
        )

        entry = JournalEntry.objects.get(title="My entry")
        self.assertRedirects(response, reverse("journal:journal-entry-detail", args=[entry.pk]))
        self.assertTrue(entry.journals.filter(pk=other_personal.pk).exists())

    def test_entry_can_be_added_to_multiple_journals(self):
        self.client.login(username="owner", password="Password123!")

        response = self.client.post(
            reverse("journal:journal-entry-create"),
            {
                "title": "Trip log",
                "content": "A new thought",
                "visibility": JournalEntry.Visibility.PRIVATE,
                "journals": [self.extra_journal.pk],
            },
        )

        entry = JournalEntry.objects.get(title="Trip log")
        self.assertRedirects(response, reverse("journal:journal-entry-detail", args=[entry.pk]))
        self.assertEqual(entry.journals.count(), 2)
        self.assertTrue(entry.journals.filter(pk=self.journal.pk).exists())
        self.assertTrue(entry.journals.filter(pk=self.extra_journal.pk).exists())

    def test_owner_can_view_edit_and_delete_own_entry(self):
        self.client.login(username="owner", password="Password123!")

        detail_response = self.client.get(reverse("journal:journal-entry-detail", args=[self.entry.pk]))
        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, self.entry.content)

        edit_response = self.client.post(
            reverse("journal:journal-entry-edit", args=[self.entry.pk]),
            {
                "title": "Updated note",
                "content": "Updated thoughts",
                "visibility": JournalEntry.Visibility.PRIVATE,
            },
        )
        self.assertRedirects(edit_response, reverse("journal:journal-entry-detail", args=[self.entry.pk]))

        self.entry.refresh_from_db()
        self.assertEqual(self.entry.title, "Updated note")

        delete_response = self.client.post(reverse("journal:journal-entry-delete", args=[self.entry.pk]))
        self.assertRedirects(delete_response, reverse("journal:journal-list"))
        self.assertFalse(JournalEntry.objects.filter(pk=self.entry.pk).exists())

    def test_other_authenticated_users_cannot_view_or_edit_private_entries(self):
        self.client.login(username="other", password="Password123!")

        detail_response = self.client.get(reverse("journal:journal-entry-detail", args=[self.entry.pk]))
        edit_response = self.client.get(reverse("journal:journal-entry-edit", args=[self.entry.pk]))
        delete_response = self.client.get(reverse("journal:journal-entry-delete", args=[self.entry.pk]))

        self.assertEqual(detail_response.status_code, 404)
        self.assertEqual(edit_response.status_code, 404)
        self.assertEqual(delete_response.status_code, 404)

    def test_shared_user_can_view_and_edit_shared_entry(self):
        self.entry.visibility = JournalEntry.Visibility.SHARED
        self.entry.save()
        self.entry.shared_with.add(self.other_user)
        self.client.login(username="other", password="Password123!")

        detail_response = self.client.get(reverse("journal:journal-entry-detail", args=[self.entry.pk]))
        edit_response = self.client.post(
            reverse("journal:journal-entry-edit", args=[self.entry.pk]),
            {
                "title": "Shared note",
                "content": "Updated by collaborator",
                "visibility": JournalEntry.Visibility.SHARED,
                "shared_with": [self.other_user.pk],
            },
        )

        self.entry.refresh_from_db()
        self.assertEqual(detail_response.status_code, 200)
        self.assertRedirects(edit_response, reverse("journal:journal-entry-detail", args=[self.entry.pk]))
        self.assertEqual(self.entry.title, "Shared note")

    def test_staff_users_are_also_restricted(self):
        self.client.login(username="admin", password="Password123!")

        response = self.client.get(reverse("journal:journal-entry-detail", args=[self.entry.pk]))

        self.assertEqual(response.status_code, 404)

    def test_journal_entry_download_returns_markdown(self):
        settings = SiteSettings.get_solo()
        settings.default_country_name = "Poland"
        settings.default_country_emoji = "🇵🇱"
        settings.save()
        self.client.login(username="owner", password="Password123!")

        response = self.client.get(reverse("journal:journal-entry-download", args=[self.entry.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/markdown", response["Content-Type"])
        self.assertIn(".md", response["Content-Disposition"])
        self.assertContains(response, 'Country: "[[Poland|🇵🇱]]"', status_code=200)
