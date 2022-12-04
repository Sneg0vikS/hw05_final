from django.test import TestCase
from django.urls import reverse


class RoutesTests(TestCase):
    def test_urls_correctly_resolved(self):
        self.assertEqual(reverse("posts:index"), "/")
        self.assertEqual(reverse("posts:post_edit", args=[1]), "/posts/1/edit/")
        self.assertEqual(reverse("posts:post_create"), "/create/")
        self.assertEqual(reverse("posts:post_detail", args=[1]), "/posts/1/")
        self.assertEqual(reverse("posts:profile", args=["username"]), "/profile/username/")
        self.assertEqual(reverse("posts:add_comment", args=[1]), "/posts/1/comment/")
        self.assertEqual(reverse("posts:group_list", args=["name"]), "/group/name/")
        self.assertEqual(reverse("posts:follow_index"), "/follow/")
        self.assertEqual(
            reverse("posts:profile_follow", args=["username"]), "/profile/username/follow/"
        )
        self.assertEqual(
            reverse("posts:profile_unfollow", args=["username"]), "/profile/username/unfollow/"
        )
