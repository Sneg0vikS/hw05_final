from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Q, F
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class Group(models.Model):
    """Класс для сообществ"""

    title = models.CharField(_("Title"), max_length=200)
    slug = models.SlugField(_("Slug"), unique=True)
    description = models.TextField(_("Description"))

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _("Group")
        verbose_name_plural = _("Groups")


class Post(models.Model):
    """Класс описывающий модель поста"""

    text = models.TextField(_("Текст"))
    pub_date = models.DateTimeField(_("Date of publication"),
                                    auto_now_add=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="posts",
        verbose_name=_("Author"),
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="posts",
        verbose_name=_("Group"),
    )
    image = models.ImageField(_("Изображение"), upload_to="posts/", blank=True)

    class Meta:
        """Указываем необходимую сортировку и название модели"""
        ordering = ("-pub_date",)
        verbose_name = _("Post")
        verbose_name_plural = _("Posts")

    def __str__(self):
        """Выводим текст поста"""
        return self.text[:15]

    def str_author(self) -> str:
        return self.author


class Comment(models.Model):
    """Класс описывающий модель комментария"""

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name=_("Post"),
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name=_("Author"),
    )
    text = models.TextField(_("Текст"))
    created = models.DateTimeField(_("Created"), auto_now_add=True)

    class Meta:
        ordering = ("-created",)
        verbose_name = _("Comment")
        verbose_name_plural = _("Comments")

    def __str__(self):
        return self.text[:30]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="follower",
        verbose_name=_("User"),
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="following",
        verbose_name=_("Author"),
    )

    class Meta:
        verbose_name = _("Following")
        verbose_name_plural = _("Followings")
        constraints = (
            models.UniqueConstraint(fields=("user", "author"),
                                    name="One follow for each"),
            models.CheckConstraint(
                check=~Q(author=F('user')),
                name='author_and_user_can_not_be_equal'
            )
        )
