from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from posts.models import Group, Post, User

User = get_user_model()


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

    def setUp(self):
        self.guest_client = self.client
        self.user = PostURLTests.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    # если я правильно понял то в ревью замечание сделать надо было так?
    def test_guest_urls_access(self):
        """Страницы доступные всем пользователям"""
        url_names = (
            '/',
            f'/group/{self.group.slug}/',
            '/profile/auth/',
            f'/posts/{self.post.id}/',
        )
        for url_name in url_names:
            with self.subTest(url_name=url_name):
                response = self.client.get(url_name)
                error_acces = f'url {url_name}, не доступен'
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    error_acces
                )

    def test_autorized_client_urls_access(self):
        """Страницы доступные авторизированному пользователю"""
        url_names = (
            '/',
            '/create/',
            f'/group/{self.group.slug}/',
            '/profile/auth/',
            f'/posts/{self.post.id}/',
        )
        for url_name in url_names:
            with self.subTest(url_name=url_name):
                response = self.authorized_client.get(url_name)
                error_acces = f'url {url_name}, не доступен'
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    error_acces
                )

    def test_unexisting_page_url(self):
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_redirects_anonymous_on_admin_login(self):
        """Редирект неавторизованного пользователя"""
        test_redirect = {
            '/create/': '/auth/login/?next=/create/',
            f'/posts/{self.post.id}/edit/':
                f'/auth/login/?next=/posts/{self.post.id}/edit/'}
        for urls, redirect_url in test_redirect.items():
            with self.subTest(urls=urls):
                response = self.guest_client.get(urls)
                self.assertRedirects(response, redirect_url)

    def post_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            '/profile/auth/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/post_create_.html',
            f'/posts/{self.post.id}/edit/': 'posts/post_create_.html'}
        for address, template in templates_url_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
