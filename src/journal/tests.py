from django.contrib.auth.models import User
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from journal.models import Journal, JournalEntry


class JournalModelTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="Password123!")

    def test_journal_can_be_created_for_user(self):
        journal = Journal.objects.get_or_create_for_user(self.owner)

        self.assertEqual(journal.owner, self.owner)
        self.assertEqual(journal.title, "My Journal")

    def test_one_journal_per_user_constraint_is_enforced(self):
        Journal.objects.create(owner=self.owner, title="First")

        with self.assertRaises(IntegrityError):
            Journal.objects.create(owner=self.owner, title="Second")

    def test_entry_timestamps_are_populated(self):
        journal = Journal.objects.get_or_create_for_user(self.owner)

        entry = JournalEntry.objects.create(journal=journal, title="Note", content="Body")

        self.assertIsNotNone(entry.created_at)
        self.assertIsNotNone(entry.updated_at)

    def test_entry_ordering_is_newest_first(self):
        journal = Journal.objects.get_or_create_for_user(self.owner)
        older = JournalEntry.objects.create(journal=journal, title="Older", content="First")
        newer = JournalEntry.objects.create(journal=journal, title="Newer", content="Second")

        entries = list(JournalEntry.objects.all())

        self.assertEqual(entries[0], newer)
        self.assertEqual(entries[1], older)


class JournalViewTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="Password123!")
        self.other_user = User.objects.create_user(username="other", password="Password123!")
        self.staff = User.objects.create_superuser(
            username="admin",
            password="Password123!",
            email="admin@example.com",
        )
        self.journal = Journal.objects.create(owner=self.owner, title="My Journal")
        self.entry = JournalEntry.objects.create(
            journal=self.journal,
            title="Daily note",
            content="Private thoughts",
        )

    def test_anonymous_users_are_redirected_to_login(self):
        response = self.client.get(reverse("journal:journal-list"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_first_authenticated_visit_creates_journal_automatically(self):
        self.client.login(username="other", password="Password123!")

        response = self.client.get(reverse("journal:journal-list"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Journal.objects.filter(owner=self.other_user).exists())
        self.assertContains(response, "No journal entries yet.")

    def test_authenticated_user_can_create_entry_in_their_journal(self):
        self.client.login(username="other", password="Password123!")

        response = self.client.post(
            reverse("journal:journal-entry-create"),
            {"title": "My entry", "content": "A new thought"},
        )

        entry = JournalEntry.objects.get(title="My entry")
        self.assertRedirects(response, reverse("journal:journal-entry-detail", args=[entry.pk]))
        self.assertEqual(entry.journal.owner, self.other_user)

    def test_owner_can_view_edit_and_delete_own_entry(self):
        self.client.login(username="owner", password="Password123!")

        detail_response = self.client.get(reverse("journal:journal-entry-detail", args=[self.entry.pk]))
        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, self.entry.content)

        edit_response = self.client.post(
            reverse("journal:journal-entry-edit", args=[self.entry.pk]),
            {"title": "Updated note", "content": "Updated thoughts"},
        )
        self.assertRedirects(edit_response, reverse("journal:journal-entry-detail", args=[self.entry.pk]))

        self.entry.refresh_from_db()
        self.assertEqual(self.entry.title, "Updated note")

        delete_response = self.client.post(reverse("journal:journal-entry-delete", args=[self.entry.pk]))
        self.assertRedirects(delete_response, reverse("journal:journal-list"))
        self.assertFalse(JournalEntry.objects.filter(pk=self.entry.pk).exists())

    def test_other_authenticated_users_cannot_view_or_edit_entries(self):
        self.client.login(username="other", password="Password123!")

        detail_response = self.client.get(reverse("journal:journal-entry-detail", args=[self.entry.pk]))
        edit_response = self.client.get(reverse("journal:journal-entry-edit", args=[self.entry.pk]))
        delete_response = self.client.get(reverse("journal:journal-entry-delete", args=[self.entry.pk]))

        self.assertEqual(detail_response.status_code, 404)
        self.assertEqual(edit_response.status_code, 404)
        self.assertEqual(delete_response.status_code, 404)

    def test_staff_users_are_also_restricted(self):
        self.client.login(username="admin", password="Password123!")

        response = self.client.get(reverse("journal:journal-entry-detail", args=[self.entry.pk]))

        self.assertEqual(response.status_code, 404)
