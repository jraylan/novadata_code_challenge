# -*- coding: utf-8 -*-
from base64 import b64encode
from django.http import HttpResponse
from django.test import TestCase
from django.urls import reverse
from django.utils.functional import cached_property

from json import JSONDecodeError

from rest_framework.serializers import ModelSerializer

from typing import Type, Union

import json

from faker import Faker


fake = Faker('pt-BR')


def dump_erros(erros: dict):
    """Formata os erros do serializer"""
    dump = ""
    
    for key, values in erros.items():
        dump += f'{key.upper()}:\n'
        dump += '\n'.join(
            [f' * {err}' for err in values])
    
    return dump.strip()


class BaseApiTestCase(TestCase):
    """Classe base para os demais testes de API.
    Possui funcionalidades úteis para teste de requisições à API
    e senilização.
    """
    fixtures = ["test_db_backup.json"]
    # Nome da URL do endpoint da API a ser testada
    url_name: str = None
    # Serializer utilizada no endpoint da API
    serializer_class: Type[ModelSerializer] = None


    @cached_property
    def headers(self):
        return {
            "Accept": "application/json"
        }
    
    @cached_property
    def model_manager(self):
        return self.serializer_class.Meta.model._default_manager

    @classmethod
    def setUpTestData(cls) -> None:
        # Certifica que a classe herdeira implementou as variáveis necessárias
        assert cls.url_name, "A classe herdeira não implementou a variável 'url_name'"
        assert cls.serializer_class, "A classe herdeira não implementou a variável 'serializer_class'"
    

    def get_url(self, pk=None) -> str:
        """Retorna a url reversa para o alias em "url_name"

        Args:
            pk (_type_, optional): Caso definido, irá retornar a url para o objeto com o id especificado. Defaults to None.

        Returns:
            str: URL reversa para o alias em "url_name"
        """
        if pk:
            return reverse(self.url_name, kwargs={"pk": pk})
        return reverse(self.url_name)
    

    def create_serializer(self, data: dict, instance=None)-> ModelSerializer:
        """Inicia uma instância do serializer. Qualquer alteração na criação de uma instância
        pode ser alterada aqui"""

        return self.serializer_class(instance=instance, data=data)
    
    def check_serialization(self, data: dict) -> ModelSerializer:
        """Verifica se os dados passado foram corretamente serializados e representam
        um objeto no banco de dados"""
        pk = data.get('id')
        self.assertIsNotNone(pk, 'Os dados não possuem o campo "id" ou o valor do "id" é inválido.')

        model_manager = self.model_manager

        try:
            instance = model_manager.filter(id=pk).first()
        except TypeError:
            self.fail("O tipo de dado contido no campo id não é válido")
        except Exception as e:
            self.fail(
                f"Uma query não pode ser executar. {str(e)}")
        # Verifica se a instância foi encontrada no banco de dados
        self.assertIsNotNone(instance, f'A instancia com id "{pk}" não foi encontrada.')

        serializer_instance = self.create_serializer(instance=instance, data=data)

        # Verifica se os dados são válidos
        self.assertTrue(serializer_instance.is_valid(),
                        f"Os dados não são válidos. {dump_erros(serializer_instance.errors)}")
        
        return serializer_instance

    def check_api_view_list(
            self, expected_status_code: int = 200, authorization = None,
            expected_response_type: Union[list, dict] = list) -> HttpResponse:
        """Performa as checagens na listagem de objetos via API e retorna a resposta.

        Args:
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
            self.get_url(), headers=self.headers, **auth_header)

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

    def check_api_view_create(
            self, json_data: dict, expected_status_code: int = 201, authorization = None,
            expected_response_type: Union[list, dict] = dict) -> HttpResponse:
        """Performa as checagens na criação de objetos via API e retorna a resposta.

        Args:
            json_data (dict): Payload da requisição
            expected_status_code (int, optional): Status esperado para a chamada. Defaults to 201.
            authorization (str, optional): Conteúdo a ser enviado no cabeçalho 'Authorization'
            expected_response_type (Union[list, dict], optional): Tipo de dado esperado na resposta. Defaults to dict.

        Returns:
            HttpResponse: Resposta da requisição.
        """

        if authorization:
            auth_header = {
                'HTTP_AUTHORIZATION': authorization
            }
        else:
            auth_header = {}

        response = self.client.post(
            self.get_url(), data=json.dumps(json_data), content_type="application/json",
            headers=self.headers, **auth_header)

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

        # Verifica se um dicionário foi retornado
        self.assertIsInstance(json_response, expected_response_type,
                         f"A busca não retornou um dicionário. Tipo retornado: {type(json_response)}")

        return response

    def check_api_view_read(
            self, pk: int, expected_status_code: int = 200, authorization = None,
            expected_response_type: Union[list, dict] = dict) -> HttpResponse:
        """Performa as checagens na leitura de objetos via API e retorna a resposta

        Args:
            pk (int): ID do objeto
            expected_status_code (int, optional): Status esperado para a chamada. Defaults to 201.
            authorization (str, optional): Conteúdo a ser enviado no cabeçalho 'Authorization'
            expected_response_type (Union[list, dict], optional): Tipo de dado esperado na resposta. Defaults to dict.

        Returns:
            HttpResponse: Resposta da requisição."""

        if authorization:
            auth_header = {
                'HTTP_AUTHORIZATION': authorization
            }
        else:
            auth_header = {}

        response = self.client.get(
            self.get_url(pk), headers=self.headers, **auth_header)

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
        
        # Verifica se um dicionário foi retornado
        self.assertIsInstance(json_response, expected_response_type,
                         f"A busca não retornou um dicionário. Tipo retornado: {type(json_response)}")
    

        return response
    
    def basic_auth(self, user:str, password:str) -> str:
        user_pass = user.encode('utf-8') + b':' + password.encode('utf-8')    
        return f'Basic {b64encode(user_pass).decode("ascii")}'


    def check_api_view_update(
            self, pk: int, json_data: dict, expected_status_code: int = 200,
            authorization = None, expected_response_type: Union[list, dict] = dict) -> HttpResponse:
        """Performa as checagens na atualização de objetos via API e retorna a resposta

        Args:
            pk (int): ID do objeto
            json_data (dict): Payload da requisição
            expected_status_code (int, optional): Status esperado para a chamada. Defaults to 201.
            authorization (str, optional): Conteúdo a ser enviado no cabeçalho 'Authorization'
            expected_response_type (Union[list, dict], optional): Tipo de dado esperado na resposta. Defaults to dict.

        Returns:
            HttpResponse: Resposta da requisição."""

        if authorization:
            auth_header = {
                'HTTP_AUTHORIZATION': authorization
            }
        else:
            auth_header = {}

        response = self.client.put(
            self.get_url(pk), data=json.dumps(json_data),
            content_type="application/json", headers=self.headers, **auth_header)

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

        # Verifica se um dicionário foi retornado
        self.assertIsInstance(json_response, expected_response_type,
                         f"A busca não retornou um dicionário. Tipo retornado: {type(json_response)}")

        return response

    def check_api_view_delete(
            self, pk: int, expected_status_code: int = 204,  authorization = None,) -> HttpResponse:
        """Performa as checagens na remoção de objetos via API e retorna a resposta

        Args:
            pk (int): ID do objeto
            expected_status_code (int, optional): Status esperado para a chamada. Defaults to 201.
            authorization (str, optional): Conteúdo a ser enviado no cabeçalho 'Authorization'

        Returns:
            HttpResponse: Resposta da requisição."""

        if authorization:
            auth_header = {
                'HTTP_AUTHORIZATION': authorization
            }
        else:
            auth_header = {}

        response = self.client.delete(
            self.get_url(pk), headers=self.headers, **auth_header)

        # Testa o código da resposta da requisição
        self.assertEqual(response.status_code, expected_status_code,
                         "A requisição retornou um status diferente do esperado. "
                         f"Status esperado: {expected_status_code}. "
                         f"Status retornado: {response.status_code}."
                         f"\nResposta: {response.content}")
        return response
    

    def assertValidationError(
            self, data_or_serializer: Union[dict, ModelSerializer],
            field: str, code: str, msg: str = None) -> None:
        """Verifica se um código de erro está presente em um campo dos dados
        após a validação feita pelo serializer.

        Args:
            data_or_serializer (Union[dict, ModelSerializer]): Dados a serem serializados ou uma instância do serializer
            field (str): Campo a ser validado
            code (str): Código do erro esperado
            msg (str, optional): Mensagem a ser exibida em caso de falha na checagem.
        """

        if isinstance(data_or_serializer, ModelSerializer):
            serializer = data_or_serializer
        else:
            serializer = self.create_serializer(data_or_serializer)

        self.assertFalse(serializer.is_valid(),
                         "Os dados foram serializados sem erros quando um erro era esperado.")
        
        self.assertIn(field, serializer.errors.keys(), "O campo informado não possui erros")

        for err in serializer.errors[field]:
            if err.code == code:
                return
            
        if msg:
            self.fail(msg)
        else:        
            self.fail(f'Não foram encontrados erros do tipo "{code}" no campo "{field}".')

    def assertNoValidationError(
            self, data_or_serializer: Union[dict, ModelSerializer],
            field: str, code: str, msg: str = None) -> None:
        """Certifica-se de que um código de erro não está presente em um campo dos dados
        após a validação feita pelo serializer.

        Args:
            data_or_serializer (Union[dict, ModelSerializer]): Dados a serem serializados ou uma instância do serializer
            field (str): Campo a ser validado
            code (str): Código do erro esperado
            msg (str, optional): Mensagem a ser exibida em caso de falha na checagem."""

        if isinstance(data_or_serializer, ModelSerializer):
            serializer = data_or_serializer
        else:
            serializer = self.create_serializer(data_or_serializer)

        if serializer.is_valid():
            return

        if not field:
            for err in serializer.errors.values():
                if not code or err.code == code:
                    if msg:
                        self.fail(msg)
                    self.fail(
                        f'Foram encontrados erros do tipo "{code}" no campo "{field}".')

        if field not in serializer.errors:
            return

        for err in serializer.errors[field]:
            if not code or err.code == code:
                if msg:
                    self.fail(msg)
                self.fail(
                    f'Foram encontrados erros do tipo "{code}" no campo "{field}".')
    
    def assertNoValidationErrors(
            self, data_or_serializer: Union[dict, ModelSerializer],
            msg: str = None) -> None:
        """Certifica-se de que não há erros após a validação feita pelo serializer.

        Args:
            data_or_serializer (Union[dict, ModelSerializer]): Dados a serem serializados ou uma instância do serializer
            msg (str, optional): Mensagem a ser exibida em caso de falha na checagem."""

        if isinstance(data_or_serializer, ModelSerializer):
            serializer = data_or_serializer
        else:
            serializer = self.create_serializer(data_or_serializer)

        if serializer.is_valid():
            return
        
        if msg:
            self.fail(msg % {
                'errors': dump_erros(serializer.errors)
            })

        self.fail(
            'Um ou mais errors foram encontrados na validação dos dados. '
            f'Erros: {dump_erros(serializer.errors)}')

    def assertObjectPresent(self, pk: int, msg=None):
        """Certifica-se de que um objeto do tipo definido no "Meta.model" do serializer
        definido em "serializer_class" está presente no banco de dados.

        Args:
            pk (int): Chave privada do objeto a ser buscado
            msg (_type_, optional): Mensagem a ser exibida em caso de falha na checagem . Defaults to None.
        """
        model_manager = self.model_manager

        if not model_manager.filter(id=pk).exists():
            if msg:
                self.fail(msg)
            self.fail(f"Objeto com id '{pk}' não encontrado no banco de dados.")

    def assertObjectNotPresent(self, pk: int, msg=None):
        """Certifica-se de que um objeto do tipo definido no "Meta.model" do serializer
        definido em "serializer_class" não está presente no banco de dados.

        Args:
            pk (int): Chave privada do objeto a ser buscado
            msg (_type_, optional): Mensagem a ser exibida em caso de falha na checagem . Defaults to None.
        """
        model_manager = self.model_manager

        if model_manager.filter(id=pk).exists():
            if msg:
                self.fail(msg)
            self.fail(f"Objeto com id '{pk}' encontrado no banco de dados.")

