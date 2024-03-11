# -*- coding: utf-8 -*-
from .base import fake
from apps.forum.models import Post, Comment
from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from django.utils.functional import cached_property


LOGIN_CREDENTIALS = {
    'username': 'admin',
    'password': 'admin'
}

TEST_USER_ID = 11

CREATE_POST_DATA = {
    'title': fake.paragraph(nb_sentences=1)[:255],
    'content': fake.paragraph(nb_sentences=fake.random.randint(7, 15)),
    'author_id': TEST_USER_ID
}

CREATE_COMMENT_POST_ID = 3

CREATE_COMMENT_DATA = {
    'content': fake.paragraph(nb_sentences=fake.random.randint(7, 15)),
}



class ModelViewTestCase(TestCase):
    fixtures = ["test_db_backup.json"]

    def assertNotTemplateUsed(self, response=None, msg_prefix=""):
        """
        Assert that no template was used in rendering the response.
        """
        context_mgr_template, template_names, msg_prefix = self._get_template_used(
            response,
            None,
            msg_prefix,
            "assertTemplateNotUsed",
        )

        self.assertFalse(
            bool(template_names),
            msg_prefix
            + "Templates '%s' was used unexpectedly in rendering the response"
            % (', '.join(template_names)),
        )

    @cached_property
    def session_cookie(self):
        """Forma mais prática de logar no sistema de forma a reduzir a necessidade de
        executar `self.client.login` e `self.cliente.logout`.
        """
        # Executa o login
        response = self.client.post(
            reverse('login'), follow=True, data=LOGIN_CREDENTIALS)
        
        # Verifica se o resultado é 200
        self.assertEqual(response.status_code, 200)

        # recupera a sessão
        session = response.context['request'].session
        # Monta o cookie da sessão
        session_cookie = f"{settings.SESSION_COOKIE_NAME}={session.session_key}"
        
        return {
            'HTTP_COOKIE': session_cookie
        }
    
    def test_login_public_urls(self):
        login_url = reverse(settings.LOGIN_URL_NAME)

        # Certifica-se que a url "post_list" exite
        response = self.client.get(reverse('post_list'))
        self.assertEqual(response.status_code, 200)        
        self.assertTemplateUsed(response, 'forum/post_list.html')

        # Certifica-se que a url "post_detail" exite
        response = self.client.get(
            reverse('post_detail', kwargs={'pk': 1}))
        self.assertEqual(response.status_code, 200)        
        self.assertTemplateUsed(response, 'forum/post_detail.html')

        # Certifica-se que a url "login" exite
        response = self.client.get(login_url)
        self.assertEqual(response.status_code, 200)        
        self.assertTemplateUsed(response, 'registration/login.html')

        # Certifica-se que a url "logout" exite
        response = self.client.get(reverse(settings.LOGOUT_URL_NAME))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, login_url)
        

    def test_login_protected_urls(self):
        login_url = reverse(settings.LOGIN_URL_NAME)
        # Testa se a requisição está redirecionando para
        # a tela de login
        response = self.client.get(
            reverse('post_create'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, login_url)
        self.assertNotTemplateUsed(response)

        # Testa se a requisição está redirecionando para
        # a tela de login
        response = self.client.post(
            reverse('post_create'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, login_url)
        self.assertNotTemplateUsed(response)

        # Testa se a requisição está redirecionando para
        # a tela de login
        response = self.client.post(
            reverse('post_delete', kwargs={'pk': 1}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, login_url)
        self.assertNotTemplateUsed(response)

        # Testa se a requisição está redirecionando para
        # a tela de login
        response = self.client.post(
            reverse('post_comment_delete', kwargs={'pk': 1}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, login_url)
        self.assertNotTemplateUsed(response)

        # Testa se a requisição está redirecionando para
        # a tela de login
        response = self.client.post(
            reverse('post_detail', kwargs={'pk': 1}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse(settings.LOGIN_URL_NAME))
        self.assertNotTemplateUsed(response)

    def test_manipulate_not_owned_objects(self):
        # Certifica-se que o usuário não pode remover uma postagem
        # que não é sua.
        response = self.client.post(
            reverse('post_delete', kwargs={'pk': 1}),
            **self.session_cookie)
        self.assertEqual(response.status_code, 403)
        self.assertNotTemplateUsed(response)

        # Certifica-se que o usuário não pode remover um comentário
        # que não é seu.
        response = self.client.post(
            reverse('post_comment_delete', kwargs={'pk': 1}),
            **self.session_cookie)
        self.assertEqual(response.status_code, 403)
        self.assertNotTemplateUsed(response)

    
    def test_view_performance(self):
        # Devido às subqueries feitas, a contagem de queries
        # é 4.
        with self.assertNumQueries(4):
            self.client.get(reverse('post_list'))

        # Devido às subqueries feitas, a contagem de queries
        # é 3.
        with self.assertNumQueries(3):
            self.client.get(
                reverse('post_detail', kwargs={'pk': 2}))

    def test_view_create_post(self):
        response = self.client.post(
            reverse('post_create'),
            data=CREATE_POST_DATA,
            **self.session_cookie)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'forum/post_form.html')

    def test_view_create_comment(self):
        create_comment_url = reverse('post_detail', kwargs={
                                     'pk': CREATE_COMMENT_POST_ID})
        response = self.client.post(
            create_comment_url,
            data=CREATE_COMMENT_DATA,
            **self.session_cookie)
        # Ao criar um comentário, a view redireciona para o post_detail para
        # evitar duplicação de comentário ao apertar F5.
        self.assertEqual(response.status_code, 302)

        # Durante o redirect, a hash #comment-{{comment.id}} é adicionado à
        # url para que a página role para o comentário criado. Por isto, se
        # faz necessário remover esta hash antes do teste.
        response_url = response.url.split('#')[0]
        self.assertEqual(response_url, create_comment_url)
        # Certifica-se de que nenhum template foi usado
        self.assertNotTemplateUsed(response)

    def test_view_delete_post(self):
        post = Post.objects.create(
            title=fake.paragraph(nb_sentences=1)[:255],
            content=fake.paragraph(nb_sentences=2),
            author_id=TEST_USER_ID)
        
        response = self.client.post(
            reverse('post_delete', kwargs={'pk': post.id}),
            **self.session_cookie)
        # Ao apagar uma postagem, a view redireciona para o post_list
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('post_list'))
        # Certifica-se de que nenhum template foi usado
        self.assertNotTemplateUsed(response)

    def test_view_delete_comment(self):
        post_id = 10

        comment = Comment.objects.create(
            content=fake.paragraph(nb_sentences=2),
            author_id=TEST_USER_ID,
            post_id=post_id)

        response = self.client.post(
            reverse('post_comment_delete', kwargs={'pk': comment.id}),
            **self.session_cookie)
        # Ao apagar um comentário, a view redireciona para o post_detail
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, reverse('post_detail', kwargs={'pk': post_id}))
        # Certifica-se de que nenhum template foi usado
        self.assertNotTemplateUsed(response)
