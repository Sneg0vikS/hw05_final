from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render, redirect

from .forms import PostForm, CommentForm
from .models import Group, Post, User, Follow
from .settings import POSTS_PER_PAGE


def paginator_page(request, posts):
    """Пагинатор"""
    paginator = Paginator(posts, POSTS_PER_PAGE)
    page_number = request.GET.get("page")
    return paginator.get_page(page_number)


def index(request):
    """Главная страница"""
    posts = Post.objects.select_related("author").all()
    page_obj = paginator_page(request, posts)
    context = {"page_obj": page_obj}
    return render(request, "posts/index.html", context)


def group_posts(request, slug):
    """Страница сообщества для постов"""
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    page_obj = paginator_page(request, posts)
    context = {
        "group": group,
        "page_obj": page_obj,
    }
    return render(request, "posts/group_list.html", context)


def profile(request, username):
    """Здесь код запроса к модели и создание словаря контекста"""
    author = get_object_or_404(User, username=username)
    following = (
        request.user.is_authenticated
        and request.user.follower.filter(author=author).exists()
    )
    post_list = author.posts.all()
    page_obj = paginator_page(request, post_list)
    context = {
        "author": author,
        "page_obj": page_obj,
        "following": following,
    }
    return render(request, "posts/profile.html", context)


def post_detail(request, post_id):
    """Здесь код запроса к модели и создание словаря контекста"""
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm()
    context = {
        "post": post,
        "form": form,
    }
    return render(request, "posts/post_detail.html", context)


@login_required
def post_create(request):
    """Создание поста"""
    form = PostForm(request.POST or None, files=request.FILES or None)
    if not form.is_valid():
        return render(request, "posts/post_create.html", {"form": form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect("posts:profile", post.author)


@login_required
def post_edit(request, post_id):
    """Редактирование поста"""
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect("posts:post_detail", post_id)
    form = PostForm(request.POST or None, files=request.FILES or None,
                    instance=post)
    if form.is_valid():
        form.save()
        return redirect("posts:post_detail", post_id)
    context = {"form": form, "post": post}
    return render(request, "posts/post_create.html", context)


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
    return redirect("posts:post_detail", post_id=post_id)


@login_required
def follow_index(request):
    """Отображение постов фоловера"""
    title = "123"
    posts = Post.objects.filter(author__following__user=request.user)
    page_obj = paginator_page(request, posts)
    context = {
        "page_obj": page_obj,
        "title": title,
    }
    return render(request, "posts/follow.html", context)


@login_required
def profile_follow(request, username):
    """Кнопка подписаться"""
    if request.user.username != username:
        author = get_object_or_404(User, username=username)
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect("posts:profile", username=username)


@login_required
def profile_unfollow(request, username):
    """Отписка"""
    get_object_or_404(Follow, user=request.user,
                      author__username=username).delete()
    return redirect("posts:profile", username=username)
