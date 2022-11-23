from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from http import HTTPStatus

from posts.models import Group, Post, Comment
from ..forms import PostForm


TEST_OF_POST: int = 13
User = get_user_model()


class PostViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=cls.uploaded,)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_templates(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}): 'posts/group_list.html',
            reverse('posts:profile', kwargs={
                    'username': self.user.username}): 'posts/profile.html',
            reverse('posts:post_detail', kwargs={
                    'post_id': self.post.id}): 'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={
                    'post_id': self.post.id}): 'posts/post_create.html',
            reverse('posts:post_create'): 'posts/post_create.html'}
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_pages_show_correct_context(self):
        """Шаблоны index, group_list, profile сформированы
        с правильным контекстом.
        """
        pages = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        post_image = Post.objects.first().image
        for reverse_name in pages:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertIn(self.post, response.context.get('page_obj'))
                self.assertEqual(post_image, self.post.image)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk}))
        post_image = Post.objects.first().image
        self.assertEqual(response.context['post'], self.post)
        self.assertEqual(post_image, self.post.image)

    def test__post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        self.assertIsInstance(response.context.get('form'), PostForm)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk})
        )
        self.assertIsInstance(response.context.get('form'), PostForm)
        self.assertEqual(response.context['form'].instance, self.post)

    def test_check_group_in_pages(self):
        """Проверка создания поста на страницах с выбранной группой"""
        pages_1 = {
            reverse("posts:index"): Post.objects.get(group=self.post.group),
            reverse(
                "posts:group_list", kwargs={"slug": self.group.slug}
            ): Post.objects.get(group=self.post.group),
            reverse(
                "posts:profile", kwargs={"username": self.post.author}
            ): Post.objects.get(group=self.post.group),
        }
        for value, expected in pages_1.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                form_field = response.context["page_obj"]
                self.assertIn(expected, form_field)

    def test_check_group_not_in_mistake_group_list_page(self):
        """Проверка созданного Поста группы, чтоб не попап в чужую группу."""
        pages_2 = {
            reverse(
                "posts:group_list", kwargs={"slug": self.group.slug}
            ): Post.objects.exclude(group=self.post.group)}
        for value, expected in pages_2.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                form_field = response.context["page_obj"]
                self.assertNotIn(expected, form_field)

    def test_authorized_client_comments(self):
        """ Комментировать посты может только авторизованный пользователь."""
        self.authorized_client.post(reverse('posts:add_comment',
                                    kwargs={'post_id': self.post.id}),
                                    data={
                                        'text': 'тестовый комментарий'}
                                    ) 
        self.authorized_client.logout()
        self.authorized_client.post(reverse('posts:add_comment',
                                    kwargs={'post_id': self.post.id}),
                                    data={
                                        'text': 'тестовый комментарий 2'}
                                    )
        self.assertTrue(Comment.objects.filter(text='тестовый комментарий')
                        .exists())
        self.assertFalse(Comment.objects.filter(text='тестовый комментарий 2')
                         .exists())

    def test_cache(self):
        """Тест по кэшу index"""
        post_cache = self.authorized_client.post(reverse('posts:index'))
        post_1 = Post.objects.get(id=1)
        post_1.text = 'Текст для кэша'
        post_1.save()
        post_cache_2 = self.authorized_client.get(reverse('posts:index'))
        self.assertAlmostEqual(post_cache.content, post_cache_2.content)
        cache.clear()
        post_cache_3 = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(post_cache.content, post_cache_3.content)

    def test_view_404_error_page(self):
        """Тест 404"""
        response = self.client.get('/nonexist-page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')


class PaginatorViewsTest(TestCase):
    """ Создаем класс для проверки Paginator"""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',)
        Post.objects.bulk_create(
            [Post(author=cls.user,
                  group=Group.objects.get(title='Тестовая группа'),
                  text='Текст',) for i in range(TEST_OF_POST)])

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_contain_required_records(self):
        pages_names = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username})
        ]
        for reverse_name in pages_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                # Проверка: количество постов на первой странице равно 10.
                self.assertEqual(len(response.context['page_obj']), 10)
                # Проверка: на второй странице должно быть три поста.
                response = self.guest_client.get(reverse_name + '?page=2')
                self.assertEqual(len(response.context['page_obj']), 3)


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.first_user = User.objects.create_user(username='first_user')
        cls.second_user = User.objects.create_user(username='second_user')
        cls.third_user = User.objects.create_user(username='third_user')
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.second_user
        )

    def setUp(self):
        self.authorized_client_1 = Client()
        self.authorized_client_2 = Client()
        self.authorized_client_3 = Client()
        self.guest_client = Client()
        self.authorized_client_1.force_login(self.first_user)
        self.authorized_client_2.force_login(self.second_user)
        self.authorized_client_3.force_login(self.third_user)

    def test_subscribe_to_other_users_and_remove_them(self):
        """Авторизованный пользователь может подписаться на автора
        и отписаться от него."""
        count_follow = self.second_user.following.count()
        response = self.authorized_client_1.get(
            reverse(
                'posts:profile_follow', kwargs={'username': self.second_user}
            )
        )
        self.assertRedirects(
            response,
            reverse('posts:follow_index')
        )
        self.assertEqual(
            self.second_user.following.count(), count_follow + 1)

        response = self.authorized_client_1.get(
            reverse(
                'posts:profile_unfollow', kwargs={'username': self.second_user}
            )
        )
        self.assertRedirects(
            response,
            reverse('posts:follow_index')
        )
        self.assertEqual(self.second_user.following.count(), count_follow)

    def test_subscribe_to_other_users_not_authorized_client(self):
        """Не авторизованный пользователь не может
        подписаться на автора поста."""
        count_follow = self.second_user.following.count()
        self.guest_client.get(
            reverse(
                'posts:profile_follow', kwargs={'username': self.second_user}
            )
        )
        self.assertEqual(self.second_user.following.count(), count_follow)

    def test_follow_index(self):
        """Новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется в ленте тех, кто не подписан."""
        count_post_first_user_before = Post.objects.filter(
            author__following__user=self.first_user
        ).count()
        count_post_third_user_before = Post.objects.filter(
            author__following__user=self.third_user
        ).count()
        self.authorized_client_1.get(
            reverse(
                'posts:profile_follow', kwargs={'username': self.second_user}
            )
        )
        count_post_first_user_after = Post.objects.filter(
            author__following__user=self.first_user
        ).count()
        count_post_third_user_after = Post.objects.filter(
            author__following__user=self.third_user
        ).count()
        self.assertEqual(
            count_post_first_user_after, count_post_first_user_before + 1
        )
        self.assertEqual(
            count_post_third_user_after, count_post_third_user_before
        )
