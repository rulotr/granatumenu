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
from menus.models.menus import TreeMenu


class ModuleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Module
    name = factory.Sequence(lambda n: 'Module {}'.format(n+1))


class MenuFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Menu
    pk = factory.Sequence(lambda n: n+1)
    name = factory.Sequence(lambda n: 'Menu {}'.format(n+1))
    module = factory.LazyAttribute(lambda x: ModuleFactory())
    parent = None  # factory.LazyAttribute(lambda x: MenuFactory(parent=None))
    order = factory.Sequence(lambda n: n+1)

    @classmethod
    def _adjust_kwargs(cls, **kwargs):
        if kwargs['parent']:
            kwargs['module'] = kwargs['parent'].module
        return kwargs


class TestModuleOperations(TestCase):
    def test_get_all_modules(self):
        ModuleFactory.reset_sequence(0)
        ModuleFactory.create_batch(2)

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
            module = Module(name="MODULE 1")
            module.full_clean()

    def test_module_name_must_be_unique_not_full_clean(self):
        Module.objects.create(name="Module 1")

        with self.assertRaises(IntegrityError):
            module = Module(name="MODULE 1")
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

    # @patch('menus.models.Menu.objects.next_order_num', return_value=3)
    @patch.object(Menu.objects, 'next_order_num')
    def test_create_menu(self, mock_next_order_num):
        module1 = Module.objects.create(name="Module 1")

        #mock_next_order_num.return_value = 2
        menu1 = Menu.objects.execute_create(
            name='  Menu 1  ', module=module1)

        mock_next_order_num.assert_called()
        self.assertEqual(menu1.name, 'Menu 1')
        self.assertEqual(menu1.module, module1)
        #self.assertEqual(menu1.order, 3)

        self.assertTrue(Menu.objects.count() == 1)

    @patch.object(Menu.objects, 'next_order_num')
    def test_create_two_menu_wit_parent_none(self, mock_next_order_num):
        module1 = Module.objects.create(name="Module 1")
        MenuFactory(module=module1, order=1, parent=None)

        Menu.objects.execute_create(
            name='  Menu 2  ', module=module1)
        mock_next_order_num.assert_called()
        num_menu_not_parent = Menu.objects.filter(
            module=module1, parent=None).count()
        self.assertEqual(num_menu_not_parent, 2)

    @patch.object(Menu.objects, 'next_order_num', return_value=2)
    def test_create_child_node(self, mock_next_order_num):
        module1 = ModuleFactory()
        module2 = ModuleFactory()
        menu1 = MenuFactory(module=module1, order=1)

        child_menu = Menu.objects.execute_create(
            name='Child 1', module=module2, parent=menu1)

        mock_next_order_num.assert_called()
        self.assertEqual(child_menu.parent, menu1)
        self.assertEqual(child_menu.module, module1)
        self.assertEqual(child_menu.order, 2)

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

    # @unittest.skip('Probar primero la busqueda por id')
    def test_update_menu_name(self):
        module1 = ModuleFactory()
        menu1 = MenuFactory(module=module1, order=1)

        menu1_update = Menu.objects.execute_update(menu1.id, "My menu 1")

        self.assertEqual(menu1_update.id, menu1.id)
        self.assertEqual(menu1_update.name, "My menu 1")

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
            module=module).order_by('order').values_list('id', 'order')

    def test_change_order_menu_last_to_first(self):
        module1 = ModuleFactory()
        MenuFactory.reset_sequence(0)
        MenuFactory.create_batch(5, module=module1, parent=None)

        menus_order = self.get_menus_by_order(module=module1)
        self.assertQuerysetEqual(
            menus_order, [(1, 1), (2, 2), (3, 3), (4, 4), (5,  5)]
        )
        Menu.objects.change_order_to(pk=5, new_order=1)
        menus_order = self.get_menus_by_order(module=module1)
        self.assertQuerysetEqual(
            menus_order, [(5,  1), (1, 2), (2, 3), (3, 4), (4, 5), ]
        )

    def test_change_order_menu_first_to_last(self):
        module1 = ModuleFactory()
        MenuFactory.reset_sequence(0)
        MenuFactory.create_batch(5, module=module1, parent=None)

        menus_order = self.get_menus_by_order(module=module1)
        self.assertQuerysetEqual(
            menus_order, [(1, 1), (2, 2), (3, 3), (4, 4), (5,  5)]
        )
        Menu.objects.change_order_to(pk=1, new_order=5)
        menus_order = self.get_menus_by_order(module=module1)
        self.assertQuerysetEqual(
            menus_order, [(2, 1), (3, 2), (4, 3), (5,  4), (1, 5)]
        )

    def test_change_order_menu_intermediate(self):
        module1 = ModuleFactory()
        MenuFactory.reset_sequence(0)
        MenuFactory.create_batch(5, module=module1, parent=None)

        menus_order = self.get_menus_by_order(module=module1)
        self.assertQuerysetEqual(
            menus_order, [(1, 1), (2, 2), (3, 3), (4, 4), (5,  5)]
        )
        Menu.objects.change_order_to(pk=2, new_order=4)
        menus_order = self.get_menus_by_order(module=module1)
        self.assertQuerysetEqual(
            menus_order, [(1, 1), (3, 2), (4, 3), (2, 4), (5,  5)]
        )

        Menu.objects.change_order_to(pk=2, new_order=2)
        menus_order = self.get_menus_by_order(module=module1)
        self.assertQuerysetEqual(
            menus_order, [(1, 1), (2, 2), (3, 3), (4, 4), (5,  5)]
        )

        Menu.objects.change_order_to(pk=3, new_order=4)
        menus_order = self.get_menus_by_order(module=module1)
        self.assertQuerysetEqual(
            menus_order, [(1, 1), (2, 2), (4, 3), (3, 4), (5,  5)]
        )

    def test_change_order_menu_dont_change_other_modules(self):
        module1 = ModuleFactory()
        module2 = ModuleFactory()
        MenuFactory.reset_sequence(0)
        MenuFactory.create_batch(2, module=module1, parent=None)
        Menu.objects.create(id=3, name="Menu module 2",
                            module=module2, parent=None, order=1)

        Menu.objects.change_order_to(pk=1, new_order=2)
        menus_order_module2 = self.get_menus_by_order(module=module2)
        self.assertQuerysetEqual(
            menus_order_module2, [(3, 1)]
        )

    @patch.object(Menu.objects, 'change_order_to')
    def test__execute_partial_update_called_change_order_to(self, mock_change_order_to):
        Menu.objects.execute_partial_update(
            pk=1, order=1)
        mock_change_order_to.assert_called()


