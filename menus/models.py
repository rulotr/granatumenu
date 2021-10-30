# Standar Library

# Core Django
from django.core.exceptions import ValidationError
from django.db import models

# Third app

# My app

# Create your models here.


class TrimCharField(models.CharField):
    description = 'CharField using trim'

    # to_python es llamado en la funcion de validacion clean
    def to_python(self, value):
        value = super().to_python(value)
        return value.strip()


class ModuleManager(models.Manager):

    def execute_create(self, name):
        module = self.model(name=name)
        module.clean_and_validate()
        module.save()
        return module

    def execute_update(self, pk, name):
        module = self.get(pk=pk)
        module.name = name
        module.clean_and_validate()
        module.save(update_fields=['name'])
        return module


errors = {'unique': 'The module already exists'}


class Module(models.Model):
    name = TrimCharField(
        max_length=15, error_messages=errors, blank=False)

    objects = ModuleManager()

    class Meta:
        constraints = [models.UniqueConstraint(
            fields=['name'], name='unique_module', )]

    def clean_and_validate(self):
        # self.name = self.name.strip()
        self.full_clean()

    # class MenuManager(models.Manager):

    #     def create_module(self, name):
    #         module = self.model(name=name.strip(), module=None)
    #         module.full_clean()
    #         module.save()
    #         return module

    #     def update_module(self, id, name):
    #         module = self.get(pk=id)
    #         module.name = name.strip()
    #         module.full_clean()
    #         module.save(update_fields=['name'])
    #         return module

    #     def create_node(self, name, parent):
    #         self.valid_node(parent=parent)
    #         module = self.get_module_owner_for(id=parent)
    #         node = self.model(name=name.strip(), parent_id=parent, module=module)
    #         node.full_clean()
    #         node.save()
    #         return node

    #     def valid_node(self, parent):
    #         node_owner = self.filter(id=parent)
    #         if not node_owner.exists():
    #             msg_error = f'Parent with id {parent} not exist'
    #             raise ValidationError(msg_error)
    #         return True

    #     def get_module_owner_for(self, id):
    #         node = Menu.objects.get(id=id)
    #         if(node.parent is None and node.module is None):
    #             return node

    #         module_owner = Menu.objects.get(
    #             id=node.module_id, parent=None, module=None)
    #         return module_owner

    # class Menu(models.Model):
    #     name = models.CharField(max_length=15, error_messages={
    #                             'unique': 'This module already exists'})
    #     module = models.ForeignKey(
    #         'self', null=True, blank=True, default=None, on_delete=models.PROTECT,
    #         related_name='+')

    #     parent = models.ForeignKey(
    #         'self', null=True, blank=True, default=None, on_delete=models.PROTECT,
    #         related_name='+',)

    #     objects = MenuManager()

    #     class Meta:
    #         constraints = [models.UniqueConstraint(
    #             fields=['name'], name='unique_module', )]
