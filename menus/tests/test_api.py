import json
# Django
from ipaddress import ip_address
from re import I
from socket import IP_RECVDSTADDR
from turtle import update
from urllib import response

import mock
from django.urls import reverse
# from django.test import TestCase
# from django.db import IntegrityError
# from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.test import (
    APIClient,
    APITestCase,
    APITransactionTestCase,
    CoreAPIClient,
    RequestsClient,
)

from menus.models import Module


class ParametroMenuAPITest(APITestCase):
    LOCAL_HOST = ''  # "http://127.0.0.1:8000"
    staging_server = ""

    def setUp(self):
        self.base_url_list = reverse('menus:module-list')

    def base_url_detail(self, pk):
        return reverse(
            'menus:module-detail', kwargs={'pk': pk})

    def test_url_list(self):
        url_list = '/api/modules/'
        self.assertEqual(self.base_url_list, url_list)

    def test_list_modules(self):
        module1 = Module.objects.create(name='Module 1')
        module2 = Module.objects.create(name='Module 2')

        resp_modules = self.client.get(self.base_url_list)
        self.assertEqual(resp_modules.status_code, 200)
        self.assertEqual(resp_modules['content-type'], 'application/json')

        modules_expected = [{'id': module1.pk, 'name': 'Module 1'},
                            {'id': module2.pk, 'name': 'Module 2'}]
        self.assertEqual(json.loads(resp_modules.content), modules_expected)

    def test_post_modules(self):
        new_module = {'name': '  New Module  '}
        resp_module = self.client.post(self.base_url_list, new_module)

        self.assertEqual(resp_module.status_code, 201)
        self.assertEqual(resp_module.data['name'], 'New module')
        self.assertEqual(Module.objects.count(), 1)

    def test_post_module_existent_validation(self):
        Module.objects.create(name='Module 1')
        new_module = {'name': 'module 1'}
        resp_module = self.client.post(
            self.base_url_list, new_module)

        num_exist = Module.objects.count()
        self.assertEqual(resp_module.status_code, 400)
        self.assertEqual(num_exist, 1)
        self.assertEqual(resp_module.data,
                         {'name': ['The module already exists']})

    @mock.patch.object(Module, 'full_clean')
    def test_post_module_existent_integrity(self, mock_method):
        mock_method.return_value = ''

        Module.objects.create(name='Module 1')
        new_module = {'name': 'Module 1'}
        resp_module = self.client.post(
            self.base_url_list, new_module)

        num_exist = Module.objects.count()
        self.assertEqual(resp_module.status_code, 400)
        self.assertEqual(num_exist, 1)
        error_message = resp_module.data
        self.assertEqual(error_message['name'][0].code, 'unique')
        self.assertEqual(error_message['name']
                         [0].title(), 'The Module Already Exists')

    def test_post_module_name_max_length(self):
        new_module = {'name': 'Module 890123456'}
        resp_module = self.client.post(
            self.base_url_list, new_module)

        self.assertEqual(resp_module.status_code, 400)
        self.assertEqual(resp_module.data['name'][0].title(
        ), 'Ensure This Field Has No More Than 15 Characters.')

    def test_url_detail(self):
        url_detail = '/api/modules/1/'
        self.assertEqual(self.base_url_detail(pk=1), url_detail)

    def test_put_module(self):
        new_module = Module.objects.create(name='Module 2')
        update_module = {'name': 'Module 1'}
        resp_module = self.client.put(
            self.base_url_detail(pk=new_module.pk), update_module)
        module = Module.objects.all().first()

        self.assertEqual(resp_module.status_code, 200)
        self.assertEqual(module.name, 'Module 1')

    def test_put_module_module_name_exists(self):
        module1 = Module.objects.create(name='Module 1')
        module2 = Module.objects.create(name='Module 2')

        update_module = {'name': 'Module 2'}
        resp_module = self.client.put(
            self.base_url_detail(pk=module1.pk), update_module)

        module = Module.objects.get(pk=module2.pk)
        self.assertEqual(resp_module.status_code, 400)
        self.assertEqual(module.name, 'Module 2')

    def test_put_module_name_max_length(self):
        module1 = Module.objects.create(name='Module 1')

        update_module = {'name': 'Module 890123456'}

        resp_module = self.client.put(
            self.base_url_detail(pk=module1.pk), update_module)

        self.assertEqual(resp_module.status_code, 400)
        self.assertEqual(resp_module.data['name'][0].title(
        ), 'Ensure This Field Has No More Than 15 Characters.')

    def test_delete_module(self):
        module1 = Module.objects.create(name='Module 1')

        base_url = self.base_url_detail(pk=module1.pk)
        resp_delete = self.client.delete(base_url)

        self.assertEqual(resp_delete.status_code, 204)
        self.assertEqual(Module.objects.all().count(), 0)

    def test_delete_module_not_exist(self):
        base_url = self.base_url_detail(pk=9999)
        resp_delete = self.client.delete(base_url)

        self.assertEqual(resp_delete.status_code, 404)
        self.assertEqual(resp_delete.data, {
                         'message': 'The module with the pk = 9999 doesnt exist'})

    def test_get_module_by_id(self):
        module1 = Module.objects.create(name='Module 1')

        base_url = self.base_url_detail(pk=module1.pk)
        resp_get = self.client.get(base_url)

        self.assertEqual(resp_get.status_code, 200)
        self.assertEqual(resp_get.data, {'id': module1.pk, 'name': 'Module 1'})

    def test_get_module_by_id_not_exist(self):
        base_url = self.base_url_detail(pk=9999)
        resp_get = self.client.get(base_url)

        self.assertEqual(resp_get.status_code, 404)
        self.assertEqual(resp_get.data,  {
                         'message': 'The module with the pk = 9999 doesnt exist'})