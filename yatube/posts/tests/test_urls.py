from datetime import datetime as dt
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from posts.models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            pub_date=dt.now(),
            group=cls.group,
            author=cls.user
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostURLTests.user)

    def test_pages_url_exists_at_desired_location(self):
        """Страницы находятся по указанным url-адресам"""
        pages_url_names = [
            '/',
            f'/group/{PostURLTests.group.slug}/',
            f'/profile/{PostURLTests.user}/',
            f'/posts/{PostURLTests.post.id}/']

        for address in pages_url_names:
            with self.subTest(adress=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url_exists_at_desired_location(self):
        """Страница /posts/<post_id>/edit/ доступна только автору."""
        response = self.authorized_client.get(
            f'/posts/{PostURLTests.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_create_url_exists_at_desired_location_authorized(self):
        """Страница /create доступна авторизованному
        пользователю."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexisting_page(self):
        """Проверка запроса к несуществующей странице"""
        response = self.authorized_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_post_create_url_redirect_anonymous_on_admin_login(self):
        """Страница по адресу /create/ перенаправит анонимного
        пользователя на страницу логина.
        """
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/create/'
        )

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{PostURLTests.group.slug}/': 'posts/group_list.html',
            f'/profile/{PostURLTests.user}/': 'posts/profile.html',
            f'/posts/{PostURLTests.post.id}/': 'posts/post_detail.html',
            f'/posts/{PostURLTests.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
            '/follow/': 'posts/follow.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(adress=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
