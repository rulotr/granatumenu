# Standar Library

# Core Django
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.functions import Lower
from django.db.models.query import QuerySet

# Third app

# My app

# Create your models here.

errors = {'unique': 'The module already exists'}
ERROR_PK_NOT_EXIST = "The module with the pk = {} doesnt exist"


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
            raise self.model.DoesNotExist(
                ERROR_PK_NOT_EXIST.format(pk)) from ex


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
        max_length=15, error_messages=errors, blank=False, unique=True)

    def clean(self):
        self.name = self.name.capitalize()

    objects = ModuleManager()
