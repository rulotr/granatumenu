from ipaddress import ip_address
from os import stat
from socket import IP_ADD_MEMBERSHIP
from urllib import request
from xml.dom import ValidationErr

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import IntegrityError
from django.db.models.deletion import ProtectedError
from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
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
from menus.serializers import (
    ItemTreeSerializer,
    MenuSerializer,
    MenuTreeSerializer,
    ModuleSerializer,
)

# Create your views here.


class ListModelMixinCustom:
    """
    List a queryset.
    """

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        result_list = self.perform_list(queryset)

        serializer = self.get_serializer(result_list, many=True)

        return Response(serializer.data)

    def perform_list(self, queryset):
        return queryset


# Arreglar este para que sea generico


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

    # def get_serializer_class(self):
    #     import ipdb
    #     ipdb.set_trace()
    #     serializer = self.dict_serializer_classes.get(
    #         self.request.method, self.serializer_class)

    #     return serializer


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
        except ProtectedError as e:
            return Response({'message': e.args[0]}, status=status.HTTP_400_BAD_REQUEST)

    def perform_destroy(self, pk):
        self.model_operations.objects.execute_delete(pk)


class ModuleListApi(CreateModelMixinCustom, ListModelMixinCustom, GenericAPIView):
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


class MenuListApi(CreateModelMixinCustom, ListModelMixinCustom, GenericAPIView):
    queryset = Menu.objects.all()
    #serializer_class = MenuSerializer
    model_operations = Menu

    dict_serializer_classes = {
        'GET': MenuTreeSerializer,
        'POST': MenuSerializer
    }
    #filter_backends = [DjangoFilterBackend]
    #filterset_fields = ['module__id']

    def get_serializer_class(self):
        serializer = self.dict_serializer_classes.get(
            self.request.method, self.serializer_class)
        return serializer

    def perform_list(self, queryset):
        return Menu.objects.get_tree_complete(queryset)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class MenuDetailApi(RetrieveModelMixinCustom, UpdateModelMixinCustom, DestroyModelMixinCustom, GenericAPIView):
    queryset = Menu.objects.all()
    serializer_class = MenuSerializer
    serializer_classes = {
        'GET': ItemTreeSerializer
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

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
