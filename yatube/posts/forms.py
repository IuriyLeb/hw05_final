from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': 'Введите текст поста',
            'group': 'Выберите группу'
        }

        help_texts = {
            'text': 'Напишите, о чем вы хотите сообщить сообществу',
            'group': 'выберите группу, или оставьте ваш пост без нее',
            'image': 'Добавьте картинку к публикации'
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {
            'text': 'Введите текст комментария'}
        help_texts = {
            'text': 'Напишите, о чем вы хотите сообщить автору поста'}
