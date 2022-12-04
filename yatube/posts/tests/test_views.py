from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User, Follow
from ..settings import POSTS_PER_PAGE

SMALL_GIF = (
    b"\x47\x49\x46\x38\x39\x61\x02\x00"
    b"\x01\x00\x80\x00\x00\x00\x00\x00"
    b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
    b"\x00\x00\x00\x2C\x00\x00\x00\x00"
    b"\x02\x00\x01\x00\x00\x02\x02\x0C"
    b"\x0A\x00\x3B"
)

USERNAME = "auth"
GROUP_SLUG = "test-slug"
INDEX_URL = reverse("posts:index")
PROFILE_URL = reverse("posts:profile", kwargs={"username": USERNAME})
GROUP_URL = reverse("posts:group_list", kwargs={"slug": GROUP_SLUG})
FOLLOW_INDEX_URL = reverse("posts:follow_index")
POST_CREATE_URL = reverse("posts:post_create")
GENERATE_POSTS_NUMBER = POSTS_PER_PAGE + 1


class PostViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.uploaded = SimpleUploadedFile(
            name="small.gif", content=SMALL_GIF, content_type="image/gif"
        )
        cls.user = User.objects.create_user(username=USERNAME)
        cls.user2 = User.objects.create_user(username=USERNAME + "2")
        cls.group = Group.objects.create(
            title="Тестовая группа", slug=GROUP_SLUG,
            description="Тестовое описание"
        )
        cls.group2 = Group.objects.create(
            title="Тестовая группа #2",
            slug=GROUP_SLUG + "-2",
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовый пост",
            group=cls.group,
            image=cls.uploaded,
        )
        cls.authorized_client2 = Client()
        cls.authorized_client2.force_login(cls.user2)

        cls.POST_EDIT_URL = reverse("posts:post_edit", kwargs={"post_id":
                                                               cls.post.pk})
        cls.POST_DETAIL_URL = reverse(
            "posts:post_detail", kwargs={"post_id": cls.post.pk}
        )
        cls.GROUP2_URL = reverse("posts:group_list", args=[cls.group2.slug])

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_show_correct_context(self):
        """Шаблоны index, group_list, profile сформированы с
         правильным контекстом."""
        url_list = (
            (INDEX_URL, self.authorized_client),
            (GROUP_URL, self.authorized_client),
            (PROFILE_URL, self.authorized_client),
            (FOLLOW_INDEX_URL, self.authorized_client2),
        )
        Follow.objects.create(user=self.user2, author=self.user)
        for url, client in url_list:
            with self.subTest(url=url):
                response = client.get(url)
                page_obj = response.context.get("page_obj")
                page_post = page_obj[0]
                self.assertIn(self.post, page_obj)
                self.assertEqual(self.post.pub_date, page_post.pub_date)
                self.assertEqual(self.post.text, page_post.text)
                self.assertEqual(self.post.image, page_post.image)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(self.POST_DETAIL_URL)
        page_post = response.context.get("post")
        self.assertEqual(self.post.pub_date, page_post.pub_date)
        self.assertEqual(self.post.text, page_post.text)
        self.assertEqual(self.post.image, page_post.image)

    def test_check_post_not_in_mistake_group_list_page(self):
        """Проверка созданного Поста группы, чтоб не попал в чужую группу."""
        response = self.authorized_client.get(GROUP_URL)
        self.assertIn(self.post, response.context["page_obj"])
        response_2 = self.authorized_client.get(self.GROUP2_URL)
        self.assertNotIn(self.post, response_2.context["page_obj"])

    def test_cache(self):
        """Тест по кэшу index"""
        post_cache = self.authorized_client.post(INDEX_URL)
        post_1 = Post.objects.get(id=self.post.id)
        post_1.text = "Текст для кэша"
        post_1.save()
        post_cache_2 = self.authorized_client.get(INDEX_URL)
        self.assertAlmostEqual(post_cache.content, post_cache_2.content)
        cache.clear()
        post_cache_3 = self.authorized_client.get(INDEX_URL)
        self.assertNotEqual(post_cache.content, post_cache_3.content)


