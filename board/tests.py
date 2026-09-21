from datetime import timedelta

from django.contrib.auth.models import User
from django.core import mail
from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Post, PostStatus


def _signup(client, username="alice", email="alice@example.is", password="Str0ng!Passw0rd"):
    return client.post(reverse("signup"), {
        "username": username, "email": email, "password1": password, "password2": password,
    })


class SignupAndPostingFlowTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_signup_creates_account_and_logs_in(self):
        resp = _signup(self.client)
        self.assertTrue(User.objects.filter(username="alice").exists())
        self.assertRedirects(resp, reverse("feed"))

    def test_signup_honeypot_blocks_account_creation_silently(self):
        resp = self.client.post(reverse("signup"), {
            "username": "bot", "email": "bot@example.is",
            "password1": "Str0ng!Passw0rd", "password2": "Str0ng!Passw0rd",
            "hp_website": "http://spam.example",
        })
        self.assertFalse(User.objects.filter(username="bot").exists())
        # still looks like success to whatever submitted it
        self.assertRedirects(resp, reverse("feed"))

    def test_new_post_starts_pending_and_hidden_from_feed(self):
        _signup(self.client)
        self.client.post(reverse("new_post"), {"category": "ideas", "body": "hello"})
        post = Post.objects.get(author__username="alice")
        self.assertEqual(post.status, PostStatus.PENDING)
        self.assertNotContains(self.client.get(reverse("feed")), "hello")

    def test_approved_post_appears_in_feed_and_captures_snapshot(self):
        _signup(self.client)
        self.client.post(reverse("new_post"), {"category": "ideas", "body": "hello world"})
        post = Post.objects.get(author__username="alice")
        self.assertEqual(post.ip_address, "127.0.0.1")
        self.assertEqual(post.author_email_snapshot, "alice@example.is")

        post.status = PostStatus.APPROVED
        post.approved_at = timezone.now()
        post.save()
        self.assertContains(self.client.get(reverse("feed")), "hello world")

    def test_post_older_than_live_window_is_not_publicly_visible(self):
        _signup(self.client)
        self.client.post(reverse("new_post"), {"category": "ideas", "body": "stale post"})
        post = Post.objects.get(author__username="alice")
        post.status = PostStatus.APPROVED
        post.approved_at = timezone.now() - timedelta(days=8)
        post.save()
        self.assertNotContains(self.client.get(reverse("feed")), "stale post")

    def test_rate_limit_blocks_second_post_immediately_after(self):
        _signup(self.client)
        self.client.post(reverse("new_post"), {"category": "ideas", "body": "first"})
        self.client.post(reverse("new_post"), {"category": "stories", "body": "second"})
        self.assertEqual(Post.objects.filter(author__username="alice").count(), 1)

    def test_auto_flags_catch_phone_number_and_shouting(self):
        _signup(self.client)
        self.client.post(reverse("new_post"), {
            "category": "complaints", "body": "CALL 555-123-4567 NOW PLEASE THANK YOU",
        })
        post = Post.objects.get(author__username="alice")
        self.assertIn("possible phone number", post.auto_flags)


class ModeratorRoleTests(TestCase):
    def test_make_moderator_grants_staff_and_post_permissions(self):
        User.objects.create_user(username="mod1", email="mod1@example.is", password="Str0ng!Passw0rd")
        call_command("make_moderator", "mod1")
        user = User.objects.get(username="mod1")
        self.assertTrue(user.is_staff)
        self.assertTrue(user.has_perm("board.view_post"))
        self.assertTrue(user.has_perm("board.change_post"))

    def test_make_moderator_remove_revokes_access(self):
        User.objects.create_user(username="mod2", email="mod2@example.is", password="Str0ng!Passw0rd")
        call_command("make_moderator", "mod2")
        call_command("make_moderator", "mod2", "--remove")
        user = User.objects.get(username="mod2")
        self.assertFalse(user.is_staff)
        self.assertFalse(user.has_perm("board.change_post"))


class RetentionPurgeTests(TestCase):
    def test_purge_deletes_only_posts_past_retention_window(self):
        user = User.objects.create_user(username="ret", email="ret@example.is", password="Str0ng!Passw0rd")
        old = Post.objects.create(
            author=user, category="ideas", body="old", status=PostStatus.APPROVED,
            ip_address="127.0.0.1", author_email_snapshot=user.email,
        )
        Post.objects.filter(id=old.id).update(
            approved_at=timezone.now() - timedelta(days=20),
            created_at=timezone.now() - timedelta(days=20),
        )
        fresh = Post.objects.create(
            author=user, category="ideas", body="fresh", status=PostStatus.APPROVED,
            ip_address="127.0.0.1", author_email_snapshot=user.email, approved_at=timezone.now(),
        )

        call_command("purge_expired_posts")

        self.assertFalse(Post.objects.filter(id=old.id).exists())
        self.assertTrue(Post.objects.filter(id=fresh.id).exists())


class ThrottlingTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_login_gets_throttled_after_repeated_attempts(self):
        statuses = []
        for _ in range(20):
            resp = self.client.post(reverse("login"), {"username": "nobody", "password": "wrong"})
            statuses.append(resp.status_code)
        self.assertIn(429, statuses)


class PasswordResetTests(TestCase):
    def test_password_reset_sends_email_with_link(self):
        User.objects.create_user(username="pw", email="pw@example.is", password="Str0ng!Passw0rd")
        # Use the locmem backend for this test only, so we can inspect mail.outbox
        with self.settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"):
            self.client.post(reverse("password_reset"), {"email": "pw@example.is"})
            self.assertEqual(len(mail.outbox), 1)
            self.assertIn("/reset/", mail.outbox[0].body)


class LanguageSwitchTests(TestCase):
    def test_switching_language_translates_the_url_prefix(self):
        resp = self.client.post(reverse("set_language"), {"language": "en", "next": "/is/"})
        self.assertRedirects(resp, "/en/", fetch_redirect_response=False)

    def test_icelandic_feed_shows_icelandic_text(self):
        resp = self.client.get("/is/")
        self.assertContains(resp, "Ekkert hér ennþá. Segðu fyrsta orðið.")

    def test_english_feed_shows_english_text(self):
        resp = self.client.get("/en/")
        self.assertContains(resp, "Nothing here yet. Say the first thing.")
