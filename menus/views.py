from ipaddress import ip_address
from os import stat
from socket import IP_ADD_MEMBERSHIP
from xml.dom import ValidationErr

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from menus.models import Menu, Module
from menus.serializers import MenuSerializer, ModuleSerializer

# Create your views here.


class ModuleListApi(APIView):
    def get(self, request):
        modules = Module.objects.get_all()
        serializer = ModuleSerializer(modules, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        try:
            serializer = ModuleSerializer(data=request.data)
            if serializer.is_valid():
                new_module = Module.objects.execute_create(
                    **serializer.validated_data)
                resp_seri = ModuleSerializer(new_module)
                return Response(resp_seri.data, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            return Response(e.message_dict, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError as e:
            return Response({'message': e.args[0]}, status=status.HTTP_400_BAD_REQUEST)


class ModuleDetailApi(APIView):
    def get(self, request, pk):
        try:
            module = Module.objects.find_by_pk(pk)
            serializer = ModuleSerializer(module)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Module.DoesNotExist as e:
            return Response({'message': e.args[0]}, status=status.HTTP_404_NOT_FOUND)

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
