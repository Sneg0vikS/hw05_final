from django.test import TestCase
from django.utils import translation

from ..models import Group, Post, User, Comment, Follow

translation.activate("en")

class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="auth")
        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовый пост",
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        self.assertEqual(self.post.text[:15], str(self.post))

    def test_models_verbose_names(self):
        verbose_names_dict = {
            "text": "Текст",
            "group": "Group",
            "image": "Изображение",
        }
        for label, verbose_name in verbose_names_dict.items():
            with self.subTest(label=label):
                response = Post._meta.get_field(label).verbose_name
                self.assertEqual(response, verbose_name)

    def test_help_texts_are_correct(self):
        help_texts_dict = {
            "text": "",
            "group": "",
        }
        for label, help_text in help_texts_dict.items():
            with self.subTest(label=label):
                response = Post._meta.get_field(label).help_text
                self.assertEqual(response, help_text)


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="Тестовый слаг",
            description="Тестовое описание",
        )

    def test_model_has_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        self.assertEqual(self.group.title, str(self.group))

    def test_models_verbose_names(self):
        verbose_names_dict = {
            "title": "Title",
            "slug": "Slug",
            "description": "Description",
        }
        for label, verbose_name in verbose_names_dict.items():
            with self.subTest(label=label):
                response = Group._meta.get_field(label).verbose_name
                self.assertEqual(response, verbose_name)

    def test_help_texts_are_correct(self):
        help_texts_dict = {
            "title": "",
            "slug": "",
            "description": "",
        }
        for label, help_text in help_texts_dict.items():
            with self.subTest(label=label):
                response = Group._meta.get_field(label).help_text
                self.assertEqual(response, help_text)


class CommentModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="auth")
        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовый пост",
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text="Тестовый коммент",
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        self.assertEqual(self.comment.text[:30], str(self.comment))

    def test_models_verbose_names(self):
        verbose_names_dict = {
            "post": "Post",
            "author": "Author",
            "text": "Текст",
        }
        for label, verbose_name in verbose_names_dict.items():
            with self.subTest(label=label):
                response = Comment._meta.get_field(label).verbose_name
                self.assertEqual(response, verbose_name)

    def test_help_texts_are_correct(self):
        help_texts_dict = {
            "post": "",
            "author": "",
            "text": "",
        }
        for label, help_text in help_texts_dict.items():
            with self.subTest(label=label):
                response = Comment._meta.get_field(label).help_text
                self.assertEqual(response, help_text)


class FollowModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.AUTHOR_USERNAME = "author"
        cls.SUBSCRIBER_USERNAME = "sub"

        cls.user_author = User.objects.create_user(username=cls.AUTHOR_USERNAME)
        cls.user_sub = User.objects.create_user(username=cls.SUBSCRIBER_USERNAME)

    def test_model_creation(self):
        Follow.objects.create(
            author=self.user_author,
            user=self.user_sub,
        )
        follow = Follow.objects.first()
        self.assertEqual(follow.author.username, self.AUTHOR_USERNAME)
        self.assertEqual(follow.user.username, self.SUBSCRIBER_USERNAME)
