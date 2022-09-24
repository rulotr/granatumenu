import json
import unittest
from operator import itemgetter, mod
# Django
from re import I
from socket import IP_RECVDSTADDR
from urllib import response

import mock
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import (
    APIClient,
    APITestCase,
    APITransactionTestCase,
    URLPatternsTestCase,
)

from menus.models import Menu, Module
from menus.serializers import MenuSerializer
from menus.tests.factories import MenuFactory, ModuleFactory

URL_MODULES = '/api/modules/'
URL_MENU = '/api/menu/'
URL_MODULES_LIST_NAME = 'menus:module-list'
URL_MODULES_DETAIL_NAME = 'menus:module-detail'
URL_MENU_LIST_NAME = 'menus:menu-list'
URL_MENU_DETAIL_NAME = 'menus:menu-detail'
URL_MENU_TREE_DETAIL_NAME = 'menus:menu-tree-detail'


class ParametroModuleAPITest(APITestCase):

    def setUp(self):
        self.base_url_list = reverse(URL_MODULES_LIST_NAME)
        ModuleFactory.reset_sequence()

    def base_url_detail(self, pk):
        return reverse(
            URL_MODULES_DETAIL_NAME, kwargs={'pk': pk})

    def test_url_list(self):
        url_list = URL_MODULES
        self.assertEqual(self.base_url_list, url_list)

    def test_list_modules(self):
        ModuleFactory.create_batch(2)

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
        self.assertEqual(resp_module.data['name'], 'New module')
        self.assertEqual(Module.objects.count(), 1)

    def test_post_module_existent_validation(self):
        ModuleFactory()
        new_module = {'name': 'module 1'}
        resp_module = self.client.post(
            self.base_url_list, new_module)

        num_exist = Module.objects.count()
        self.assertEqual(resp_module.status_code, 400)
        self.assertEqual(num_exist, 1)
        self.assertEqual(resp_module.data['name'][0].title(),
                         'The Module Already Exists')

    @mock.patch.object(Module, 'full_clean')
    def test_post_module_existent_integrity(self, mock_method):
        mock_method.return_value = ''
        ModuleFactory()
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
        url_detail = URL_MODULES + '1/'
        self.assertEqual(self.base_url_detail(pk=1), url_detail)

    def test_put_module(self):
        new_module = ModuleFactory(name='Module 2')
        update_module = {'name': 'Module 1'}
        resp_module = self.client.put(
            self.base_url_detail(pk=new_module.pk), update_module)
        module = Module.objects.all().first()

        self.assertEqual(resp_module.status_code, 200)
        self.assertEqual(module.name, 'Module 1')

    def test_put_module_module_name_exists(self):
        ModuleFactory.create_batch(2)

        update_module = {'name': 'Module 2'}
        resp_module = self.client.put(
            self.base_url_detail(pk=1), update_module)

        module = Module.objects.get(pk=2)
        self.assertEqual(resp_module.status_code, 400)
        self.assertEqual(module.name, 'Module 2')

    def test_put_module_name_max_length(self):
        module1 = ModuleFactory()

        update_module = {'name': 'Module 890123456'}
        resp_module = self.client.put(
            self.base_url_detail(pk=module1.pk), update_module)

        self.assertEqual(resp_module.status_code, 400)
        self.assertEqual(resp_module.data['name'][0].title(
        ), 'Ensure This Field Has No More Than 15 Characters.')

    def test_delete_module(self):
        module1 = ModuleFactory()
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
        module1 = ModuleFactory()
        base_url = self.base_url_detail(pk=module1.pk)
        resp_get = self.client.get(base_url)

        self.assertEqual(resp_get.status_code, 200)
        self.assertEqual(resp_get.data, {'id': module1.pk, 'name': 'Module 1'})

    def test_get_module_by_id_not_exist(self):
        base_url = self.base_url_detail(pk=9999)
        resp_get = self.client.get(base_url)

        self.assertEqual(resp_get.status_code, 404)
        self.assertEqual(resp_get.data,
                         {'detail': ErrorDetail(string='Not found.', code='not_found')})


