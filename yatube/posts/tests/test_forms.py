from django.test import Client, TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from ..forms import CommentForm
from ..models import Post, Group, User, Comment

COMMENT_TEXT = "Тестовый комментарий"
POST_TEXT = "Тестовый пост"
NONAUTH = " - не авторизован"
EDITED = " - редактированный"
TEST_DESCRIPTION = "Тестовое описание"
USERNAME = "auth"

INDEX_PAGE_URL = reverse("posts:index")
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
SMALL_GIF2 = (
    b"\x00\x00\x00\x2C\x00\x00\x00\x00"
    b"\x02\x00\x01\x00\x00\x02\x02\x0C"
    b"\x01\x00\x80\x00\x00\x00\x00\x00"
    b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
    b"\x00\x00\x00\x2C\x00\x00\x00\x00"
    b"\x0A\x00\x3B\x00\x00\x02"
)


class FormsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.uploaded = SimpleUploadedFile(
            name="small.gif", content=SMALL_GIF, content_type="image/gif"
        )
        cls.uploaded2 = SimpleUploadedFile(
            name="small2.gif", content=SMALL_GIF2, content_type="image/gif"
        )
        cls.user = User.objects.create_user(username=USERNAME)
        cls.user2 = User.objects.create_user(username="user2")
        cls.group = Group.objects.create(
            title="Тестовая группа", slug="test-slug",
            description=TEST_DESCRIPTION
        )
        cls.group2 = Group.objects.create(
            title="Тестовая группа №2",
            slug="test-slug-two",
            description=TEST_DESCRIPTION,
        )
        cls.post = Post.objects.create(
            author=cls.user, text=POST_TEXT, group=cls.group,
            image=cls.uploaded
        )

        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.authorized_client2 = Client()
        cls.authorized_client2.force_login(cls.user2)

        cls.POST_DETAIL_URL = reverse(
            "posts:post_detail", kwargs={"post_id": cls.post.pk}
        )
        cls.POST_EDIT_URL = reverse("posts:post_edit",
                                    kwargs={"post_id": cls.post.pk})

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        Post.objects.all().delete()

        form_data = {
            "text": POST_TEXT + " new",
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
        # Проверяем, что в таблице только один пост
        self.assertEqual(Post.objects.count(), 1)

        # Проверяем, что создалась запись с заданными параметрами
        post = Post.objects.first()

        self.assertEqual(post.text, form_data["text"])
        self.assertEqual(post.group.pk, form_data["group"])
        self.assertEqual(post.author, self.user)
        self.assertEqual(
            post.image.open().read(), form_data["image"].open().read()
        )
        self.assertEqual(response.status_code, 200)

    def test_post_edit(self):
        """Автор поста редактирует запись в Post."""
        form_data = {
            "text": POST_TEXT + EDITED,
            "group": self.group2.pk,
            "image": self.uploaded.open(),
        }
        response = self.authorized_client.post(
            self.POST_EDIT_URL,
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, self.POST_DETAIL_URL)
        post = Post.objects.get(pk=self.post.pk)
        self.assertEqual(post.text, form_data["text"])
        self.assertEqual(post.group.pk, form_data["group"])
        self.assertEqual(post.author, self.user)
        self.assertEqual(
            post.image.open().read(), form_data["image"].open().read()
        )

    def test_post_edit_other_user(self):
        """Другой пользователь не может редактировать запись в Post."""
        form_data = {
            "text": POST_TEXT + EDITED,
            "group": self.group2.pk,
            "image": self.uploaded2.open(),
        }
        clients = (self.authorized_client2, self.client)
        for client in clients:
            with self.subTest(cient=client):
                client.post(
                    self.POST_EDIT_URL,
                    data=form_data,
                    follow=True,
                )
                post = Post.objects.get(pk=self.post.pk)
                self.assertEqual(post.text, self.post.text)
                self.assertEqual(post.group.pk, self.post.group.pk)
                self.assertEqual(post.author, self.post.author)
                self.assertEqual(
                    post.image.open().read(), self.post.image.open().read()
                )

        response = self.authorized_client2.post(
            self.POST_EDIT_URL,
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, self.POST_DETAIL_URL)


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

    def test_create_comment_no_authorized_client(self):
        """Неавторизованный клиент не создает комментарий."""
        Comment.objects.all().delete()
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
        Comment.objects.all().delete()
        form_data = {
            "text": COMMENT_TEXT,
        }
        response = self.authorized_client.post(
            self.COMMENT_ADD_URL,
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, self.POST_DETAIL_URL)

        self.assertEqual(Comment.objects.count(), 1)

        comment = Comment.objects.first()
        self.assertEqual(comment.text, form_data["text"])
        self.assertEqual(comment.author, self.user)
        self.assertEqual(comment.post, self.post)
