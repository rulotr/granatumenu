# Standar Library

# Core Django
# Third app
import unittest
from ipaddress import ip_address
from unittest.mock import patch

import factory
import psycopg2
import pytest
from django.core import exceptions
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction
from django.test import SimpleTestCase, TestCase, skipIfDBFeature
from django_mock_queries.mocks import ModelMocker, mocked_relations
from django_mock_queries.query import MockModel, MockSet

# My app
from menus.models import Menu, Module


class ModuleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Module
    name = factory.Sequence(lambda n: 'Module {}'.format(n+1))


class MenuFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Menu

    name = factory.Sequence(lambda n: 'Menu {}'.format(n+1))
    module = None  # factory.SubFactory(ModuleFactory)
    # factory.SubFactory('menus.tests.test_managers.MenuFactory')
    parent = None
    order = factory.Sequence(lambda n: n+1)

    @classmethod
    def _adjust_kwargs(cls, **kwargs):
        if kwargs['parent']:
            kwargs['module'] = kwargs['parent'].module
        return kwargs


class TestModuleOperations(TestCase):
    def test_get_all_modules(self):
        Module.objects.create(name="Module 1")
        Module.objects.create(name="Module 2")

        modules = Module.objects.get_all()
        self.assertEqual(modules.count(), 2)

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

    def test_module_name_must_be_unique_full_clean(self):
        Module.objects.create(name="Module 1")

        with self.assertRaises(ValidationError):
            module = Module(name="Module 1")
            module.full_clean()

    def test_module_name_must_be_unique_not_full_clean(self):
        Module.objects.create(name="Module 1")

        with self.assertRaises(IntegrityError):
            module = Module(name="Module 1")
            module.save()

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

    def test_find_by_pk_not_exist(self):
        with self.assertRaisesMessage(Module.DoesNotExist, "The module with the pk = 1 doesnt exist"):
            Module.objects.find_by_pk(pk=1)


