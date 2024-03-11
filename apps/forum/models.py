# -*- coding: utf-8 -*-
from django.db import models
from django.conf import settings
from django.utils.translation import gettext as _;


class Post(models.Model):
    title = models.CharField(_('Título'), max_length=255, blank=False)
    content = models.TextField(_('Conteúdo'), blank=False)
    created_at = models.DateTimeField(
        _('Data da Publicação'), auto_now_add=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_("Autor"),
        related_name='post_list', on_delete=models.PROTECT)

    class Meta:
        verbose_name = _('Postagem')
        verbose_name_plural = _('Postagens')



class Comment(models.Model):
    content = models.TextField(_('Conteúdo'), blank=False)
    created_at = models.DateTimeField(
        _('Data da Criação'), auto_now_add=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_("Autor"),
        related_name="comments", on_delete=models.PROTECT)
    post = models.ForeignKey(
        Post, verbose_name=_("Post"), related_name="comments",
        on_delete=models.CASCADE)

    class Meta:
        verbose_name = _('Comentário')
        verbose_name_plural = _('Comentários')
