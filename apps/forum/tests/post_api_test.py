# -*- coding: utf-8 -*-
from .base import *
from apps.forum.serializers import PostSerializer
from django.contrib.auth.models import User
from django.utils.functional import cached_property


READ_POST_PK = 1
UPDATE_POST_PK = 2
DELETE_POST_PK = 3
NO_DELETE_POST_PK = 4


CREATE_POST_DATA = {
    'title': fake.paragraph(nb_sentences=1)[:255],
    'content': fake.paragraph( nb_sentences=fake.random.randint(7, 15))
}

UPDATE_POST_DATA = {
    'title': fake.paragraph(nb_sentences=1)[:255],
    'content': fake.paragraph(nb_sentences=fake.random.randint(7, 15))
}

TEST_CREDENTIALS = {
    'username': 'admin',
    'password': 'admin'
}


class PostApiTestCase(BaseApiTestCase):
    url_name = "post_api_view"
    serializer_class = PostSerializer

    @cached_property
    def user(self):
        return User.objects.get(username=TEST_CREDENTIALS['username'])
    
    @cached_property
    def credentials(self):
        return self.basic_auth(
            TEST_CREDENTIALS['username'], TEST_CREDENTIALS['password'])
    
    def test_validations(self):
        """Testa as validações do serializer"""
        # Verifica se os erros de validação estão sendo acionados
        self.assertValidationError({}, 'title', 'required')
        self.assertValidationError({}, 'content', 'required')

        # Verifica validação na criação de postagem
        self.check_api_view_create({}, 400, authorization=self.credentials)
        
    def test_list_post(self):
        """Testa a chamada de API de listagem de postagem"""
        response = self.check_api_view_list()
        response_json = response.json()
        self.assertGreater(len(response_json), 0,
                           "A listagem não retornou nenhum objeto")

        for obj in response_json:
            self.check_serialization(obj)

    def test_create_post(self):
        """Testa a chamada de API de criação de postagem"""
        # Verifica se os dados de testes não apresentam erros de validação
        self.assertNoValidationErrors(
            CREATE_POST_DATA, "Houve um erro na validação dos dados de teste de criação de postagem.")

        # Verifica a chamada da api de criação
        response = self.check_api_view_create(
            CREATE_POST_DATA, authorization=self.credentials)

        try:
            response_json = response.json()
        except JSONDecodeError:
            self.fail("A requisição não retornou um JSON válido.")

        pk = response_json.get('id')
        self.assertIsNotNone(
            pk, "Os dados da resposta da criação do objeto não retornou o id do mesmo.")

        # Verifica se o objeto foi criado
        self.assertObjectPresent(pk)

    def test_create_comment_negative(self):
        """Testa a criação de postagem quando não autenticado"""
        self.check_api_view_create(
            CREATE_POST_DATA, expected_status_code=401)

    def test_read_post(self):
        """Testa a chamada de API de detalhamento de postagem"""
        # Certifica-se de que o objeto está no banco antes de iniciar o teste.
        self.assertObjectPresent(
            READ_POST_PK,
            f"A postagem com id '{READ_POST_PK}' não foi encontrado no banco de dados."
            "O teste não poderá ser realizado")

        self.check_api_view_read(READ_POST_PK, authorization=self.credentials)

    def test_update_post(self):
        """Testa a chamada de API de atualização de postagem"""
        
        # Cria um objeto de teste
        instance = self.model_manager.create(
            author=self.user, **CREATE_POST_DATA)
        
        self.assertObjectPresent(
            instance.pk,
            f"A postagem com id '{instance.pk}' não foi encontrado no banco de dados."
            "O teste não poderá ser realizado")


        # Verifica a chamada da API
        self.check_api_view_update(
            instance.pk, UPDATE_POST_DATA, expected_status_code=200,
            authorization=self.credentials)

    def test_update_post_negative(self):
        """Testa a chamada de API de atualização de postagem não pertencentes ao usuário"""
        
        # Certifica-se de que o objeto está no banco antes de iniciar o teste.
        self.assertObjectPresent(
            UPDATE_POST_PK,
            f"A postagem com id '{UPDATE_POST_PK}' não foi encontrado no banco de dados. "
            "O teste não poderá ser realizado")

        # Verifica a chamada da API
        self.check_api_view_update(
            UPDATE_POST_PK, UPDATE_POST_DATA, expected_status_code=403,
            authorization=self.credentials)

    def test_update_post_not_logged_in(self):
        """Testa a atualização de postagem quando não autenticado"""
        self.check_api_view_update(
            UPDATE_POST_PK, UPDATE_POST_DATA, expected_status_code=401)        

    def test_delete_post(self):
        """Testa remoção de objetos pertencente o usuário de teste"""
        # Cria um objeto de teste
        instance = self.model_manager.create(author=self.user,**CREATE_POST_DATA)

        # Verifica o chamado da API
        self.check_api_view_delete(
            instance.pk, expected_status_code=204, authorization=self.credentials)
        
        # Certifica-se que o objeto foi excluído
        self.assertObjectNotPresent(
            instance.pk,
            f"A postagem com id '{DELETE_POST_PK}' foi encontrado no banco de dados.")
        
    def test_delete_post_negative(self):
        """Testa remoção de objetos pertencente a outra pessoa"""
        # Certifica-se de que o objeto está no banco antes de iniciar o teste.
        self.assertObjectPresent(
            DELETE_POST_PK,
            f"A postagem com id '{DELETE_POST_PK}' não foi encontrado no banco de dados."
            "O teste não poderá ser realizado")
        
        # Verifica o chamado da API
        self.check_api_view_delete(
            DELETE_POST_PK, expected_status_code=403, authorization=self.credentials)

        # Certifica-se que o objeto não foi excluído
        self.assertObjectPresent(
            DELETE_POST_PK,
            f"A postagem com id '{DELETE_POST_PK}' não foi encontrado no banco de dados.")
        
    def test_query_performance(self):
        """Testa a performance das queries."""
        with self.assertNumQueries(1):
            self.check_api_view_list()

        with self.assertNumQueries(1):
            self.check_api_view_read(READ_POST_PK)