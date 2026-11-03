from unittest.mock import patch
import requests
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from . import services
from .models import BookmarkedProfile


class ServiceTests(TestCase):
    def test_get_user_validation_bad_name(self):
        """Invalid GitHub username pattern raises UserNotFound before any API call."""
        with self.assertRaises(services.UserNotFound):
            services.get_user("bad name!!")

    def test_get_user_not_found_from_api(self):
        """404 status from GitHub raises UserNotFound."""
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 404
            with self.assertRaises(services.UserNotFound):
                services.get_user("nonexistent-test-user-12345")

    def test_get_user_network_error(self):
        """RequestException raises GitHubUnavailable with friendly message."""
        with patch("requests.get", side_effect=requests.exceptions.RequestException("No connection")):
            with self.assertRaises(services.GitHubUnavailable) as ctx:
                services.get_user("anyuser")
            self.assertIn("Could not connect", str(ctx.exception))

    def test_get_user_timeout(self):
        """Timeout raises GitHubUnavailable with friendly timeout message."""
        with patch("requests.get", side_effect=requests.exceptions.Timeout("Timed out")):
            with self.assertRaises(services.GitHubUnavailable) as ctx:
                services.get_user("anyuser")
            self.assertIn("took too long to respond", str(ctx.exception))

    def test_get_user_rate_limited(self):
        """403 with X-RateLimit-Remaining == 0 raises RateLimited."""
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 403
            mock_get.return_value.headers = {"X-RateLimit-Remaining": "0"}
            with self.assertRaises(services.RateLimited) as ctx:
                services.get_user("anyuser")
            self.assertIn("rate limit reached", str(ctx.exception))

    def test_get_repos_parsed_properly(self):
        """get_repos returns cleaned dict with correct keys."""
        mock_data = [
            {
                "name": "cool-repo",
                "description": "A great project",
                "language": "Python",
                "stargazers_count": 42,
                "html_url": "https://github.com/testuser/cool-repo",
            }
        ]
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_data
            repos = services.get_repos("testuser", limit=1)
            self.assertEqual(len(repos), 1)
            self.assertEqual(repos[0]["name"], "cool-repo")
            self.assertEqual(repos[0]["stars"], 42)


class ViewTests(TestCase):
    def setUp(self):
        self.user_a = User.objects.create_user("user_a", password="password123")
        self.user_b = User.objects.create_user("user_b", password="password123")

    def test_search_page_loads(self):
        """Search page responds with 200."""
        response = self.client.get(reverse("search"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "GitHub Profile Viewer")

    def test_search_unknown_user_shows_friendly_message(self):
        """Friendly error message is displayed when user does not exist, no 500."""
        with patch("profiles.services.get_user", side_effect=services.UserNotFound("No GitHub user with that username.")):
            response = self.client.get(reverse("search"), {"q": "this-user-does-not-exist-98765"})
            self.assertEqual(response.status_code, 200)
            messages = [str(m) for m in response.context["messages"]]
            self.assertIn("No GitHub user with that username.", messages)

    def test_search_bad_name_shows_friendly_message(self):
        """Invalid username format shows friendly error message without 500."""
        response = self.client.get(reverse("search"), {"q": "bad name!!"})
        self.assertEqual(response.status_code, 200)
        messages = [str(m) for m in response.context["messages"]]
        self.assertIn("That is not a valid GitHub username.", messages)

    def test_search_offline_shows_friendly_message(self):
        """Simulated offline / network drop displays 'Could not connect' message."""
        with patch("profiles.services.get_user", side_effect=services.GitHubUnavailable("Could not connect to GitHub. Check your internet.")):
            response = self.client.get(reverse("search"), {"q": "torvalds"})
            self.assertEqual(response.status_code, 200)
            messages = [str(m) for m in response.context["messages"]]
            self.assertIn("Could not connect to GitHub. Check your internet.", messages)

    def test_bookmark_requires_login(self):
        """Logged out user attempting to bookmark is redirected to login."""
        response = self.client.post(reverse("bookmark", args=["torvalds"]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/accounts/login/") or response.url.startswith(reverse("login")))

    def test_bookmarks_page_requires_login(self):
        """Logged out user visiting /bookmarks/ is redirected to login."""
        response = self.client.get(reverse("bookmarks"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue("/accounts/login/" in response.url or reverse("login") in response.url)

    def test_bookmark_twice_creates_one_row(self):
        """Bookmarking the same user twice only creates one database record."""
        self.client.login(username="user_a", password="password123")
        profile_data = {
            "username": "torvalds",
            "name": "Linus Torvalds",
            "avatar_url": "https://avatars.githubusercontent.com/u/1024025",
            "bio": "Linux creator",
            "public_repos": 10,
            "followers": 200000,
            "html_url": "https://github.com/torvalds",
        }
        with patch("profiles.services.get_user", return_value=profile_data):
            self.client.post(reverse("bookmark", args=["torvalds"]))
            self.client.post(reverse("bookmark", args=["torvalds"]))
            self.assertEqual(BookmarkedProfile.objects.filter(user=self.user_a, username="torvalds").count(), 1)

    def test_user_only_sees_own_bookmarks(self):
        """Users only see their own bookmarks on /bookmarks/."""
        b_a = BookmarkedProfile.objects.create(user=self.user_a, username="torvalds")
        b_b = BookmarkedProfile.objects.create(user=self.user_b, username="octocat")

        self.client.login(username="user_a", password="password123")
        response = self.client.get(reverse("bookmarks"))
        self.assertContains(response, "torvalds")
        self.assertNotContains(response, "octocat")

    def test_user_a_cannot_delete_user_b_bookmark_returns_404(self):
        """User A trying to delete User B's bookmark ID returns 404."""
        b_b = BookmarkedProfile.objects.create(user=self.user_b, username="octocat")
        self.client.login(username="user_a", password="password123")
        response = self.client.post(reverse("bookmark_delete", args=[b_b.pk]))
        self.assertEqual(response.status_code, 404)
        # Ensure User B's bookmark is untouched
        self.assertTrue(BookmarkedProfile.objects.filter(pk=b_b.pk).exists())

    def test_bookmark_note_update(self):
        """Bonus feature: user can update personal notes on a bookmark."""
        b_a = BookmarkedProfile.objects.create(user=self.user_a, username="torvalds")
        self.client.login(username="user_a", password="password123")
        response = self.client.post(reverse("bookmark_update_note", args=[b_a.pk]), {"note": "Great developer to follow"})
        self.assertEqual(response.status_code, 302)
        b_a.refresh_from_db()
        self.assertEqual(b_a.note, "Great developer to follow")
