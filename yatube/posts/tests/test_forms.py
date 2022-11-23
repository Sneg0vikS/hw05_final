from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Post, Group

User = get_user_model()

TEST_POST = 'Тестовый пост'
CHANGE_TEXT = 'Изменяем текст'
TEST_DESCRIPTION = 'Тестовое описание'


class FormsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description=TEST_DESCRIPTION)
        cls.post = Post.objects.create(
            author=cls.user,
            text=TEST_POST,
            group=cls.group,
            image=uploaded)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_task(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        form_data = {'text': TEST_POST}
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True)
        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': self.user.username}))
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count + 1)
        # Проверяем, что создалась запись с заданным слагом
        self.assertTrue(Post.objects.filter(text=TEST_POST).exists())
        self.assertEqual(response.status_code, 200)

    def test_change_post(self):
        """Валидная форма изменяет запись в Post."""
        self.post = Post.objects.create(text='Тестовый текст',
                                        author=self.user,
                                        group=self.group)

        self.group2 = Group.objects.create(title='Тестовая группа2',
                                           slug='test-group',
                                           description=TEST_DESCRIPTION)
        posts_count = Post.objects.count()
        form_data = {"text": CHANGE_TEXT, "group": self.group2.id}
        response = self.authorized_client.post(
            reverse("posts:post_edit", args=({self.post.id})),
            data=form_data,
            follow=True,)
        self.assertRedirects(
            response,
            reverse("posts:post_detail", kwargs={"post_id": self.post.id}))
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(Post.objects.select_related(self.post.text)
                                    .filter(text=CHANGE_TEXT,
                                            id=self.post.id).exists())
        self.assertEqual(response.status_code, 200)

    def test_post_with_picture(self):
        count_posts = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост',
            'group': self.group.id,
            'image': self.post.image
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        post = Post.objects.get(id=self.group.id)
        author = User.objects.get(username='auth')
        group = Group.objects.get(title='Тестовая группа')
        self.assertEqual(Post.objects.count(), count_posts + 1)
        self.assertRedirects(response, reverse('posts:profile',
                                               kwargs={"username":
                                                       post.author}))
        self.assertEqual(post.text, 'Тестовый пост')
        self.assertEqual(author.username, 'auth')
        self.assertEqual(group.title, 'Тестовая группа')
