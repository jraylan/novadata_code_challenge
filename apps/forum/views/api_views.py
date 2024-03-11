# -*- coding: utf-8 -*-
from apps.forum.models import (
    Post,
    Comment
)

from apps.forum.serializers import (
    PostSerializer,
    CommentSerializer
)

from django.utils.translation import gettext as _

from rest_framework import mixins, generics
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response



class BaseModelAPIView(
        mixins.ListModelMixin,
        mixins.CreateModelMixin,
        mixins.RetrieveModelMixin,
        mixins.UpdateModelMixin,
        mixins.DestroyModelMixin,
        generics.GenericAPIView):
    """Classe que serve de base para as outras views. Esta classe implementa
    as features compartilhadas pelas outras views (listagem, criação
    e recuperação, alteração e remoção de objetos)."""
    model = None

    permission_classes = [IsAuthenticatedOrReadOnly]
    # Quando True, enviar o post na url com o id do objeto irá atualizar-lo
    # o método put precisa ser implementado
    atualizar_via_post = False
    lookup_url_kwarg = 'pk'

    def get_queryset(self):
        return self.model.objects.all()

    def get(self, request, pk=None, format=None):
        if pk:
            return self.retrieve(request, format=format)
        return self.list(request, format=format)

    def post(self, request, pk=None, format=None):
        if pk:
            # Permitir alteração criação via post?
            if self.atualizar_via_post and hasattr(self, 'put'):
                # Se permitido, tratar como um PUT
                return self.put(request, format=format)
            # Retornar 405 já que o POST na url sem o pk não é um método válido
            return self.http_method_not_allowed(request)

        return self.create(request, format=format)

    def put(self, request, pk=None, format=None):
        return self.update(request, pk=pk, format=format)

    def delete(self, request, pk=None, format=None):
        return self.destroy(request, pk=pk, format=format)


class PostAPIView(BaseModelAPIView, ):
    model = Post
    serializer_class = PostSerializer

    def perform_destroy(self, instance):
        if instance.author != self.request.user:
            self.permission_denied(
                self.request, _("Você só pode remover uma postagem criada por voce."))
        return super().perform_destroy(instance)

    def perform_update(self, serializer):
        if not serializer.instance or serializer.instance.author != self.request.user:
            self.permission_denied(
                self.request, _("Você só pode alterar uma postagem criada por voce."))
        return super().perform_update(serializer)
    
    def perform_create(self, serializer):
        if not self.request.user.is_authenticated:
            self.permission_denied(
                self.request, _("Você precisa está logado para criar uma postagem."))
        serializer.save(author=self.request.user)


class PostCommentsAPIView(mixins.ListModelMixin,
                          mixins.RetrieveModelMixin,
                          generics.GenericAPIView):
    model = Comment
    serializer_class = CommentSerializer


    def get_queryset(self):
        # Filtra somente os comentários de um post específico
        return Comment.objects.filter(post_id=self.kwargs['pk'])

    def get(self, request, pk=None, format=None):
        return self.list(request, format=format)


class CommentAPIView(BaseModelAPIView):
    model = Comment
    serializer_class = CommentSerializer

    def perform_update(self, serializer):
        if not serializer.instance or serializer.instance.author != self.request.user:
            self.permission_denied(
                self.request, _("Você só pode alterar uma comentário criada por voce."))
        return super().perform_update(serializer)

    def perform_destroy(self, instance):
        if instance.author != self.request.user:
            self.permission_denied(
                self.request, _("Você só pode remover um comentário criada por voce."))
        return super().perform_destroy(instance)

    def perform_create(self, serializer):
        if not self.request.user.is_authenticated:
            self.permission_denied(
                self.request, _("Você precisa está logado para comentar em uma postagem."))

        serializer.save(author=self.request.user)
