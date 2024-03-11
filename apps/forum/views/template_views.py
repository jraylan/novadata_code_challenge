# -*- coding: utf-8 -*-
from django.conf import settings
from apps.forum.forms import PostCommentForm, PostForm
from apps.forum.models import Post, Comment

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _
from django.views import generic

from functools import partial
from typing import Any



class PostListView(generic.ListView):
    """View responsável por listar as postagens."""
    model = Post
    # Seguindo a especificação
    ordering = 'created_at'
    # Pagina as postagens de 10 em 10.
    paginate_by = 10

    @property
    def queryset(self):
        # Adiciona o prefetch/select related para otimizar
        # o desenpenho.
        return self.model.objects\
                    .select_related('author')\
                    .prefetch_related('comments__author')\
                    .annotate(
                        comments_qtd=Count('comments', distinct=True)
                    )

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        # Instância do paginator
        paginator = context.get('paginator')
        # Instância da página atual
        page = context.get('page_obj')

        if not paginator or not page:
            return context

        # Se houver paginação, adicionar ao contexto o objeto elided_page_range
        elided_page_range = partial(
            paginator.get_elided_page_range, number=page.number)    

        context["elided_page_range"] = elided_page_range

        return context


class PostCreationView(generic.CreateView):
    """View responsavel por Criar uma postagem."""
    model = Post
    form_class = PostForm
    object = None

    @property
    def success_url(self):
        # Url de redirecionamento
        if self.object:
            # Retorna para o detalhe das postagens
            return reverse('post_detail', kwargs={'pk': self.object.id})
        # retorna para a lista de postagens
        return reverse('post_list')

    def get_initial(self):
        return {
            'author': self.request.user
        }


class PostDetailView(
        generic.DetailView,
        generic.edit.BaseCreateView):
    """View responsavel por visualizar a postagem e adicionar comentários à ela."""

    model = Post
    form_class = PostCommentForm

    @property
    def success_url(self):
        # Url de redirecionamento
        if self.object:
            # Retorna para o detalhe das postagens
            return reverse('post_detail', kwargs={'pk': self.object.id})
        # retorna para a lista de postagens        
        return reverse('post_list')
    
    @property
    def queryset(self):
        # Adiciona o prefetch/select related para otimizar
        # o desenpenho.
        return self.model.objects\
                .select_related('author')\
                .prefetch_related('comments__author')\
                .all()
    
    def form_invalid(self, form):
        """Função chamada quando o post de um comentário falha"""
        self.object = self.get_object()
        context = self.get_context_data(object=self.object, comment_form=form)
        return self.render_to_response(context)

    def form_valid(self, form):
        """Função chamada ao realizar um post de um comentário com sucesso"""
        self.object = self.get_object()

        if not self.request.user.is_authenticated:
            messages.add_message(
                self.request, messages.ERROR,
                _("Você precisa estar logado para executar esta ação."))

            return HttpResponseRedirect(self.success_url)


        # Pega a instância gerada pelo form
        comment = form.save(commit=False)

        # Popula os campos author e post
        comment.author = self.request.user
        comment.post = self.object

        # Salva o objeto no banco de dados
        comment.save()

        hashtag = f"#comment-{comment.id}"

        # Fazer um redirect para evitar que os comentários sejam duplicados
        # ao realizar um refresh
        messages.add_message(
            self.request, messages.SUCCESS,
            _("Comentário adicionado com sucesso."))

        return HttpResponseRedirect(self.success_url+ hashtag)
    
    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return super().post(request, *args, **kwargs)
        return HttpResponseRedirect(settings.LOGIN_URL)


class PostDeletionView(generic.DeleteView):
    model = Post
    success_url = reverse_lazy('post_list')

    def get(self, request, *args, **kwargs):
        # Retornar para a página da postagem
        return HttpResponseRedirect(
            reverse('post_detail', args=args, kwargs=kwargs))

    def form_valid(self, form):
        # Verifica se o usuário é o autor da postagem
        if self.object and self.object.author != self.request.user:
            messages.add_message(
                self.request, messages.ERROR,
                _("Você não tem permissão para apagar esta postagem."))
            raise PermissionDenied()
            
        messages.add_message(
            self.request, messages.SUCCESS,
            _("Postagem apagada com sucesso."))
        return super().form_valid(form)


class CommentDeletionView(generic.DeleteView):
    model = Comment

    @property
    def success_url(self):
        if self.object:
            # Retornar para a página da postagem
            return reverse('post_detail', kwargs={'pk': self.object.post_id})
        # Retornar para a lista de postagens
        return reverse('post_list')

    def get(self, request, *args, **kwargs):
        # Em caso de POST, redirecionar para a página da postagem
        return HttpResponseRedirect(reverse(self.success_url))

    def form_valid(self, form):
        # Verifica se o usuário é o autor do comentário
        if self.object and self.object.author != self.request.user:
            messages.add_message(
                self.request, messages.ERROR,
                _("Você não tem permissão para executar esta ação."))
            raise PermissionDenied()

        messages.add_message(
            self.request, messages.SUCCESS,
            _("Comentário removido com sucesso."))
        return super().form_valid(form)

