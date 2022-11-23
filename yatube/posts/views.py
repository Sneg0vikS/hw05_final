from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render, redirect

from .models import Group, Post, User, Comment, Follow
from . forms import PostForm, CommentForm


def index(request):
    """Главная страница"""
    posts = Post.objects.select_related('author').all()
    page_obj = paginator_page(request, posts)
    context = {'page_obj': page_obj}
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    """Страница сообщества для постов"""
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    page_obj = paginator_page(request, posts)
    context = {
        'group': group,
        'posts': posts,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    """Здесь код запроса к модели и создание словаря контекста"""
    author = get_object_or_404(User, username=username)
    following = request.user.is_authenticated and Follow.objects.filter(
        user=request.user,
        author=author
    ).exists()
    post_list = author.posts.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    """Здесь код запроса к модели и создание словаря контекста"""
    post = get_object_or_404(Post, pk=post_id)
    posts_author = post.author
    posts_counts = Post.objects.filter(author=posts_author).count()
    post_comment = Comment.objects.select_related('post').filter(post=post_id)
    form = CommentForm()
    context = {
        'post': post,
        'posts_counts': posts_counts,
        'form': form,
        'comments': post_comment,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    """Создание поста"""
    form = PostForm()
    if request.method == 'POST':
        form = PostForm(request.POST,
                        files=request.FILES or None)
        if form.is_valid():
            form = form.save(commit=False)
            form.author = request.user
            form.save()
            return redirect('posts:profile', form.author)
    return render(request, 'posts/post_create.html', {'form': form})


@login_required
def post_edit(request, post_id):
    """Редактирование поста"""
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    if request.method == 'POST':
        if form.is_valid():
            form = form.save()
            return redirect('posts:post_detail', post_id)
    context = {'form': form, 'is_edit': True, 'post': post}
    return render(request, 'posts/post_create.html', context)


@login_required
def add_comment(request, post_id):
    """Добавление комментария"""
    # Получите пост и сохраните его в переменную post.
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


def paginator_page(request, posts):
    """Пагинатор"""
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj


@login_required
def follow_index(request):
    """Отображение постов фоловера"""
    posts = Post.objects.filter(author__following__user=request.user)
    page_obj = paginator_page(request, posts)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    """Кнопка подписаться"""
    if request.user.username != username:
        author = get_object_or_404(User, username=username)
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect("posts:follow_index")


@login_required
def profile_unfollow(request, username):
    """Отписка"""
    author = get_object_or_404(User, username=username)
    follower = Follow.objects.filter(user=request.user, author=author)
    if follower.exists():
        follower.delete()
    return redirect("posts:follow_index")
