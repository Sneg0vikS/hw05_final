from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    """"Форма модели, добавляем через нее новую запись"""

    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': "Текст поста",
            'group': "Группа"}


class CommentForm(forms.ModelForm):
    """Форма модели комментария"""

    class Meta:
        model = Comment
        fields = ('text',)
        labels = {
            'text': 'Добавить комментарий'}
        help_texts = {'text': 'Текст комментария'}
