from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render


from .forms import PostForm, CommentForm
from .models import Group, Post, User, Follow


def pagination(request, posts):
    paginator = Paginator(posts, settings.POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def index(request):
    posts = Post.objects.all()
    context = {
        'page_obj': pagination(request, posts),
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    context = {
        'group': group,
        'page_obj': pagination(request, posts),
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    user_obj = get_object_or_404(User, username=username)
    posts = user_obj.posts.all()
    posts_number = posts.count()
    if (request.user.is_authenticated and
            Follow.objects.filter(user=request.user, author=user_obj).exists()):
        following = True
    else:
        following = False
    context = {
        'username': user_obj,
        'posts_number': posts_number,
        'page_obj': pagination(request, posts),
        'following': following
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    comments = post.comments.all()
    author = post.author
    posts_number = author.posts.all().count()
    form = CommentForm()
    context = {
        'author': author,
        'post': post,
        'posts_number': posts_number,
        'form': form,
        'comments': comments
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None,
                    files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        form.save()
        return redirect('posts:profile', post.author.username)
    form = PostForm()
    return render(
        request,
        'posts/create_post.html',
        {
            'form': form,
            'is_edit': False})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(request.POST, instance=post)
    return render(
        request,
        'posts/create_post.html',
        {'form': form,
         'is_edit': True})


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    user = get_object_or_404(User, username=request.user.username)
    posts = Post.objects.filter(author__following__user=user).all()
    context = {
        'page_obj': pagination(request, posts)
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    user = get_object_or_404(User, username=request.user.username)
    user_to_follow = get_object_or_404(User, username=username)
    if user != user_to_follow:
        Follow.objects.create(user=user, author=user_to_follow)
    return redirect('posts:profile', username=user_to_follow)


@login_required
def profile_unfollow(request, username):
    # Дизлайк, отписка
    user = get_object_or_404(User, username=request.user.username)
    user_to_follow = get_object_or_404(User, username=username)
    if user != user_to_follow:
        Follow.objects.filter(user=user, author=user_to_follow).delete()
    return redirect('posts:profile', username=user_to_follow)
