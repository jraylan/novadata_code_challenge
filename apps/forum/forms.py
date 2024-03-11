# -*- coding: utf-8 -*-
from django import forms
from django.forms import widgets

from apps.forum.models import Post, Comment


class PostCommentForm(forms.ModelForm):
    
    class Meta:
        model = Comment
        fields = ('content',)


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = (
            'title',
            'content',
            'author'
        )

        

        widgets = {
            'title': widgets.TextInput(
                attrs={'class': "form-control"}),
            'content': widgets.Textarea(
                attrs={'class': "form-control"}),
            'author': widgets.Select(
                attrs={'class': "form-control"})
        }
