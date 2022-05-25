import json
# Django
from ipaddress import ip_address
from socket import IP_RECVDSTADDR
from urllib import response

from django.urls import reverse
#from django.test import TestCase
#from django.db import IntegrityError
#from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.test import (
    APIClient,
    APITestCase,
    APITransactionTestCase,
    CoreAPIClient,
    RequestsClient,
)

from menus.models import Module


class ParametroMenuAPITest(APITransactionTestCase):
    reset_sequences = True
    LOCAL_HOST = ''  # "http://127.0.0.1:8000"
    staging_server = ""

    def setUp(self):

        #self.base_url = reverse('menus:menu_list')
        self.base_url_list = reverse('menus:module-list')
        #self.base_url = f'{self.staging_server}{self.base_url}'
        #self.base_url = f'{self.staging_server}'

    def test_url_list(self):
        url_list = '/api/modules/'
        self.assertEqual(self.base_url_list, url_list)

    def test_list_modules(self):
        #client = APIClient()
        Module.objects.create(name='Module 1')
        Module.objects.create(name='Module 2')

        resp_modules = self.client.get(self.base_url_list)
        self.assertEqual(resp_modules.status_code, 200)
        self.assertEqual(resp_modules['content-type'], 'application/json')

        modules_expected = [{'id': 1, 'name': 'Module 1'},
                            {'id': 2, 'name': 'Module 2'}]
        self.assertEqual(json.loads(resp_modules.content), modules_expected)

    def test_post_modules(self):
        new_module = {'name': '  New Module  '}
        resp_module = self.client.post(self.base_url_list, new_module)

        self.assertEqual(resp_module.status_code, 201)
        self.assertEqual(resp_module.data, {'id': 3, 'name': 'New Module'})
        self.assertEqual(Module.objects.count(), 1)

    def test_post_module_existent(self):
        Module.objects.create(name='Module 1')
        new_module = {'name': 'Module 1'}
        resp_module = self.client.post(self.base_url_list, new_module)

        self.assertEqual(resp_module.status_code, 400)
        #self.assertEqual(resp_module.data, {'id': 3, 'name': 'New Module'})
        #self.assertEqual(Module.objects.count(), 1)

     #   self.assertEqual(resp_modules.data, {'id': 1, 'name': "Module 1"})
    # def test_post_module(self):
    #     #response = self.client.post(self.base_url, {'name': 'Modulo 1'})
    #     self.assertEqual(response.status_code, 201)

    # def test_ruta(self):
    #     ruta = '/apis/menu/'
    #     client = APIClient()

    #     response = client.get('/menu/api/menu/')
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
