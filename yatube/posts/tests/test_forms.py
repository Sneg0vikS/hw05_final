from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from posts.forms import CommentForm
from posts.models import Post, Group, User, Comment


User = get_user_model()


TEST_POST = 'Тестовый пост'
CHANGE_TEXT = 'Изменяем текст'
TEST_DESCRIPTION = 'Тестовое описание'
INDEX_PAGE = '/index/'

SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


class FormsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
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

    def test_create_post_no_valid_form(self):
        """Не валидная форма не создает запись в Post."""
        post_count = Post.objects.count()
        form_data = {
            'text': '',
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), post_count)

    def test_post_edit(self):
        """Автор поста редактуриет запись в Post."""
        form_data = {
            'text': 'Тестовый пост  - редактированный',
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
            ).exists()
        )

    def test_post_edit_group(self):
        """Автор поста редактуриет группу поста в Post."""
        form_data = {
            'text': self.post.text,
            'group': self.group.id
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                group=form_data['group']
            ).exists()
        )


class CommentCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.form = CommentForm()
        cls.user = User.objects.create_user(username='Thank_you')
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user
        )
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    def test_create_comment_no_valid_form(self):
        """Не валидная форма не создает коментарий."""
        first_post = Post.objects.first()
        comment_count = first_post.comments.count()
        form_data = {
            'text': '',
        }
        self.authorized_client.post(
            reverse(
                'posts:add_comment', kwargs={'post_id': first_post.pk}
            ),
            data=form_data,
            follow=True
        )
        self.assertEqual(first_post.comments.count(), comment_count)

    def test_create_comment_no_authorized_client(self):
        """Не авторизованный клиент не создает коментарий."""
        first_post = Post.objects.first()
        comment_count = first_post.comments.count()
        form_data = {
            'text': 'Тестовый текст',
        }
        self.guest_client.post(
            reverse(
                'posts:add_comment', kwargs={'post_id': first_post.pk}
            ),
            data=form_data,
            follow=True
        )
        self.assertEqual(first_post.comments.count(), comment_count)

    def test_create_comment(self):
        """Валидная форма создает комментарий."""
        first_post = Post.objects.first()
        comment_count = first_post.comments.count()
        form_data = {
            'text': 'Тестовый комментарий',
        }
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment', kwargs={'post_id': first_post.pk}
            ),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': first_post.pk})
        )
        self.assertEqual(first_post.comments.count(), comment_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                post=first_post,
                text=form_data['text']
            ).exists()
        )
