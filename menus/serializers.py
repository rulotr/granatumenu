from django.db import models
from rest_framework import serializers

from menus.models import Module


class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = ('id', 'name')