class PaginatorViewsTest(TestCase):
    """Создаем класс для проверки Paginator"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="auth")
        cls.user2 = User.objects.create_user(username="auth2")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание",
        )
        Post.objects.bulk_create(
            [
                Post(
                    author=cls.user,
                    group=Group.objects.get(title="Тестовая группа"),
                    text="Текст",
                )
                for _ in range(GENERATE_POSTS_NUMBER)
            ]
        )

        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.authorized_client2 = Client()
        cls.authorized_client2.force_login(cls.user2)

    def test_pages_contain_required_records(self):
        pages_names = (
            (INDEX_URL, self.authorized_client),
            (GROUP_URL, self.authorized_client),
            (PROFILE_URL, self.authorized_client),
            (FOLLOW_INDEX_URL, self.authorized_client2),
        )
        Follow.objects.create(user=self.user2, author=self.user)
        for url, client in pages_names:
            with self.subTest(url=url):
                response = client.get(url)
                self.assertEqual(response.status_code, 200)
                # Проверка: количество постов на первой странице равно 10.
                self.assertEqual(len(response.context["page_obj"]),
                                 POSTS_PER_PAGE)
                # Проверка: на второй странице должен быть один пост.
                response = client.get(url + "?page=2")
                self.assertEqual(
                    len(response.context["page_obj"]),
                    GENERATE_POSTS_NUMBER - POSTS_PER_PAGE,
                )


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.first_user = User.objects.create_user(username="first_user")
        cls.second_user = User.objects.create_user(username="second_user")
        cls.third_user = User.objects.create_user(username="third_user")
        cls.post = Post.objects.create(text="Тестовый пост",
                                       author=cls.second_user)

        cls.authorized_client_1 = Client()
        cls.authorized_client_2 = Client()
        cls.authorized_client_3 = Client()
        cls.authorized_client_1.force_login(cls.first_user)
        cls.authorized_client_2.force_login(cls.second_user)
        cls.authorized_client_3.force_login(cls.third_user)

        cls.FOLLOW_SECOND_USER_URL = reverse(
            "posts:profile_follow", kwargs={"username": cls.second_user}
        )
        cls.UNFOLLOW_SECOND_USER_URL = reverse(
            "posts:profile_unfollow", kwargs={"username": cls.second_user}
        )

    def test_subscribe_to_other_users(self):
        """Авторизованный пользователь может подписаться на автора."""
        self.authorized_client_1.get(self.FOLLOW_SECOND_USER_URL)
        self.assertTrue(
            Follow.objects.filter(
                author=self.second_user, user=self.first_user
            ).exists()
        )

    def test_unsubscribe_from_other_users(self):
        """Авторизованный пользователь может отписаться от автора."""
        Follow.objects.create(author=self.second_user, user=self.first_user)
        self.authorized_client_1.get(self.UNFOLLOW_SECOND_USER_URL)
        self.assertFalse(
            Follow.objects.filter(
                author=self.second_user, user=self.first_user
            ).exists()
        )

    def test_subscribe_to_other_users_not_authorized_client(self):
        """Неавторизованный пользователь не может подписаться на
        автора поста."""
        self.client.get(self.FOLLOW_SECOND_USER_URL)
        self.assertFalse(self.second_user.following.filter(
            user=self.first_user).exists())

    def test_follow_index(self):
        """Новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется в ленте тех, кто не подписан."""

        self.authorized_client_1.get(self.FOLLOW_SECOND_USER_URL)
        response_1 = self.authorized_client_1.get(FOLLOW_INDEX_URL)
        self.assertIn(self.post, response_1.context["page_obj"])
        response_3 = self.authorized_client_3.get(FOLLOW_INDEX_URL)
        self.assertNotIn(self.post, response_3.context["page_obj"])
