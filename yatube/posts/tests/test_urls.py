from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User

INDEX_URL = reverse("posts:index")
CREATE_URL = reverse("posts:post_create")
LOGIN_URL = reverse("users:login")
NEXT = "?next="
FOLLOW_INDEX_URL = reverse("posts:follow_index")
GROUP_SLUG = "test-slug"
GROUP_SLUG_URL = reverse("posts:group_list", args=[GROUP_SLUG])
GROUP_WRONG_SLUG_URL = reverse("posts:group_list", args=["wrong"])
USERNAME = "auth"
PROFILE_URL = reverse("posts:profile", args=[USERNAME])
PROFILE_WRONG_URL = reverse("posts:profile", args=["wrong"])
FOLLOW_PROFILE_URL = reverse("posts:profile_follow", args=[USERNAME])
UNFOLLOW_PROFILE_URL = reverse("posts:profile_unfollow", args=[USERNAME])
POST_WRONG_URL = reverse("posts:post_detail", args=[99])
POST_EDIT_WRONG_URL = reverse("posts:post_edit", args=[99])


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.user2 = User.objects.create_user(username=USERNAME + "-2")
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=GROUP_SLUG,
            description='Тестовое описание')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group)

        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.authorized_client2 = Client()
        cls.authorized_client2.force_login(cls.user2)

        cls.POST_URL = reverse("posts:post_detail", args=[cls.post.id])
        cls.POST_EDIT_URL = reverse("posts:post_edit", args=[cls.post.id])

    def test_urls_response_correct_status(self):
        """В ответах корректный код состояния"""
        url_cases = (
            (INDEX_URL, self.client, HTTPStatus.OK),
            (GROUP_SLUG_URL, self.client, HTTPStatus.OK),
            (GROUP_WRONG_SLUG_URL, self.client, HTTPStatus.NOT_FOUND),
            (PROFILE_URL, self.client, HTTPStatus.OK),
            (PROFILE_WRONG_URL, self.client, HTTPStatus.NOT_FOUND),
            (self.POST_URL, self.client, HTTPStatus.OK),
            (POST_WRONG_URL, self.client, HTTPStatus.NOT_FOUND),
            (CREATE_URL, self.authorized_client, HTTPStatus.OK),
            (self.POST_EDIT_URL, self.authorized_client, HTTPStatus.OK),
            (POST_EDIT_WRONG_URL, self.authorized_client,
             HTTPStatus.NOT_FOUND),
            (FOLLOW_INDEX_URL, self.authorized_client, HTTPStatus.OK),
            ("/nonexistent_page/", self.client, HTTPStatus.NOT_FOUND),

            (CREATE_URL, self.client, HTTPStatus.FOUND),
            (self.POST_EDIT_URL, self.client, HTTPStatus.FOUND),
            (FOLLOW_INDEX_URL, self.client, HTTPStatus.FOUND),
            (FOLLOW_PROFILE_URL, self.client, HTTPStatus.FOUND),
            (UNFOLLOW_PROFILE_URL, self.client, HTTPStatus.FOUND),
            (self.POST_EDIT_URL, self.authorized_client2, HTTPStatus.FOUND),
            (FOLLOW_PROFILE_URL, self.authorized_client2, HTTPStatus.FOUND),
            (UNFOLLOW_PROFILE_URL, self.authorized_client2, HTTPStatus.FOUND),
            (FOLLOW_PROFILE_URL, self.authorized_client, HTTPStatus.FOUND),
        )
        for url, client, status in url_cases:
            with self.subTest(url=url):
                self.assertEqual(
                    client.get(url).status_code,
                    status,
                )

    def test_redirects(self):
        """Редирект неавторизованного пользователя"""
        test_redirects = (
            (CREATE_URL, LOGIN_URL + NEXT + CREATE_URL, self.client),
            (self.POST_EDIT_URL, LOGIN_URL + NEXT + self.POST_EDIT_URL,
             self.client),
            (FOLLOW_INDEX_URL, LOGIN_URL + NEXT + FOLLOW_INDEX_URL,
             self.client),
            (FOLLOW_PROFILE_URL, LOGIN_URL + NEXT + FOLLOW_PROFILE_URL,
             self.client),
            (UNFOLLOW_PROFILE_URL, LOGIN_URL + NEXT + UNFOLLOW_PROFILE_URL,
             self.client),
            (self.POST_EDIT_URL, self.POST_URL, self.authorized_client2),
            (FOLLOW_PROFILE_URL, PROFILE_URL, self.authorized_client2),
            (UNFOLLOW_PROFILE_URL, PROFILE_URL, self.authorized_client2),
            (FOLLOW_PROFILE_URL, PROFILE_URL, self.authorized_client),
        )
        for url, redirect_url, client in test_redirects:
            with self.subTest(url=url, client=client):
                self.assertRedirects(client.get(url), redirect_url)

    def test_post_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            INDEX_URL: 'posts/index.html',
            GROUP_SLUG_URL: 'posts/group_list.html',
            PROFILE_URL: 'posts/profile.html',
            self.POST_URL: 'posts/post_detail.html',
            CREATE_URL: 'posts/post_create.html',
            self.POST_EDIT_URL: 'posts/post_create.html',
            FOLLOW_INDEX_URL: 'posts/follow.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(template=template):
                self.assertTemplateUsed(self.authorized_client.get(address),
                                        template)
