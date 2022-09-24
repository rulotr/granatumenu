from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

from django.db import models
from django.db.models import F, Max
from django.db.models.functions import Coalesce

from menus.consts import ErrorMessage
from menus.models import Module
from menus.models.custom_fields import CharFieldTrim
from menus.models.custom_managers import GenericManager


class GenericOperationsABC(ABC):
    @abstractmethod
    def execute_create(self, name, module, parent):
        pass


class MenuManager(GenericOperationsABC, GenericManager):
    def execute_create(self, name, module=None, parent=None):
        if parent:
            module = parent.module

        order = self.next_order_num(module=module, parent=parent)

        menu = self.model(name=name, module=module, parent=parent, order=order)
        menu.full_clean()
        menu.save()
        return menu

    def execute_update(self, pk, name):
        menu = self.find_by_pk(pk)
        menu.name = name
        menu.full_clean()
        menu.save(update_fields=['name'])
        return menu

    def execute_partial_update(self, pk, order):
        self.change_order_to(pk=pk, new_order=order)

    def next_order_num(self, module=None, parent=None):
        if parent:
            module = parent.module
        order = self.filter(module=module, parent=parent).aggregate(
            num=Coalesce(Max('order'), 0))['num']
        return order + 1

    def change_order_to(self, pk, new_order):
        menu = self.find_by_pk(pk)
        sort_order = sorted([menu.order, new_order])
        add_order = -1 if menu.order < new_order else 1

        self.filter(module=menu.module, parent=menu.parent,
                    order__gte=sort_order[0], order__lte=sort_order[1]
                    ).update(order=F('order')+add_order)
        self.filter(pk=menu.id).update(order=new_order)

    def get_tree_by_module(self, module):
        nodes_menu = self.filter(module__id=module)

        nodes_menu = sorted(nodes_menu, key=lambda x: x.order)

        tree_menu = self.build_tree_menu(nodes_menu, None, 0)

        return tree_menu

    def build_tree_menu(self, nodes_menu, id_parent, deep):

        tree_menu = [TreeMenu(module=node.module.id,
                              pk=node.id,
                              name=node.name,
                              order=node.order,
                              parent=node.parent_id,
                              deep=deep,
                              sub_menu=self.build_tree_menu(nodes_menu, node.id, deep+1))
                     for node in nodes_menu if node.parent_id == id_parent]

        return tree_menu


@dataclass
class TreeMenu:
    pk: int
    module: int
    name: str
    order: int
    parent: int
    sub_menu: List['TreeMenu']
    deep: int = 0

    def path(self):
        return '|---' * self.deep + self.name


class Menu(models.Model):
    name = CharFieldTrim(
        max_length=15, error_messages=ErrorMessage.UNIQUE_ERROR, blank=False)
    module = models.ForeignKey(Module, on_delete=models.PROTECT)
    parent = models.ForeignKey(
        'self', null=True, default=None, blank=True, on_delete=models.PROTECT)
    order = models.PositiveSmallIntegerField(default=0)

    objects = MenuManager()
