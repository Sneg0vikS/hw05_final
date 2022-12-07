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
USERNAME2 = "auth2"
GROUP_SLUG = "test-slug"
GROUP2_SLUG = "test-slug-2"
INDEX_URL = reverse("posts:index")
PROFILE_URL = reverse("posts:profile", kwargs={"username": USERNAME})
GROUP_URL = reverse("posts:group_list", kwargs={"slug": GROUP_SLUG})
GROUP2_URL = reverse("posts:group_list", kwargs={"slug": GROUP2_SLUG})
FOLLOW_INDEX_URL = reverse("posts:follow_index")
POST_CREATE_URL = reverse("posts:post_create")
POSTS_PER_PAGE2 = 1
FOLLOW_SECOND_USER_URL = reverse(
    "posts:profile_follow", kwargs={"username": USERNAME2}
)
UNFOLLOW_SECOND_USER_URL = reverse(
    "posts:profile_unfollow", kwargs={"username": USERNAME2}
)


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
            slug=GROUP2_SLUG,
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовый пост",
            group=cls.group,
            image=cls.uploaded,
        )
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.authorized_client2 = Client()
        cls.authorized_client2.force_login(cls.user2)

        cls.POST_EDIT_URL = reverse("posts:post_edit", kwargs={"post_id":
                                                               cls.post.pk})
        cls.POST_DETAIL_URL = reverse(
            "posts:post_detail", kwargs={"post_id": cls.post.pk}
        )

    def test_pages_show_correct_post(self):
        """Шаблоны, содержащие пост сформированы с правильными полями поста."""
        url_list = (
            (INDEX_URL, self.authorized_client, True),
            (GROUP_URL, self.authorized_client, True),
            (PROFILE_URL, self.authorized_client, True),
            (FOLLOW_INDEX_URL, self.authorized_client2, True),
            (self.POST_DETAIL_URL, self.authorized_client, False)
        )
        Follow.objects.create(user=self.user2, author=self.user)
        for url, client, with_paginator in url_list:
            with self.subTest(url=url):
                response = client.get(url)
                if with_paginator:
                    page_obj = response.context.get("page_obj")
                    self.assertEqual(len(page_obj), 1)
                    post = page_obj[0]
                else:
                    post = response.context.get("post")
                self.assertEqual(self.post, post)
                self.assertEqual(self.post.text, post.text)
                self.assertEqual(self.post.group, post.group)
                self.assertEqual(self.post.image, post.image)
                self.assertEqual(self.post.author, post.author)

    def test_check_post_not_in_mistake_page(self):
        """Проверка созданного Поста группы, чтоб не попал в чужую группу."""
        cases = (
            (GROUP2_URL, self.authorized_client),
            (FOLLOW_INDEX_URL, self.authorized_client2),
        )
        for url, client in cases:
            with self.subTest(url=url):
                response = client.get(url)
                self.assertNotIn(self.post, response.context["page_obj"])

    def test_cache(self):
        """Тест по кэшу index"""
        post_cache = self.authorized_client.post(INDEX_URL)
        post_1 = Post.objects.get(id=self.post.id)
        post_1.text = "Текст для кэша"
        post_1.save()
        post_cache_2 = self.authorized_client.get(INDEX_URL)
        self.assertEqual(post_cache.content, post_cache_2.content)
        cache.clear()
        post_cache_3 = self.authorized_client.get(INDEX_URL)
        self.assertNotEqual(post_cache.content, post_cache_3.content)

    def test_author_in_profile_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        self.assertEqual(self.user, self.authorized_client.get(PROFILE_URL).
                         context.get("author"))

    def test_group_in_group_list(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(GROUP_URL)
        group = response.context.get("group")
        self.assertEqual(self.group, group)
        self.assertEqual(self.group.title, group.title)
        self.assertEqual(self.group.description, group.description)
        self.assertEqual(self.group.slug, group.slug)


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
            (
                Post(
                    author=cls.user,
                    group=Group.objects.get(title="Тестовая группа"),
                    text="Текст",
                )
                for _ in range(POSTS_PER_PAGE + POSTS_PER_PAGE2)
            )
        )

        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.authorized_client2 = Client()
        cls.authorized_client2.force_login(cls.user2)

    def test_pages_contain_required_records(self):
        pages_names = (
            (INDEX_URL, self.authorized_client, POSTS_PER_PAGE),
            (GROUP_URL, self.authorized_client, POSTS_PER_PAGE),
            (PROFILE_URL, self.authorized_client, POSTS_PER_PAGE),
            (FOLLOW_INDEX_URL, self.authorized_client2, POSTS_PER_PAGE),
            (INDEX_URL + "?page=2", self.authorized_client, POSTS_PER_PAGE2),
            (GROUP_URL + "?page=2", self.authorized_client, POSTS_PER_PAGE2),
            (PROFILE_URL + "?page=2", self.authorized_client, POSTS_PER_PAGE2),
            (FOLLOW_INDEX_URL + "?page=2", self.authorized_client2,
             POSTS_PER_PAGE2),
        )
        Follow.objects.create(user=self.user2, author=self.user)
        for url, client, posts_number in pages_names:
            with self.subTest(url=url):
                response = client.get(url)
                self.assertEqual(len(response.context["page_obj"]),
                                 posts_number)


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.first_user = User.objects.create_user(username=USERNAME)
        cls.second_user = User.objects.create_user(username=USERNAME2)
        cls.post = Post.objects.create(text="Тестовый пост", author=cls.
                                       second_user)

        cls.authorized_client_1 = Client()
        cls.authorized_client_1.force_login(cls.first_user)

    def test_subscribe_to_other_users(self):
        """Авторизованный пользователь может подписаться на автора."""
        self.authorized_client_1.get(FOLLOW_SECOND_USER_URL)
        self.assertTrue(
            Follow.objects.filter(
                author=self.second_user, user=self.first_user
            ).exists()
        )

    def test_unsubscribe_from_other_users(self):
        """Авторизованный пользователь может отписаться от автора."""
        Follow.objects.create(author=self.second_user, user=self.first_user)
        self.authorized_client_1.get(UNFOLLOW_SECOND_USER_URL)
        self.assertFalse(
            Follow.objects.filter(
                author=self.second_user, user=self.first_user
            ).exists()
        )
