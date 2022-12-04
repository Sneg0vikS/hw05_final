from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile

from ..forms import CommentForm, PostForm
from ..models import Post, Group, User, Comment


COMMENT_TEXT = "Тестовый комментарий"
POST_TEXT = "Тестовый пост"
NONAUTH = " - не авторизован"
EDITED = " - редактированный"
TEST_DESCRIPTION = "Тестовое описание"
USERNAME = "auth"

INDEX_PAGE = "/index/"
PROFILE_URL = reverse("posts:profile", args=(USERNAME,))
POST_CREATE_URL = reverse("posts:post_create")

SMALL_GIF = (
    b"\x47\x49\x46\x38\x39\x61\x02\x00"
    b"\x01\x00\x80\x00\x00\x00\x00\x00"
    b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
    b"\x00\x00\x00\x2C\x00\x00\x00\x00"
    b"\x02\x00\x01\x00\x00\x02\x02\x0C"
    b"\x0A\x00\x3B"
)


class FormsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.uploaded = SimpleUploadedFile(
            name="small.gif", content=SMALL_GIF, content_type="image/gif"
        )
        cls.user = User.objects.create_user(username=USERNAME)
        cls.user2 = User.objects.create_user(username="user2")
        cls.group = Group.objects.create(
            title="Тестовая группа", slug="test-slug", description=TEST_DESCRIPTION
        )
        cls.group2 = Group.objects.create(
            title="Тестовая группа №2",
            slug="test-slug-two",
            description=TEST_DESCRIPTION,
        )
        cls.post = Post.objects.create(
            author=cls.user, text=POST_TEXT, group=cls.group, image=cls.uploaded
        )

        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.authorized_client2 = Client()
        cls.authorized_client2.force_login(cls.user2)

        cls.POST_DETAIL_URL = reverse(
            "posts:post_detail", kwargs={"post_id": cls.post.pk}
        )
        cls.POST_EDIT_URL = reverse("posts:post_edit", kwargs={"post_id": cls.post.pk})

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        time_before_test = timezone.now()

        form_data = {
            "text": POST_TEXT,
            "group": self.group.pk,
            "image": self.uploaded.open(),
        }
        response = self.authorized_client.post(
            POST_CREATE_URL, data=form_data, follow=True
        )

        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response,
            PROFILE_URL,
        )
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count + 1)
        # Проверяем, что создалась одна запись с заданными пааметрами
        new_posts = Post.objects.filter(
            text=form_data["text"],
            group__pk=form_data["group"],
            author=self.user,
            pub_date__gt=time_before_test,
        )
        self.assertTrue(new_posts.exists())
        self.assertEqual(new_posts.count(), 1)

        # проверяем картинку
        self.assertEqual(
            new_posts.first().image.open().read(), form_data["image"].open().read()
        )

        self.assertEqual(response.status_code, 200)

    def test_create_post_no_valid_form(self):
        """Не валидная форма не создает запись в Post."""
        form_data = {
            "text": "",
        }
        self.authorized_client.post(POST_CREATE_URL, data=form_data, follow=True)
        self.assertFalse(Post.objects.filter(text=form_data["text"]).exists())

    def test_post_edit(self):
        """Автор поста редактирует запись в Post."""
        form_data = {
            "text": POST_TEXT + EDITED,
            "group": self.group.pk,
            "image": self.uploaded.open(),
        }
        response = self.authorized_client.post(
            self.POST_EDIT_URL,
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, self.POST_DETAIL_URL)
        self.assertTrue(
            Post.objects.filter(
                text=form_data["text"],
            ).exists()
        )
        self.assertEqual(Post.objects.get(pk=self.post.pk).text, form_data["text"])

    def test_post_edit_other_user(self):
        """Другой пользователь не может редактировать запись в Post."""
        form_data = {
            "text": POST_TEXT + EDITED,
            "group": self.group.pk,
            "image": self.uploaded.open(),
        }
        response = self.authorized_client2.post(
            self.POST_EDIT_URL,
            data=form_data,
            follow=True,
        )
        self.assertFalse(
            Post.objects.filter(
                text=form_data["text"],
            ).exists()
        )

    def test_post_edit_group(self):
        """Автор поста редактирует группу поста в Post."""
        form_data = {"text": self.post.text, "group": self.group2.id}
        response = self.authorized_client.post(
            self.POST_EDIT_URL,
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, self.POST_DETAIL_URL)
        self.assertTrue(
            Post.objects.filter(
                text=form_data["text"], group=form_data["group"]
            ).exists()
        )

    def test_create_post_no_authorized_client(self):
        """Не авторизованный клиент не создает пост."""
        form_data = {
            "text": POST_TEXT + NONAUTH,
            "group": self.group.pk,
            "image": self.uploaded.open(),
        }
        self.client.post(
            POST_CREATE_URL,
            data=form_data,
            follow=True,
        )
        self.assertFalse(
            Post.objects.filter(
                text=form_data["text"],
            ).exists()
        )

    def test_post_create_page_show_correct_context(self):
        """Правильная форма создания в контексте."""
        response = self.authorized_client.get(POST_CREATE_URL)
        self.assertIsInstance(response.context.get('form'), PostForm)

    def test_post_edit_page_show_correct_context(self):
        """Правильная форма редактирования в контексте."""
        response = self.authorized_client.get(self.POST_EDIT_URL)
        self.assertIsInstance(response.context.get('form'), PostForm)
        self.assertEqual(response.context.get('form').instance, self.post)


class CommentCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.form = CommentForm()
        cls.user = User.objects.create_user(username="Thank_you")
        cls.post = Post.objects.create(text="Тестовый пост", author=cls.user)
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        cls.COMMENT_ADD_URL = reverse(
            "posts:add_comment", kwargs={"post_id": cls.post.pk}
        )
        cls.POST_DETAIL_URL = reverse(
            "posts:post_detail", kwargs={"post_id": cls.post.pk}
        )

    def test_create_comment_no_valid_form(self):
        """Не валидная форма не создает коментарий."""
        form_data = {
            "text": "",
        }
        self.authorized_client.post(
            self.COMMENT_ADD_URL,
            data=form_data,
            follow=True,
        )
        self.assertFalse(Comment.objects.exists())

    def test_create_comment_no_authorized_client(self):
        """Не авторизованный клиент не создает коментарий."""
        form_data = {
            "text": COMMENT_TEXT,
        }
        self.client.post(
            self.COMMENT_ADD_URL,
            data=form_data,
            follow=True,
        )
        self.assertFalse(Comment.objects.exists())

    def test_create_comment(self):
        """Валидная форма создает комментарий."""
        form_data = {
            "text": COMMENT_TEXT,
        }
        response = self.authorized_client.post(
            self.COMMENT_ADD_URL,
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, self.POST_DETAIL_URL)
        self.assertTrue(
            Comment.objects.filter(post=self.post, text=form_data["text"]).exists()
        )