class TestMenuQueries(TestCase):

    def test_find_by_pk(self):
        module1 = Module.objects.create(name="Module 2")
        menu1 = Menu.objects.create(name="Menu 1", module=module1)
        new_menu = Menu.objects.find_by_pk(pk=menu1.pk)

        self.assertEqual(new_menu.name, 'Menu 1')

    def test_find_by_pk_not_exist(self):
        with self.assertRaisesMessage(Menu.DoesNotExist, "The menu with the pk = 1 doesnt exist"):
            Menu.objects.find_by_pk(pk=1)

    def test_get_tree_menu_for_module_one_level(self):
        module1 = ModuleFactory()
        module2 = ModuleFactory()
        MenuFactory.reset_sequence(0)
        MenuFactory.create_batch(5, module=module1, parent=None)
        MenuFactory.create_batch(2, module=module2, parent=None)

        tree_menu = Menu.objects.get_tree_by_module(module=module1.pk)
        tree1, tree2, tree3, tree4, tree5 = tree_menu

        module_id = module1.pk
        self.assertEqual(len(tree_menu), 5)
        self.assertEqual(tree1, TreeMenu(
            pk=1, module=module_id, name='Menu 1', order=1, parent=None, sub_menu=[]))
        self.assertEqual(tree2, TreeMenu(
            pk=2, module=module_id, name='Menu 2', order=2, parent=None, sub_menu=[]))
        self.assertEqual(tree3, TreeMenu(
            pk=3, module=module_id, name='Menu 3', order=3, parent=None, sub_menu=[]))
        self.assertEqual(tree4, TreeMenu(
            pk=4, module=module_id, name='Menu 4', order=4, parent=None, sub_menu=[]))
        self.assertEqual(tree5, TreeMenu(
            pk=5, module=module_id, name='Menu 5', order=5, parent=None, sub_menu=[]))

    def test_get_tree_menu_for_module_with_submenu(self):
        module1 = ModuleFactory()
        MenuFactory.reset_sequence(0)
        menu1 = MenuFactory(module=module1, order=2)
        menu2 = MenuFactory(module=module1, order=1)

        menu1_1 = MenuFactory(parent=menu1, order=1)
        menu1_2 = MenuFactory(parent=menu1, order=2)
        menu2_1 = MenuFactory(parent=menu2, order=1)

        menu1_1_1 = MenuFactory(parent=menu1_1, order=1)
        tree_menu = Menu.objects.get_tree_by_module(module=module1.pk)

        tree1, tree2 = tree_menu
        tree1_1 = tree1.sub_menu[0]

        tree2_1, tree2_2 = tree2.sub_menu
        tree2_1_1 = tree2_1.sub_menu[0]

        self.assertEqual(len(tree_menu), 2)
        self.assertEqual(len(tree1.sub_menu), 1)
        self.assertEqual(len(tree1_1.sub_menu), 0)
        self.assertEqual(len(tree2.sub_menu), 2)
        self.assertEqual(len(tree2_1.sub_menu), 1)
        self.assertEqual(len(tree2_1_1.sub_menu), 0)
        self.assertEqual(len(tree2_2.sub_menu), 0)

        self.assertEqual(tree1.path(), menu2.name)
        self.assertEqual(tree1_1.path(), f'|---{menu2_1.name}')
        self.assertEqual(tree2.path(), menu1.name)
        self.assertEqual(tree2_1.path(), f'|---{menu1_1.name}')
        self.assertEqual(tree2_1_1.path(), f'|---|---{menu1_1_1.name}')
        self.assertEqual(tree2_2.path(), f'|---{menu1_2.name}')
