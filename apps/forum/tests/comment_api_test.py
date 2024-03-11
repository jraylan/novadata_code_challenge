# -*- coding: utf-8 -*-
from .base import *
from apps.forum.serializers import CommentSerializer
from django.contrib.auth.models import User
from django.utils.functional import cached_property


READ_COMMENT_PK = 1
UPDATE_COMMENT_PK = 2
DELETE_COMMENT_PK = 3
NO_DELETE_COMMENT_PK = 4


CREATE_COMMENT_DATA = {
    'content': fake.paragraph( nb_sentences=fake.random.randint(7, 15)),
    'post': 11
}

UPDATE_COMMENT_DATA = {
    'content': fake.paragraph(nb_sentences=fake.random.randint(7, 15)),
    'post': 11
}

TEST_CREDENTIALS = {
    'username': 'admin',
    'password': 'admin'
}


class CommentApiTestCase(BaseApiTestCase):
    url_name = "comment_api_view"
    serializer_class = CommentSerializer

    @cached_property
    def user(self):
        return User.objects.get(username=TEST_CREDENTIALS['username'])
    
    @cached_property
    def credentials(self):
        return self.basic_auth(
            TEST_CREDENTIALS['username'], TEST_CREDENTIALS['password'])

    def check_api_view_list_post_comments(
            self, pk, expected_status_code: int = 200, authorization=None,
            expected_response_type: Union[list, dict] = list) -> HttpResponse:
        """Performa as checagens na listagem de objetos via API e retorna a resposta.

        Args:
            pk (dict): Payload da requisição
            expected_status_code (int, optional): Status esperado para a chamada. Defaults to 201.
            authorization (str, optional): Conteúdo a ser enviado no cabeçalho 'Authorization'
            expected_response_type (Union[list, dict], optional): Tipo de dado esperado na resposta. Defaults to list.

        Returns:
            HttpResponse: Resposta da requisição."""

        if authorization:
            auth_header = {
                'HTTP_AUTHORIZATION': authorization
            }
        else:
            auth_header = {}

        response = self.client.get(
            reverse('post_comments_api_view', kwargs={'pk': pk}), headers=self.headers, **auth_header)

        # Testa o código da resposta da requisição
        self.assertEqual(response.status_code, expected_status_code,
                         "A requisição retornou um status diferente do esperado. "
                         f"Status esperado: {expected_status_code}. "
                         f"Status retornado: {response.status_code} "
                         f"\nResposta:\n{response.content.decode('utf8')}")
        try:
            json_response = response.json()
        except JSONDecodeError as e:
            self.fail(
                f"A requisição não retornou um json válido. Exceção: {e.msg}")

        # Verifica se uma lista foi retornada
        self.assertIsInstance(json_response, expected_response_type,
                              f"A listagem não retornou uma lista. Tipo retornado: {type(json_response)}")

        return response

    def test_validations(self):
        """Testa as validações do serializer"""
        # Verifica se os erros de validação estão sendo acionados
        self.assertValidationError({}, 'content', 'required')

        # Verifica validação na criação de comentário
        self.check_api_view_create({}, 400, authorization=self.credentials)
        
    def test_list_comments(self):
        """Testa a chamada de API de listagem de comentário"""
        response = self.check_api_view_list()
        response_json = response.json()
        self.assertGreater(len(response_json), 0,
                           "A listagem não retornou nenhum objeto")

        for obj in response_json:
            self.check_serialization(obj)

    def test_create_comment(self):
        """Testa a chamada de API de criação de comentário"""
        # Verifica se os dados de testes não apresentam erros de validação
        self.assertNoValidationErrors(
            CREATE_COMMENT_DATA, "Houve um erro na validação dos dados de teste de criação de comentário.")

        # Verifica a chamada da api de criação
        response = self.check_api_view_create(
            CREATE_COMMENT_DATA, authorization=self.credentials)

        try:
            response_json = response.json()
        except JSONDecodeError:
            self.fail("A requisição não retornou um JSON válido.")

        pk = response_json.get('id')
        self.assertIsNotNone(
            pk, "Os dados da resposta da criação do objeto não retornou o id do mesmo.")

        # Verifica se o objeto foi criado
        self.assertObjectPresent(pk)

    # Verifica a chamada da api de criação
    def test_create_comment_negative(self):
        """Testa a criação de comentário quando não autenticado"""
        self.check_api_view_create(
            CREATE_COMMENT_DATA, expected_status_code=401)

    def test_read_comment(self):
        """Testa a chamada de API de detalhamento de comentário"""
        # Certifica-se de que o objeto está no banco antes de iniciar o teste.
        self.assertObjectPresent(
            READ_COMMENT_PK,
            f"O comentário com id '{READ_COMMENT_PK}' não foi encontrado no banco de dados."
            "O teste não poderá ser realizado")

        self.check_api_view_read(READ_COMMENT_PK, authorization=self.credentials)

    def test_update_comment(self):
        """Testa a chamada de API de atualização de postagem"""

        # Cria um objeto de teste
        instance = self.model_manager.create(
            author=self.user,
            content=CREATE_COMMENT_DATA['content'],
            post_id=CREATE_COMMENT_DATA['post'])

        self.assertObjectPresent(
            instance.pk,
            f"A postagem com id '{instance.pk}' não foi encontrado no banco de dados."
            "O teste não poderá ser realizado")

        # Verifica a chamada da API
        self.check_api_view_update(
            instance.pk, UPDATE_COMMENT_DATA, expected_status_code=200,
            authorization=self.credentials)

    def test_update_comment_negative(self):
        """Testa a atualização de comentário não pertencentes ao usuário de teste"""
        # Certifica-se de que o objeto está no banco antes de iniciar o teste.
        self.assertObjectPresent(
            UPDATE_COMMENT_PK,
            f"O comentário com id '{UPDATE_COMMENT_PK}' não foi encontrado no banco de dados. "
            "O teste não poderá ser realizado")

        # Verifica a chamada da API
        self.check_api_view_update(
            UPDATE_COMMENT_PK, UPDATE_COMMENT_DATA, expected_status_code=403,
            authorization=self.credentials)

    def test_update_comment_not_logged_in(self):
        """Testa a atualização de comentário quando não autenticado"""
        self.check_api_view_update(
            UPDATE_COMMENT_PK, UPDATE_COMMENT_DATA, expected_status_code=401)

    def test_delete_comment(self):
        """Testa remoção de objetos pertencente o usuário de teste"""
        # Cria um objeto de teste
        instance = self.model_manager.create(
            author=self.user,
            content=CREATE_COMMENT_DATA['content'],
            post_id=CREATE_COMMENT_DATA['post'])

        # Verifica o chamado da API
        self.check_api_view_delete(
            instance.pk, expected_status_code=204, authorization=self.credentials)
        
        # Certifica-se que o objeto foi excluído
        self.assertObjectNotPresent(
            instance.pk,
            f"O comentário com id '{DELETE_COMMENT_PK}' foi encontrado no banco de dados.")
        
    def test_delete_comment_negative(self):
        """Testa remoção de objetos pertencente a outra pessoa"""
        # Certifica-se de que o objeto está no banco antes de iniciar o teste.
        self.assertObjectPresent(
            DELETE_COMMENT_PK,
            f"O comentário com id '{DELETE_COMMENT_PK}' não foi encontrado no banco de dados."
            "O teste não poderá ser realizado")
        
        # Verifica o chamado da API
        self.check_api_view_delete(
            DELETE_COMMENT_PK, expected_status_code=403, authorization=self.credentials)

        # Certifica-se que o objeto não foi excluído
        self.assertObjectPresent(
            DELETE_COMMENT_PK,
            f"O comentário com id '{DELETE_COMMENT_PK}' não foi encontrado no banco de dados.")

    def test_query_performance(self):
        """Testa a performance das queries."""
        with self.assertNumQueries(1):
            self.check_api_view_list()

        with self.assertNumQueries(1):
            self.check_api_view_read(READ_COMMENT_PK)

        with self.assertNumQueries(1):
            self.check_api_view_list_post_comments(1)
        
