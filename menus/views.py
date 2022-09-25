from ipaddress import ip_address
from os import stat
from socket import IP_ADD_MEMBERSHIP
from urllib import request
from xml.dom import ValidationErr

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import IntegrityError
from django.shortcuts import render
from rest_framework import serializers, status
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import (
    CreateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView
from yaml import serialize

from menus.models import Menu, Module
from menus.serializers import MenuSerializer, MenuTreeSerializer, ModuleSerializer

# Create your views here.


class RetrieveModelMixinCustom(RetrieveModelMixin):
    def retrieve(self, request, *args, **kwargs):
        instance = self.model_operations.objects.execute_retrieve(
            *args, **kwargs)
        serializer = self.get_serializer(instance, many=True)
        return Response(serializer.data)


class CreateModelMixinCustom(CreateModelMixin):
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer = self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        new_module = self.model_operations.objects.execute_create(
            **serializer.validated_data)
        serializer = self.get_serializer(new_module)
        return serializer


class UpdateModelMixinCustom(UpdateModelMixin):
    def perform_update(self, pk, serializer):
        list_method_update = {
            'PUT': self.model_operations.objects.execute_update,
            'PATCH': self.model_operations.objects.execute_partial_update
        }

        method_update = list_method_update[self.request.method]

        update_module = method_update(pk=pk, **serializer.validated_data)
        serializer = self.get_serializer(update_module)
        return serializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)

        assert 'pk' in kwargs, (
            'Expected view %s to be called with a URL keyword argument '
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            'attribute on the view correctly.' %
            (self.__class__.__name__, 'pk')
        )

        pk = kwargs['pk']
        serializer = self.get_serializer(data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer = self.perform_update(pk, serializer)

        return Response(serializer.data)


class DestroyModelMixinCustom(DestroyModelMixin):
    def destroy(self, request, *args, **kwargs):
        assert 'pk' in kwargs, (
            'Expected view %s to be called with a URL keyword argument '
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            'attribute on the view correctly.' %
            (self.__class__.__name__, 'pk')
        )

        pk = kwargs['pk']

        try:
            self.perform_destroy(pk)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ObjectDoesNotExist as e:
            return Response({'message': e.args[0]}, status=status.HTTP_404_NOT_FOUND)

    def perform_destroy(self, pk):
        self.model_operations.objects.execute_delete(pk)


class ModuleListApi(CreateModelMixinCustom, ListModelMixin, GenericAPIView):
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer
    model_operations = Module

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class ModuleDetailApi(RetrieveModelMixin, UpdateModelMixinCustom, DestroyModelMixinCustom, GenericAPIView):
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer
    model_operations = Module

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class MenuListApi(CreateModelMixinCustom, GenericAPIView):
    queryset = Menu.objects.all()
    serializer_class = MenuSerializer
    model_operations = Menu

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class MenuDetailApi(RetrieveModelMixinCustom, UpdateModelMixinCustom, GenericAPIView):
    queryset = Menu.objects.all()
    serializer_class = MenuSerializer
    serializer_classes = {
        'GET': MenuTreeSerializer
    }
    model_operations = Menu

    def get_serializer_class(self):
        return self.serializer_classes.get(self.request.method, self.serializer_class)

    def get(self, request,  *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)
