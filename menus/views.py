from ipaddress import ip_address
from os import stat
from socket import IP_ADD_MEMBERSHIP
from xml.dom import ValidationErr

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.shortcuts import render
from rest_framework import serializers, status
from rest_framework.generics import GenericAPIView, RetrieveAPIView
from rest_framework.mixins import CreateModelMixin, ListModelMixin
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView
from yaml import serialize

from menus.models import Menu, Module
from menus.serializers import MenuSerializer, MenuTreeSerializer, ModuleSerializer

# Create your views here.


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


class ModuleListApi(CreateModelMixinCustom, ListModelMixin, GenericAPIView):
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer
    model_operations = Module

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class ModuleDetailApi(RetrieveAPIView, GenericAPIView):
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(self, request, *args, **kwargs)

    def put(self, request, pk):
        try:
            serializer = ModuleSerializer(data=request.data)
            if serializer.is_valid():
                update_module = Module.objects.execute_update(
                    pk, **serializer.validated_data)
                resp_module = ModuleSerializer(update_module)
                return Response(resp_module.data, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            return Response(e.message_dict, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError as e:
            return Response({'message': e.args[0]}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            Module.objects.execute_delete(pk=pk)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Module.DoesNotExist as e:
            return Response({'message': e.args[0]}, status=status.HTTP_404_NOT_FOUND)


class MenuListApi(APIView):
    def post(self, request):
        try:
            serializer = MenuSerializer(data=request.data)
            if serializer.is_valid():
                new_module = Menu.objects.execute_create(
                    **serializer.validated_data)
                resp_seri = MenuSerializer(new_module)
                return Response(resp_seri.data, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            return Response(e.message_dict, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError as e:
            return Response({'message': e.args[0]}, status=status.HTTP_400_BAD_REQUEST)


class MenuDetailApi(APIView):
    class MenuPartialSerializer(serializers.Serializer):
        order = serializers.IntegerField()

    def get(self, request, pk):
        tree_menu = Menu.objects.get_tree_by_module(module=pk)
        serializer = MenuTreeSerializer(tree_menu, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        try:
            serializer = MenuSerializer(data=request.data)
            if serializer.is_valid():
                update_menu = Menu.objects.execute_update(
                    pk, **serializer.validated_data)
                resp_menu = MenuSerializer(update_menu)
                return Response(resp_menu.data, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            return Response(e.message_dict, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        serializer = self.MenuPartialSerializer(data=request.data)
        serializer.is_valid()
        Menu.objects.execute_partial_update(pk, **serializer.validated_data)
        return Response(request.data, status=status.HTTP_200_OK)
