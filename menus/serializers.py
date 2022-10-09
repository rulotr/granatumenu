from django.db import models
from rest_framework import serializers

from menus.models import Menu, Module


class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = ('id', 'name')


class MenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = Menu
        fields = ('id', 'name', 'module', 'parent', 'order',)
        extra_kwargs = {"module": {"required": False, "allow_null": True}}


class ItemTreeSerializer(serializers.Serializer):
    pk = serializers.IntegerField()
    name = serializers.CharField()
    module = serializers.IntegerField()
    order = serializers.IntegerField()
    parent = serializers.IntegerField()
    deep = serializers.IntegerField()
    sub_menu = serializers.SerializerMethodField()

    def get_sub_menu(self, obj):
        if obj.sub_menu is not None:
            return ItemTreeSerializer(obj.sub_menu, many=True).data
        else:
            return None


class MenuTreeSerializer(serializers.Serializer):
    module = serializers.IntegerField()
    menus = ItemTreeSerializer(many=True)
