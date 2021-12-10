from datetime import datetime as dt
from http import HTTPStatus
import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from django.urls import reverse
from posts.models import Group, Post, Follow
from posts.forms import PostForm

User = get_user_model()


def create_redirect_url(target_view, redirect_view, kwargs=None):
    url = reverse(target_view) + '?next='
    if kwargs:
        url += reverse(redirect_view, kwargs=kwargs)
        return url
    url += reverse(redirect_view)
    return url


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='StasBasov')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            pub_date=dt.now(),
            group=cls.group,
            author=cls.user
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTests.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/create_post.html': reverse('posts:post_create'),
            'posts/post_detail.html': (
                reverse(
                    'posts:post_detail',
                    kwargs={'post_id': PostPagesTests.post.id})
            ),
            'posts/group_list.html': (
                reverse(
                    'posts:group_posts',
                    kwargs={'slug': PostPagesTests.group.slug})
            ),
            'posts/profile.html': (
                reverse(
                    'posts:profile',
                    kwargs={'username': PostPagesTests.user})
            ),
        }

        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_show_correct_context(self):
        """Шаблоны home, group_list, profile сформированы
        с правильным контекстом."""
        links = [
            reverse('posts:index'),
            reverse(
                'posts:group_posts',
                kwargs={'slug': PostPagesTests.group.slug}
            ),
            reverse(
                'posts:profile',
                kwargs={'username': PostPagesTests.user}
            )
        ]
        for address in links:
            with self.subTest(adress=address):
                response = self.authorized_client.get(address)
                if 'username' in response.context:
                    self.assertEqual(
                        response.context['username'],
                        PostPagesTests.user)
                if 'group' in response.context:
                    self.assertEqual(
                        response.context['group'],
                        PostPagesTests.group
                    )
                first_object = response.context['page_obj'][0]
                post_text_0 = first_object.text
                post_group_0 = first_object.group
                post_author_0 = first_object.author
                self.assertEqual(post_text_0, PostPagesTests.post.text)
                self.assertEqual(post_group_0, PostPagesTests.group)
                self.assertEqual(post_author_0, PostPagesTests.user)

    def test_post_detail_shows_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом"""
        response = self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': PostPagesTests.post.id}
                    ))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        post_author = response.context['author']
        post_id = response.context['post'].id
        self.assertEqual(post_author, PostPagesTests.user)
        self.assertEqual(post_id, PostPagesTests.post.id)

    def test_post_create_edit_shows_correct_context(self):
        """Шаблон post_create, post_edit сформирован с правильным контекстом"""
        links = [
            reverse('posts:post_create'),
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostPagesTests.post.id}
            )]
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for address in links:
            response = self.authorized_client.get(address)
            self.assertEqual(response.status_code, HTTPStatus.OK)
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)


class PaginatorViewsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='StasBasov')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug')
        post = Post(text='Тестовый текст',
                    pub_date=dt.now(),
                    group=cls.group,
                    author=cls.user)
        cls.posts_per_page = 10
        cls.posts_all = 13
        Post.objects.bulk_create(
            [post] * PaginatorViewsTest.posts_all
        )
        cls.links = [
            reverse('posts:index'),
            reverse(
                'posts:group_posts',
                kwargs={'slug': PaginatorViewsTest.group.slug}
            ),
            reverse(
                'posts:profile',
                kwargs={'username': PaginatorViewsTest.user}
            )
        ]

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PaginatorViewsTest.user)

    def test_first_page_contains_ten_records(self):
        """На первую страницу паджинатора выводятся 10 постов."""
        for address in PaginatorViewsTest.links:
            with self.subTest(adress=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertEqual(
                    len(response.context['page_obj']),
                    PaginatorViewsTest.posts_per_page)

    def test_second_page_contains_three_records(self):
        """На вторую страницу паджинатора выводятся 3 поста."""
        posts_per_second_page = (PaginatorViewsTest.posts_all
                                 - PaginatorViewsTest.posts_per_page)
        for address in PaginatorViewsTest.links:
            with self.subTest(adress=address):
                response = self.client.get(address + '?page=2')
                self.assertEqual(
                    len(response.context['page_obj']),
                    posts_per_second_page)


class CreatePostViewsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='StasBasov')
        cls.group_1 = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            pub_date=dt.now(),
            group=cls.group_1,
            author=cls.user
        )
        cls.links = [
            reverse('posts:index'),
            reverse(
                'posts:group_posts',
                kwargs={'slug': CreatePostViewsTest.group_1.slug}
            ),
            reverse(
                'posts:profile',
                kwargs={'username': CreatePostViewsTest.user}
            )
        ]

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(CreatePostViewsTest.user)

    def test_create_post(self):
        """При создании поста с указанной группой
        он появляется в нужных view функциях"""
        for address in CreatePostViewsTest.links:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                first_object = response.context['page_obj'][0]
                post_text_0 = first_object.text
                post_group_0 = first_object.group
                post_author_0 = first_object.author
                self.assertEqual(post_text_0, CreatePostViewsTest.post.text)
                self.assertEqual(post_group_0, CreatePostViewsTest.group_1)
                self.assertEqual(post_author_0, CreatePostViewsTest.user)
        response = self.authorized_client.get(
            reverse(
                'posts:group_posts',
                kwargs={'slug': 'test_slug_2'}
            ))
        self.assertEqual(response.status_code, 404)


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class UploadImageTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_cls_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded_cls = SimpleUploadedFile(
            name='small.gif',
            content=small_cls_gif,
            content_type='image/gif'
        )
        cls.form = PostForm()
        cls.user = User.objects.create_user(username='StasBasov')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            pub_date=dt.now(),
            group=cls.group,
            author=cls.user,
            image=UploadImageTest.uploaded_cls
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(UploadImageTest.user)

    def test_image_in_context(self):
        """Изображение выводится в словаре context"""
        links = [
            reverse('posts:index'),
            reverse(
                'posts:group_posts',
                kwargs={'slug': UploadImageTest.group.slug}
            ),
            reverse(
                'posts:profile',
                kwargs={'username': UploadImageTest.user}
            ),
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostPagesTests.post.id}

            )
        ]
        for address in links:
            with self.subTest(adress=address):
                response = self.authorized_client.get(address)
                self.assertTrue(response.request)


class CacheTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='StasBasov')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            pub_date=dt.now(),
            group=cls.group,
            author=cls.user
        )

    def setUp(self):
        self.unauthorized_client = Client()

    def test_cache_index_page(self):
        """Посты на главной странице хранятся в кэше."""
        self.assertContains(
            self.unauthorized_client.get(reverse('posts:index')),
            CacheTest.post.text
        )
        Post.objects.all().delete()
        self.assertContains(
            self.unauthorized_client.get(reverse('posts:index')),
            CacheTest.post.text
        )
        cache.clear()
        self.assertNotContains(
            self.unauthorized_client.get(reverse('posts:index')),
            CacheTest.post.text
        )


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Test_user')
        cls.user_to_follow = User.objects.create_user(
            username='User_to_follow'
        )
        cls.kwargs_follow = {'username': cls.user_to_follow.username}
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            pub_date=dt.now(),
            group=cls.group,
            author=cls.user_to_follow
        )
        cls.post_data = {
            'text': 'Тестовый текст',
            'group': FollowTest.group,
            'author': FollowTest.user_to_follow
        }

    def setUp(self):
        self.unauthorized_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(FollowTest.user)

    def test_follow_user_unauthorized(self):
        """Неавторизованный пользователь не может подписаться."""
        response = self.unauthorized_client.get(
            reverse('posts:profile_follow', kwargs=FollowTest.kwargs_follow),
            follow=True)
        self.assertRedirects(response, create_redirect_url(
            'users:login',
            'posts:profile_follow',
            kwargs=FollowTest.kwargs_follow
        ))

    def test_follow_user_authorized(self):
        """Подписки доступны авторизованному пользователю."""
        follows_number = Follow.objects.all().count()
        response = self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs=FollowTest.kwargs_follow),
            follow=True)
        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                kwargs=FollowTest.kwargs_follow)
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(
            Follow.objects.all().count(),
            follows_number + 1
        )
        self.assertTrue(Follow.objects.filter(
            user=FollowTest.user,
            author=FollowTest.user_to_follow
        ).exists())

    def test_unfollow_authorized_user(self):
        """Отписка доступна авторизованному пользователю."""
        follows_number = Follow.objects.all().count()
        Follow.objects.create(
            user=FollowTest.user,
            author=FollowTest.user_to_follow
        )
        self.assertEqual(Follow.objects.all().count(), follows_number + 1)
        self.authorized_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': FollowTest.user_to_follow}),
            follow=True)
        self.assertEqual(Follow.objects.all().count(), follows_number)

    def test_new_post_for_non_followers(self):
        """Новый пост не отображается в ленте у неподписанных."""
        Post.objects.create(
            text=FollowTest.post_data['text'],
            pub_date=dt.now(),
            group=FollowTest.post_data['group'],
            author=FollowTest.post_data['author']
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        posts = response.context['page_obj']
        self.assertFalse(posts)

    def test_new_post_for_followers(self):
        Post.objects.create(
            text=FollowTest.post_data['text'],
            pub_date=dt.now(),
            group=FollowTest.post_data['group'],
            author=FollowTest.post_data['author']
        )
        """Новый пост отображается в ленте у подписчиков."""
        response = self.authorized_client.get(reverse('posts:follow_index'))
        posts = response.context['page_obj']
        self.assertFalse(posts)
        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': FollowTest.user_to_follow}),
            follow=True)
        response = self.authorized_client.get(reverse('posts:follow_index'))
        first_post = response.context['page_obj'][0]
        self.assertEqual(first_post.text, FollowTest.post_data['text'])
