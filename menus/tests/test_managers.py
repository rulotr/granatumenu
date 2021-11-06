# Standar Library

# Core Django
# Third app
from unittest.mock import patch

import psycopg2
import pytest
from django.core import exceptions
from django.core.exceptions import ValidationError
from django.db import connection, transaction
from django.db.utils import IntegrityError
from django.test import SimpleTestCase, TestCase, skipIfDBFeature
from django_mock_queries.mocks import ModelMocker, mocked_relations
from django_mock_queries.query import MockModel, MockSet

# My app
from menus.models import Module


class TestModuleOperations(TestCase):
    def test_remove_space_fields(self):
        module1 = Module(name="    Module 1    ")
        module1.full_clean()
        self.assertEqual(module1.name, 'Module 1')

    def test_create_module_with_spaces(self):
        module1 = Module.objects.execute_create(name='   Module 1   ')

        self.assertEqual(module1.name, 'Module 1')
        self.assertTrue(Module.objects.count() == 1)

        with self.assertRaisesMessage(ValidationError, "This field cannot be blank."):
            Module.objects.execute_create(name="     ")

    def test_module_name_must_be_unique(self):
        Module.objects.create(name="Module 1")

        with self.assertRaisesMessage(ValidationError, 'The module already exists'):
            Module.objects.execute_create(name="Module 1")

    def test_update_module_name(self):
        module1 = Module.objects.create(name="Module 2")

        with patch.object(Module, 'full_clean') as mock_validate:
            module_update = Module.objects.execute_update(
                module1.id, "Module 1")

            mock_validate.assert_called()
            self.assertEqual(module_update.id, module1.id)
            self.assertEqual(module_update.name, "Module 1")

    def test_delete_module_by_id(self):
        module1 = Module.objects.create(name="Module 1")

        Module.objects.execute_delete(pk=module1.pk)

        self.assertTrue(Module.objects.count() == 0)

    def test_delete_module_not_exist(self):
        with self.assertRaisesMessage(Module.DoesNotExist, "The module with the pk = 1 doesnt exist"):
            Module.objects.execute_delete(pk=1)


class TestModuleQueries(TestCase):
    def test_find_by_pk(self):
        module1 = Module.objects.create(name="Module 1")

        new_module = Module.objects.find_by_pk(pk=module1.pk)

        self.assertEqual(module1, new_module)

    def test_find_by_pk_doesnotexist(self):
        with self.assertRaisesMessage(Module.DoesNotExist, "The module with the pk = 1 doesnt exist"):
            Module.objects.find_by_pk(pk=1)

        # class TestMenuOperations(TestCase):

        #     def test_create_module_without_space(self):
        #         module1 = Menu.objects.create_module(name=" Modulo 1 ")
        #         self.assertEqual(module1.name, 'Modulo 1')
        #         self.assertTrue(Menu.objects.filter(name='Modulo 1').count() == 1)

        #     def test_create_module_empty(self):
        #         with self.assertRaises(ValidationError):
        #             Menu.objects.create_module(name="   ")

        #     def test_create_modules_with_same_name(self):
        #         Menu.objects.create_module(name="Module 1")
        #         with self.assertRaisesMessage(ValidationError, 'This module already exists'):
        #             Menu.objects.create_module(name="Module 1")

        #     def test_update_module_name_whitout_spaces(self):
        #         menu = Menu.objects.create(name="Module")

        #         Menu.objects.update_module(menu.pk, name="  Module 1  ")
        #         self.assertTrue(Menu.objects.filter(name='Module').count() == 0)
        #         self.assertTrue(Menu.objects.filter(name='Module 1').count() == 1)

        #     def test_update_module_with_empty_name(self):
        #         menu = Menu.objects.create(name="Module")
        #         with self.assertRaises(ValidationError):
        #             Menu.objects.update_module(menu.pk, name="   ")

        #     def test_add_node_to_modules(self):
        #         with patch.object(Menu.objects, 'valid_node') as mock_valid_node:
        #             menu = Menu.objects.create(name="Module")

        #             nodo = Menu.objects.create_node(name="Nodo 1", parent=menu.id)
        #             mock_valid_node.assert_called_with(parent=menu.id)
        #             self.assertEqual(nodo.module_id, menu.id)

        #     def test_add_node_with_non_existent_module_constraint(self):
        #         Menu.objects.create(
        #             name="Nodo 1", parent_id=1, module_id=1)
        #         with self.assertRaises(IntegrityError):
        #             connection.check_constraints()

        #     def test_valid_node_not_existent_module(self):
        #         with self.assertRaisesMessage(ValidationError, 'Parent with id 1 not exist'):
        #             Menu.objects.valid_node(parent=1)

        #     def test_valid_node_existent_module(self):
        #         module = Menu.objects.create(name="Module")
        #         valid = Menu.objects.valid_node(parent=module.id)
        #         self.assertTrue(valid)

        #     def test_get_module_node(self):
        #         module1 = Menu.objects.create(name="Module 1")
        #         node1 = Menu.objects.create(
        #             name="Node 1", parent_id=module1.id, module_id=module1.id)

        #         module_owner = Menu.objects.get_module_owner_for(id=node1.id)
        #         module_itself = Menu.objects.get_module_owner_for(id=module1.id)

        #         self.assertEqual(module_owner, module1)

        #         self.assertEqual(module_itself, module1)

        #     def test_add_node_to_father(self):

        #         module = Menu.objects.create(name="Module")
        #         node1 = Menu.objects.create(
        #             name="Node 1", parent_id=module.id, module=module)

        #         sig_id = node1.id + 1
        #         expected_node = Menu(id=sig_id, name="Nodo 1.1",
        #                              parent=node1, module_id=module)

        #         node2 = Menu.objects.create_node(name="Nodo 1.1", parent=node1.id)
        #         self.assertEqual(node2, expected_node)
        # #@mocked_relations(Menu)
        # class TestMenuManager(SimpleTestCase):
        #     mens = MockSet()
        #     menu_objects = patch('menus.models.Menu.objects',mens)

        #     @menu_objects
        #     @patch('menus.models.MenuManager.buscar_por_nombre')
        #     def test_manager(self, buscar_por_nombre):

        #         res =Menu.objects.buscar_por_nombre("a")
        #         self.assertEqual(res,1)

        #     def test_module_filter(self):
        #         expected_result =[Menu(name = "Module1",)]

        #         qs_mock = MockSet(Menu(name = "Module1",),Menu(name = "Module2",),Menu(name = "Module3",))

        #         with patch.object(Menu.objects, 'get_queryset', return_value=qs_mock):
        #             resultado = Menu.objects.buscar_por_nombre("Module1")
        #             #import ipdb;ipdb.set_trace()
        #             self.assertEqual(resultado.count(), 1)

        # @menu_objects
        # #@patch.object(Menu,'save')
        # def test_module_creation(self):
        #     expected_result =Menu(name = "Module1",)
        #     qs_mock = MockSet(expected_result)

        #     #mock_save.return_value =qs_mock
        #     #with patch.object(Menu, 'save', return_value=qs_mock):

        #     #mod1 = Menu.objects.create(name="Module 1")
        #     mod1 = Menu.operaciones.create_module()

        # self.assertEqual(mod1.name, expected_result.name)
        # self.assertEqual(Menu.objects.count(), 1 )
