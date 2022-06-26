# Standar Library

# Core Django
from ast import Mod
from ipaddress import ip_address
from turtle import position

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Max
from django.db.models.functions import Coalesce, Lower
from django.db.models.query import QuerySet

# Third app

# My app

# Create your models here.

errors = {'unique': 'The module already exists'}
ERROR_PK_NOT_EXIST = "The {} with the pk = {} doesnt exist"


class CharFieldTrim(models.CharField):
    # Una vez que se establece el tipo del que hereda no se podra cambiar

    description = 'CharField using trim'

    # to_python es llamado en la funcion de validacion clean
    def to_python(self, value):
        value = super().to_python(value)
        return value.strip()


class GenericManager(models.Manager):

    def find_by_pk(self, pk):
        try:
            return self.get(pk=pk)
        except self.model.DoesNotExist as ex:
            name_model = self.model._meta.model_name
            raise self.model.DoesNotExist(
                ERROR_PK_NOT_EXIST.format(name_model, pk)) from ex


class ModuleManager(GenericManager):
    def get_all(self):
        return self.model.objects.all()

    def execute_create(self, name):
        module = self.model(name=name)
        module.full_clean()
        module.save()
        return module

    def execute_update(self, pk, name):
        module = self.find_by_pk(pk)
        module.name = name
        module.full_clean()
        module.save(update_fields=['name'])
        return module

    def execute_delete(self, pk):
        module = self.find_by_pk(pk)
        module.delete()


class MenuManager(GenericManager):
    def execute_create(self, name, module=None, parent=None):
        if parent is None and self.filter(module=module, parent=None).count() > 0:
            raise ValidationError('Can only exist one main menu for module')

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

    def next_order_num(self, module=None, parent=None):
        if parent:
            module = parent.module
        order = self.filter(module=module, parent=parent).aggregate(
            num=Coalesce(Max('order'), 0))['num']
        return order + 1


class Module(models.Model):
    name = CharFieldTrim(
        max_length=15, error_messages=errors, blank=False, unique=True)

    def clean(self):
        self.name = self.name.capitalize()

    objects = ModuleManager()


class Menu(models.Model):
    name = CharFieldTrim(
        max_length=15, error_messages=errors, blank=False)
    module = models.ForeignKey(Module, on_delete=models.PROTECT)
    parent = models.ForeignKey(
        'self', null=True, default=None, blank=True, on_delete=models.PROTECT)
    order = models.PositiveSmallIntegerField(default=0)

    objects = MenuManager()
