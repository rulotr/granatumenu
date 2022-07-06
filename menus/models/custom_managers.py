
from django.db import models

from menus.consts import ErrorMessage


class GenericManager(models.Manager):

    def find_by_pk(self, pk):
        try:
            return self.get(pk=pk)
        except self.model.DoesNotExist as ex:
            name_model = self.model._meta.model_name
            raise self.model.DoesNotExist(
                ErrorMessage.PK_NOT_EXIST.format(name_model, pk)) from ex