class TestMenuOperations(TestCase):

    def test_create_menu(self):
        module1 = Module.objects.create(name="Module 1")
        menu1 = Menu.objects.execute_create(
            name='  Menu 1  ', module=module1)

        self.assertEqual(menu1.name, 'Menu 1')
        self.assertEqual(menu1.module, module1)

        self.assertTrue(Menu.objects.count() == 1)

    def test_create_child_node(self):
        module1 = ModuleFactory()
        module2 = ModuleFactory()
        menu1 = MenuFactory(module=module1, order=1)

        child_menu = Menu.objects.execute_create(
            name='Child 1', module=module2, parent=menu1)

        self.assertEqual(child_menu.parent, menu1)
        self.assertEqual(child_menu.module, module1)

    def test_create_menu_with_not_module(self):
        with self.assertRaisesMessage(ValidationError, "{'module': ['This field cannot be null.']}"):
            Menu.objects.execute_create(name='Menu 1')

    def test_create_menu_same_name(self):
        module1 = ModuleFactory()
        module2 = ModuleFactory()

        menu1 = Menu.objects.execute_create(
            name='  Menu 1  ', module=module1)
        menu2 = Menu.objects.execute_create(
            name='  Menu 1  ', module=module2)

        self.assertEqual(menu1.name, 'Menu 1')
        self.assertEqual(menu2.name, 'Menu 1')

        self.assertTrue(Menu.objects.count() == 2)

    def test_create_two_main_menu_same_module(self):
        module1 = ModuleFactory()

        Menu.objects.execute_create(name='Menu 1', module=module1)

        with self.assertRaisesMessage(ValidationError, "Can only exist one main menu for module"):
            Menu.objects.execute_create(name='Menu 2', module=module1)

    # @unittest.skip('Probar primero la busqueda por id')
    def test_update_menu_name(self):
        module1 = ModuleFactory()
        menu1 = MenuFactory(module=module1, order=1)

        menu1_update = Menu.objects.execute_update(menu1.id, "My menu 1")

        self.assertEqual(menu1_update.id, menu1.id)
        self.assertEqual(menu1_update.name, "My menu 1")

    @unittest.skip('Este debe de ser un test de integracion')
    def test_create_menu_with_order_same_module(self):
        module1 = Module.objects.create(name="Module 1")

        menu1 = Menu.objects.execute_create(
            name='  Menu 1  ', module=module1)
        menu1_1 = Menu.objects.execute_create(
            name='  Menu 1.1  ', parent=menu1)
        menu1_2 = Menu.objects.execute_create(
            name='  Menu 1.2  ', parent=menu1)

        self.assertEqual(menu1.order, 1)
        self.assertEqual(menu1_1.order, 1)
        self.assertEqual(menu1_2.order, 2)

    @unittest.skip('Este debe de ser un test de integracion')
    def test_create_menu_with_order_different_module(self):
        module1 = Module.objects.create(name="Module 1")
        module2 = Module.objects.create(name="Module 2")

        menu1_1 = Menu.objects.execute_create(
            name='  Menu 1  ', module=module1)
        menu2_1 = Menu.objects.execute_create(
            name='  Menu 2  ', module=module2)

        self.assertEqual(menu1_1.order, 1)
        self.assertEqual(menu2_1.order, 1)

    def test_get_num_order_next_menu(self):
        module1 = ModuleFactory()
        menu1 = MenuFactory(module=module1, order=1)
        menu1_1 = MenuFactory(parent=menu1, order=1)
        menu1_2 = MenuFactory(parent=menu1, order=2)
        module2 = ModuleFactory()
        menu2 = MenuFactory(module=module2, order=1)
        module3 = ModuleFactory()

        order_menu_1_3 = Menu.objects.next_order_num(parent=menu1)
        order_menu_1_2_1 = Menu.objects.next_order_num(parent=menu1_2)
        order_menu_2_1 = Menu.objects.next_order_num(parent=menu2)
        order_menu_2_2 = Menu.objects.next_order_num(module=module2)
        order_menu_3 = Menu.objects.next_order_num(module=module3)

        self.assertEqual(order_menu_1_3, 3)
        self.assertEqual(order_menu_1_2_1, 1)
        self.assertEqual(order_menu_2_1, 1)
        self.assertEqual(order_menu_2_2, 2)
        self.assertEqual(order_menu_3, 1)

    def get_menus_by_order(self, module):
        return Menu.objects.filter(
            module=module).order_by('order').values_list('id', 'name', 'order')

    def test_change_order_menu_last_to_first(self):
        module1 = ModuleFactory()
        MenuFactory.reset_sequence(0)
        MenuFactory.create_batch(5, module=module1, parent=None)

        menus_order = self.get_menus_by_order(module=module1)
        self.assertQuerysetEqual(
            menus_order,
            [(1, 'Menu 1', 1), (2, 'Menu 2', 2), (3, 'Menu 3', 3), (4, 'Menu 4', 4), (5, 'Menu 5', 5)]
            )

        #menu1_1 = MenuFactory(module=module1, order=1)
        #menu1_2 = MenuFactory(module=module1, order=2)
        #menu1_3 = MenuFactory(module=module1, order=3)
        #menu1_4 = MenuFactory(module=module1, order=4)
        #menu1_5 = MenuFactory(module=module1, order=5)

        ''' menus_order = self.get_menus_by_order(module=module1)
        self.assertQuerysetEqual(
            menus_order, [('Menu 1', 1), ('Menu 2', 2), ('Menu 3', 3), ('Menu 4', 4), ('Menu 5', 5)])

        Menu.objects.change_order_to(menu1_5, 1)
        menus_order = self.get_menus_by_order(module=module1)

        self.assertQuerysetEqual(
            menus_order, [('Menu 5', 1), ('Menu 1', 2), ('Menu 2', 3), ('Menu 3', 4), ('Menu 4', 5)])

        Menu.objects.change_order_to(menu1_5, 5)
        menus_order = self.get_menus_by_order(module=module1)
        self.assertQuerysetEqual(
            menus_order, [('Menu 1', 1), ('Menu 2', 2), ('Menu 3', 3), ('Menu 4', 4), ('Menu 5', 5)])
 '''


class TestMenuQueries(TestCase):

    def test_find_by_pk(self):
        module1 = Module.objects.create(name="Module 2")
        menu1 = Menu.objects.create(name="Menu 1", module=module1)
        new_menu = Menu.objects.find_by_pk(pk=menu1.pk)

        self.assertEqual(new_menu.name, 'Menu 1')

    def test_find_by_pk_not_exist(self):
        with self.assertRaisesMessage(Menu.DoesNotExist, "The menu with the pk = 1 doesnt exist"):
            Menu.objects.find_by_pk(pk=1)

    # # @patch('django.db.models.query.QuerySet')
    # def test_find_by_pk2(self):
    #     module1 = Module.objects.create(name="Module 1")

    #     qs_mock = MockSet2(Module(pk=1, name="Module1",), Module(
    #         name="Module2",), Module(name="Module3",))

    #     with patch.object(Module.objects, 'get_queryset', return_value=qs_mock):
    #         new_module = Module.objects.find_by_pk(pk=1)
    #         self.assertEqual(qs_mock, new_module)

    # def test_find_by_pk_doesnotexist(self):
    #    with self.assertRaisesMessage(Module.DoesNotExist, "The module with the pk = 1 doesnt exist"):
    #        Module.objects.find_by_pk(pk=1)

        #     def test_module_filter(self):
        #         expected_result =[Menu(name = "Module1",)]

        #         qs_mock = MockSet(Menu(name = "Module1",),Menu(name = "Module2",),Menu(name = "Module3",))

        #         with patch.object(Menu.objects, 'get_queryset', return_value=qs_mock):
        #             resultado = Menu.objects.buscar_por_nombre("Module1")
        #             #import ipdb;ipdb.set_trace()
        #             self.assertEqual(resultado.count(), 1)

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
