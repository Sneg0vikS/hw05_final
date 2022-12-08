from django.test import TestCase
from django.urls import reverse

from ..urls import app_name

USERNAME = "username"
SLUG = "slug"
ID = 1

ROUTES = (
    ("index", "/", []),
    ("post_edit", f"/posts/{ID}/edit/", [ID]),
    ("post_create", "/create/", []),
    ("post_detail", f"/posts/{ID}/", [ID]),
    ("profile", f"/profile/{USERNAME}/", [USERNAME]),
    ("add_comment", f"/posts/{ID}/comment/", [ID]),
    ("group_list", f"/group/{SLUG}/", [SLUG]),
    ("follow_index", "/follow/", []),
    ("profile_follow", f"/profile/{USERNAME}/follow/", [USERNAME]),
    ("profile_unfollow", f"/profile/{USERNAME}/unfollow/", [USERNAME]),
)


class RoutesTests(TestCase):
    def test_urls_correctly_resolved(self):
        for key, url, args in ROUTES:
            with self.subTest(key=key):
                self.assertEqual(reverse(f"{app_name}:{key}", args=args), url)
