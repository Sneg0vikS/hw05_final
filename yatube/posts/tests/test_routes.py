from django.test import TestCase
from django.urls import reverse
from ..urls import app_name

SLUG = "slug"
ID = 1

ROUTES = (
    ("index", "/", []),
    ("post_edit", f"/posts/{ID}/edit/", [ID]),
    ("post_create", "/create/", []),
    ("post_detail", f"/posts/{ID}/", [ID]),
    ("profile", f"/profile/{SLUG}/", [SLUG]),
    ("add_comment", f"/posts/{ID}/comment/", [ID]),
    ("group_list", f"/group/{SLUG}/", [SLUG]),
    ("follow_index", "/follow/", []),
    ("profile_follow", f"/profile/{SLUG}/follow/", [SLUG]),
    ("profile_unfollow", f"/profile/{SLUG}/unfollow/", [SLUG]),
)


class RoutesTests(TestCase):
    def test_urls_correctly_resolved(self):
        for key, url, args in ROUTES:
            with self.subTest(key=key):
                self.assertEqual(reverse(app_name + ":" + key, args=args), url)
