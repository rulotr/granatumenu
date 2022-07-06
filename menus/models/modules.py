

from django.db import models

from menus.consts import ErrorMessage
from menus.models.custom_fields import CharFieldTrim
from menus.models.custom_managers import GenericManager


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


class Module(models.Model):
    name = CharFieldTrim(
        max_length=15, error_messages=ErrorMessage.UNIQUE_ERROR, blank=False, unique=True)

    # def clean(self):
    #    self.name = self.name.capitalize()

    objects = ModuleManager()
