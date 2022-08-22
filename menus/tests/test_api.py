import json
import unittest
# Django
from re import I
from socket import IP_RECVDSTADDR
from urllib import response

import mock
from django.urls import reverse
from rest_framework import status
from rest_framework.test import (
    APIClient,
    APITestCase,
    APITransactionTestCase,
    URLPatternsTestCase,
)

from menus.models import Menu, Module
from menus.serializers import MenuSerializer


class ParametroModuleAPITest(APITestCase):

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
        self.assertEqual(resp_module.data['name'][0].title(),
                         'The Module Already Exists')

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


class ParametroMenuAPITest(APITestCase):

    def setUp(self):
        self.base_url_list = reverse('menus:menu-list')

    def base_url_detail(self, pk):
        return reverse(
            'menus:menu-detail', kwargs={'pk': pk})

    def base_url_detail_tree(self, pk):
        return reverse(
            'menus:menu-tree-detail', kwargs={'pk': pk})

    def test_url_list(self):
        url_list = '/api/menu/'
        self.assertEqual(self.base_url_list, url_list)

    def test_menuserializer_invalid(self):
        data_menu = {'name': 'Menu 1', 'module': 12}

        serializer = MenuSerializer(data=data_menu)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(set(serializer.errors),  {'module'})

    def test_menuserializer_valid(self):
        module1 = Module.objects.create(name="Module 1")
        data_menu = {'name': 'Menu 1', 'module': module1.pk}

        serializer = MenuSerializer(data=data_menu)
        self.assertTrue(serializer.is_valid())
        data = serializer.data
        self.assertCountEqual(data.keys(), ['name', 'module', 'parent'])
        self.assertEqual(data['name'], 'Menu 1')

    def test_post_menu(self):
        module1 = Module.objects.create(name="Module 1")

        new_menu = {'name': 'Menu 1', 'module': module1.pk}

        resp_module = self.client.post(self.base_url_list, new_menu)

        self.assertEqual(resp_module.status_code, 201)
        self.assertEqual(resp_module.data['name'], 'Menu 1')
        self.assertEqual(Menu.objects.count(), 1)

    def test_post_many_menus_same_module(self):
        module1 = Module.objects.create(name="Module 1")

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
        module1 = Module.objects.create(name="Module 1")
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
        module1 = Module.objects.create(name="Module 1")
        module2 = Module.objects.create(name="Module 2")

        menu1 = {'name': 'Menu M1', 'module': module1.pk}
        resp1 = self.client.post(self.base_url_list, menu1)
        menu2 = {'name': 'Menu M2', 'module': module2.pk}
        resp2 = self.client.post(self.base_url_list, menu2)
        menu3 = {'name': 'Menu M2.1', 'parent': resp2.data['id']}
        resp3 = self.client.post(self.base_url_list, menu3)

        self.assertEqual(resp1.status_code, 201)
        self.assertEqual(resp2.status_code, 201)
        self.assertEqual(resp3.status_code, 201)

        self.assertEqual(resp1.data['module'], module1.pk)
        self.assertEqual(resp2.data['module'], module2.pk)
        self.assertEqual(resp3.data['module'], module2.pk)

    def test_post_menu_not_module(self):
        menu1 = {'name': 'Menu M1', 'module': 1}
        resp = self.client.post(self.base_url_list, menu1)

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.data['module'][0].title(
        ), 'Invalid Pk "1" - Object Does Not Exist.')

    def test_post_menu_max_length(self):
        module1 = Module.objects.create(name="Module 1")
        menu1 = {'name': 'Menu with max length', 'module': module1.pk}
        resp = self.client.post(self.base_url_list, menu1)

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.data['name'][0].title(
        ), 'Ensure This Field Has No More Than 15 Characters.')

    def test_url_detail(self):
        url_detail = '/api/menu/1/'
        self.assertEqual(self.base_url_detail(pk=1), url_detail)

    def test_change_name_menu(self):
        module1 = Module.objects.create(name='Module 1')
        menu1 = {'name': 'Menu 1', 'module': module1.pk}
        resp = self.client.post(self.base_url_list, menu1)

        update_menu = {'name': 'Menu 1 Change'}
        resp_memu = self.client.put(
            self.base_url_detail(pk=resp.data['id']), update_menu)
        menu_update = Menu.objects.all().first()

        self.assertEqual(resp_memu.status_code, 200)
        self.assertEqual(menu_update.name, 'Menu 1 change')

    def test_change_order_menu(self):
        module1 = Module.objects.create(name="Module 1")

        menu1 = {'name': 'Menu 1', 'module': module1.pk}
        menu2 = {'name': 'Menu 2', 'module': module1.pk}
        menu3 = {'name': 'Menu 3', 'module': module1.pk}

        menu1['pk'] = self.client.post(self.base_url_list, menu1).data['id']
        menu2['pk'] = self.client.post(self.base_url_list, menu2)
        menu3['pk'] = self.client.post(self.base_url_list, menu3)

        change_order = {'order': 2, 'name': 'Change my name'}
        resp_menu = self.client.patch(
            self.base_url_detail(pk=menu1['pk']), change_order)
        self.assertEqual(resp_menu.status_code, 200)

        menus = Menu.objects.all().order_by('order').values('name')
        self.assertDictEqual(
            menus[0], {'name': 'Menu 2'})
        self.assertDictEqual(
            menus[1], {'name': 'Menu 1'})
        self.assertDictEqual(
            menus[2], {'name': 'Menu 3'})

    def test_url_tree_module(self):
        url_tree_module = '/api/menu/module/1/'
        self.assertEqual(self.base_url_detail_tree(pk=1), url_tree_module)

    def test_get__tree_detail_simple_menu(self):
        module1 = Module.objects.create(name="Module 1")

        #menu1 = {'name': 'Menu 1', 'module': module1.pk}
        #self.client.post(self.base_url_list, menu1)

        menu1 = Menu.objects.create(name="Menu 1",
                                    module=module1, parent=None, order=1)

        resp_tree_menu = self.client.get(
            self.base_url_detail_tree(pk=module1.pk))
        self.assertEqual(resp_tree_menu.status_code, 200)
        self.assertEqual(json.loads(resp_tree_menu.content), [{
                         'pk': menu1.pk, 'name': 'Menu 1', 'module': module1.pk,   'order': 1, 'parent': None, 'deep': 0, 'sub_menu': []}])

    def test_get__tree_detail_menu(self):
        module1 = Module.objects.create(name="Module 1")

        menu1 = {'name': 'Menu 1', 'module': module1.pk}
        resp1 = self.client.post(self.base_url_list, menu1)

        menu1_1 = {'name': 'Menu 1.1', 'parent': resp1.data['id']}
        resp_1_1 = self.client.post(self.base_url_list, menu1_1)

        menu1_2 = {'name': 'Menu 1.1.1', 'parent': resp_1_1.data['id']}
        resp_1_1_1 = self.client.post(self.base_url_list, menu1_2)
        menu1_3 = {'name': 'Menu 1.1.2', 'parent': resp_1_1.data['id']}
        resp_1_1_2 = self.client.post(self.base_url_list, menu1_3)

        resp_tree_menu = self.client.get(
            self.base_url_detail_tree(pk=module1.pk))

        self.assertEqual(resp_tree_menu.status_code, 200)

        result_exp = [
            {'pk': 5, 'name': 'Menu 1', 'module': 3, 'order': 1, 'parent': None, 'deep': 0,
             'sub_menu': [
                 {'pk': 6, 'name': 'Menu 1.1', 'module': 3, 'order': 1, 'parent': 5, 'deep': 1,
                  'sub_menu': [
                      {'pk': 7, 'name': 'Menu 1.1.1', 'module': 3,
                       'order': 1, 'parent': 6, 'deep': 2, 'sub_menu': []},
                      {'pk': 8, 'name': 'Menu 1.1.2', 'module': 3,
                          'order': 2, 'parent': 6, 'deep': 2, 'sub_menu': []}
                  ]
                  }
             ]
             }
        ]

        self.assertEqual(json.loads(resp_tree_menu.content), result_exp)
