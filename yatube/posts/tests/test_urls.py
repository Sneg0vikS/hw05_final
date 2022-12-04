from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User

INDEX_URL = reverse("posts:index")
CREATE_URL = reverse("posts:post_create")
LOGIN_URL = reverse("users:login")
NEXT = "?next="
FOLLOW_INDEX_URL = reverse("posts:follow_index")
PASSWORD_CHANGE_URL = reverse("users:password_change_form")
PROFILE_URL = reverse('posts:profile')


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group)

        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        cls.GROUP_SLUG_URL = reverse("posts:group_list", args=[cls.group.slug])
        cls.PROFILE_URL = reverse("posts:profile", args=[cls.user.username])
        cls.POST_URL = reverse("posts:post_detail", args=[cls.post.id])
        cls.POST_EDIT_URL = reverse("posts:post_edit", args=[cls.post.id])
        cls.COMMENT_ADD_URL = reverse("posts:add_comment", args=[cls.post.id])
        cls.FOLLOW_PROFILE_URL = reverse("posts:profile_follow",
                                         args=[cls.user.username])
        cls.UNFOLLOW_PROFILE_URL = reverse("posts:profile_unfollow",
                                           args=[cls.user.username])

    def test_urls_access(self):
        """Страницы доступные всем пользователям"""
        url_cases = (
            (INDEX_URL, self.client),
            (self.GROUP_SLUG_URL, self.client),
            (self.PROFILE_URL, self.client),
            (self.POST_URL, self.client),
            (CREATE_URL, self.authorized_client),
        )
        for url_case in url_cases:
            with self.subTest(url_case=url_case):
                response = url_case[1].get(url_case[0])
                error_text = f'url {url_case[0]} не доступен'
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    error_text
                )

    def test_unexisting_page_url(self):
        response = self.client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_redirects_anonymous_on_admin_login(self):
        """Редирект неавторизованного пользователя"""
        test_redirects = (
            CREATE_URL,
            self.POST_EDIT_URL,
            self.COMMENT_ADD_URL,
            FOLLOW_INDEX_URL,
            self.FOLLOW_PROFILE_URL,
            self.UNFOLLOW_PROFILE_URL,
            PASSWORD_CHANGE_URL,
        )
        for url in test_redirects:
            redirect_url = LOGIN_URL + NEXT + url
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)

    def post_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            INDEX_URL: 'posts/index.html',
            self.GROUP_SLUG_URL: 'posts/group_list.html',
            PROFILE_URL: 'posts/profile.html',
            self.POST_URL: 'posts/post_detail.html',
            CREATE_URL: 'posts/post_create_.html',
            self.POST_EDIT_URL: 'posts/post_create_.html',
            FOLLOW_INDEX_URL: 'posts/follow.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(template=template):
                self.assertTemplateUsed(self.authorized_client.get(address),
                                        template)