class ParametroMenuAPITest(APITestCase):

    def setUp(self):
        self.base_url_list = reverse(URL_MENU_LIST_NAME)
        ModuleFactory.reset_sequence()
        MenuFactory.reset_sequence()

    def base_url_detail(self, pk):
        return reverse(
            URL_MENU_DETAIL_NAME, kwargs={'pk': pk})

    def base_url_detail_tree(self, pk):
        return reverse(
            URL_MENU_TREE_DETAIL_NAME, kwargs={'pk': pk})

    def test_url_list(self):
        url_list = URL_MENU
        self.assertEqual(self.base_url_list, url_list)

    def test_menuserializer_invalid(self):
        data_menu = {'name': 'Menu 1', 'module': 12}

        serializer = MenuSerializer(data=data_menu)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(set(serializer.errors),  {'module'})

    def test_menuserializer_valid(self):
        ModuleFactory()
        data_menu = {'name': 'Menu 1', 'module': 1}

        serializer = MenuSerializer(data=data_menu)
        self.assertTrue(serializer.is_valid())
        data = serializer.data
        self.assertCountEqual(data.keys(), ['name', 'module', 'parent'])
        self.assertEqual(data['name'], 'Menu 1')

    def test_post_menu(self):
        ModuleFactory()

        new_menu = {'name': 'Menu 1', 'module': 1}

        resp_module = self.client.post(self.base_url_list, new_menu)

        self.assertEqual(resp_module.status_code, 201)
        self.assertEqual(resp_module.data['name'], 'Menu 1')
        self.assertEqual(Menu.objects.count(), 1)

    def test_post_many_menus_same_module(self):

        module1 = ModuleFactory()

        menu1 = {'name': 'Menu 1', 'module': module1.pk}
        menu2 = {'name': 'Menu 2', 'module': module1.pk}
        menu3 = {'name': 'Menu 3', 'module': module1.pk}

        resp1 = self.client.post(self.base_url_list, menu1)
        resp2 = self.client.post(self.base_url_list, menu2)
        resp3 = self.client.post(self.base_url_list, menu3)

        self.assertEqual(resp1.status_code, 201)
        self.assertEqual(resp2.status_code, 201)
        self.assertEqual(resp3.status_code, 201)
        self.assertEqual(resp1.data,  {
                         'id': resp1.data['id'], 'name': 'Menu 1', 'module': module1.pk, 'parent': None, 'order': 1})
        self.assertEqual(resp2.data, {
                         'id': resp2.data['id'], 'name': 'Menu 2', 'module': module1.pk, 'parent': None, 'order': 2})
        self.assertEqual(resp3.data, {
                         'id': resp3.data['id'], 'name': 'Menu 3', 'module': module1.pk, 'parent': None, 'order': 3})

        self.assertEqual(Menu.objects.count(), 3)

    def test_post_many_menus_three_levels(self):
        module1 = ModuleFactory()

        menu1 = {'name': 'Menu 1', 'module': module1.pk}
        resp1 = self.client.post(self.base_url_list, menu1)

        menu1_1 = {'name': 'Menu 1.1', 'parent': resp1.data['id']}
        resp_1_1 = self.client.post(self.base_url_list, menu1_1)

        menu1_2 = {'name': 'Menu 1.1.1', 'parent': resp_1_1.data['id']}
        resp_1_1_1 = self.client.post(self.base_url_list, menu1_2)
        menu1_3 = {'name': 'Menu 1.1.2', 'parent': resp_1_1.data['id']}
        resp_1_1_1 = self.client.post(self.base_url_list, menu1_3)

        self.assertEqual(resp1.status_code, 201)
        self.assertEqual(resp_1_1.status_code, 201)
        self.assertEqual(resp_1_1_1.status_code, 201)

        menus = Menu.objects.all().order_by('id').values('name', 'parent', 'order')
        self.assertEqual(menus.count(), 4)

        self.assertDictEqual(
            menus[0], {'name': 'Menu 1', 'parent': None, 'order': 1})
        self.assertDictEqual(
            menus[1], {'name': 'Menu 1.1', 'parent': menu1_1['parent'], 'order': 1})
        self.assertDictEqual(
            menus[2], {'name': 'Menu 1.1.1', 'parent': menu1_2['parent'], 'order': 1})
        self.assertDictEqual(
            menus[3], {'name': 'Menu 1.1.2', 'parent': menu1_2['parent'], 'order': 2})

    def test_post_menus_different_module(self):
        ModuleFactory.create_batch(2)

        menu1 = {'name': 'Menu M1', 'module': 1}
        resp1 = self.client.post(self.base_url_list, menu1)
        menu2 = {'name': 'Menu M2', 'module': 2}
        resp2 = self.client.post(self.base_url_list, menu2)
        menu3 = {'name': 'Menu M2.1', 'parent': resp2.data['id']}
        resp3 = self.client.post(self.base_url_list, menu3)

        self.assertEqual(resp1.status_code, 201)
        self.assertEqual(resp2.status_code, 201)
        self.assertEqual(resp3.status_code, 201)

        self.assertEqual(resp1.data['module'], 1)
        self.assertEqual(resp2.data['module'], 2)
        self.assertEqual(resp3.data['module'], 2)

    def test_post_menu_not_module(self):
        menu1 = {'name': 'Menu M1', 'module': 1}
        resp = self.client.post(self.base_url_list, menu1)

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.data['module'][0].title(
        ), 'Invalid Pk "1" - Object Does Not Exist.')

    def test_post_menu_max_length(self):
        module1 = ModuleFactory()

        menu1 = {'name': 'Menu with max length', 'module': module1.pk}
        resp = self.client.post(self.base_url_list, menu1)

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.data['name'][0].title(
        ), 'Ensure This Field Has No More Than 15 Characters.')

    def test_url_detail(self):
        url_detail = URL_MENU + '1/'
        self.assertEqual(self.base_url_detail(pk=1), url_detail)

    def test_change_name_menu(self):
        module1 = ModuleFactory()

        menu1 = {'name': 'Menu 1', 'module': module1.pk}
        resp = self.client.post(self.base_url_list, menu1)

        update_menu = {'name': 'Menu 1 Change'}
        resp_memu = self.client.put(
            self.base_url_detail(pk=resp.data['id']), update_menu)
        menu_update = Menu.objects.all().first()

        self.assertEqual(resp_memu.status_code, 200)
        self.assertEqual(menu_update.name, 'Menu 1 change')

    def test_change_order_menu(self):
        module1 = ModuleFactory()
        menu1 = MenuFactory(module=module1, order=1)
        menu2 = MenuFactory(module=module1, order=2)
        menu3 = MenuFactory(module=module1, order=3)

        change_order = {'order': 2, 'name': 'Change my name'}
        resp_menu = self.client.patch(
            self.base_url_detail(pk=menu1.pk), change_order)
        self.assertEqual(resp_menu.status_code, 200)

        menus = Menu.objects.all().order_by('order').values('name')
        self.assertDictEqual(
            menus[0], {'name': 'Menu 2'})
        self.assertDictEqual(
            menus[1], {'name': 'Menu 1'})
        self.assertDictEqual(
            menus[2], {'name': 'Menu 3'})

    def test_url_tree_module(self):
        url_tree_module = URL_MENU + 'module/1/'
        self.assertEqual(self.base_url_detail_tree(pk=1), url_tree_module)

    def test_get__tree_detail_simple_menu(self):
        module1 = ModuleFactory()
        menu1 = MenuFactory(module=module1, order=1)

        resp_tree_menu = self.client.get(
            self.base_url_detail_tree(pk=module1.pk))
        self.assertEqual(resp_tree_menu.status_code, 200)
        self.assertEqual(json.loads(resp_tree_menu.content), [{
                         'pk': menu1.pk, 'name': 'Menu 1', 'module': module1.pk,   'order': 1, 'parent': None, 'deep': 0, 'sub_menu': []}])

    def test_get__tree_detail_menu(self):
        module1 = ModuleFactory()
        menu1 = MenuFactory(module=module1, order=1)
        menu1_1 = MenuFactory(
            name='Menu 1.1', module=module1, parent=menu1, order=1)
        menu1_1_1 = MenuFactory(
            name='Menu 1.1.1', module=module1, parent=menu1_1, order=1)
        menu1_1_2 = MenuFactory(
            name='Menu 1.1.2', module=module1, parent=menu1_1, order=2)

        resp_tree_menu = self.client.get(
            self.base_url_detail_tree(pk=module1.pk))

        self.assertEqual(resp_tree_menu.status_code, 200)

        result_exp = [
            {'pk': menu1.pk, 'name': 'Menu 1', 'module': 1, 'order': 1, 'parent': None, 'deep': 0,
             'sub_menu': [
                 {'pk': menu1_1.pk, 'name': 'Menu 1.1', 'module': 1, 'order': 1, 'parent': menu1.pk, 'deep': 1,
                  'sub_menu': [
                      {'pk': menu1_1_1.pk, 'name': 'Menu 1.1.1', 'module': 1,
                       'order': 1, 'parent': menu1_1.pk, 'deep': 2, 'sub_menu': []},
                      {'pk': menu1_1_2.pk, 'name': 'Menu 1.1.2', 'module': 1,
                          'order': 2, 'parent': menu1_1.pk, 'deep': 2, 'sub_menu': []}
                  ]
                  }
             ]
             }
        ]

        json_tree_menu = json.loads(resp_tree_menu.content)
        self.assertEqual(len(json_tree_menu), 1)

        m1 = json_tree_menu[0]
        m1_1 = m1.pop('sub_menu')[0]
        m1_1_1, m1_1_2 = itemgetter(0, 1)(m1_1.pop('sub_menu'))

        self.assertEqual(m1, {'pk': m1['pk'], 'name': 'Menu 1',
                              'module': 1, 'order': 1, 'deep': 0, 'parent': None})
        self.assertEqual(m1_1, {'pk': m1_1['pk'], 'name': 'Menu 1.1',
                         'module': 1, 'order': 1, 'parent': m1['pk'], 'deep': 1})
        self.assertEqual(m1_1_1, {'pk': m1_1_1['pk'], 'name': 'Menu 1.1.1', 'module': 1,
                                  'order': 1, 'parent': m1_1['pk'], 'deep': 2, 'sub_menu': []})
        self.assertEqual(m1_1_2, {'pk': m1_1_2['pk'], 'name': 'Menu 1.1.2', 'module': 1,
                                  'order': 2, 'parent': m1_1['pk'], 'deep': 2, 'sub_menu': []})

        self.assertEqual(json.loads(resp_tree_menu.content), result_exp)
