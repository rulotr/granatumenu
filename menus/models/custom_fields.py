from django.db import models


class CharFieldTrim(models.CharField):
    # Una vez que se establece el tipo del que hereda no se podra cambiar

    description = 'CharField using trim'

    # to_python es llamado en la funcion de validacion clean
    def to_python(self, value):
        value = super().to_python(value)
        return value.strip().capitalize()
