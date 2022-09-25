

from abc import ABC, abstractmethod

from django.db import models

from menus.consts import ErrorMessage
from menus.models.custom_fields import CharFieldTrim
from menus.models.custom_managers import GenericManager


class GenericOperationsABC(ABC):
    @abstractmethod
    def execute_create(self, name, module, parent):
        pass

    @abstractmethod
    def execute_retrieve(self, *args, **kwargs):
        pass

    @abstractmethod
    def execute_update(self, pk, name):
        pass

    @abstractmethod
    def execute_partial_update(self, pk, order):
        pass

    @abstractmethod
    def execute_delete(self, pk):
        pass


class ModuleManager(GenericOperationsABC, GenericManager):
    def get_all(self):
        return self.model.objects.all()

    def execute_create(self, name):
        module = self.model(name=name)
        module.full_clean()
        module.save()
        return module

    def execute_retrieve(self, *args, **kwargs):
        pass

    def execute_update(self, pk, name):
        module = self.find_by_pk(pk)
        module.name = name
        module.full_clean()
        module.save(update_fields=['name'])
        return module

    def execute_partial_update(self, pk, order):
        pass

    def execute_delete(self, pk):
        module = self.find_by_pk(pk)
        module.delete()


class Module(models.Model):
    name = CharFieldTrim(
        max_length=15, error_messages=ErrorMessage.UNIQUE_ERROR, blank=False, unique=True)

    objects = ModuleManager()
