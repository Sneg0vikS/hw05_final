from django.test import TestCase
from django.urls import reverse


class RoutesTests(TestCase):
    def test_urls_correctly_resolved(self):
        routes = (
            ("index", "/", []),
            ("post_edit", "/posts/1/edit/", [1]),
            ("post_create", "/create/", []),
            ("post_detail", "/posts/1/", [1]),
            ("profile", "/profile/username/", ["username"]),
            ("add_comment", "/posts/1/comment/", [1]),
            ("group_list", "/group/name/", ["name"]),
            ("follow_index", "/follow/", []),
            ("profile_follow", "/profile/username/follow/", ["username"]),
            ("profile_unfollow", "/profile/username/unfollow/", ["username"]),
        )
        for name, url, args in routes:
            with self.subTest(route=name):
                self.assertEqual(reverse("posts:" + name, args=args), url)
