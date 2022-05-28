from ipaddress import ip_address
from os import stat
from xml.dom import ValidationErr

from django.core.exceptions import ValidationError
from django.shortcuts import render
from psycopg2 import IntegrityError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from menus.models import Module
from menus.serializers import ModuleSerializer

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


class ModuleDetailApi(APIView):
    def get(self, request):
        return Response()

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

    def delete(self, request, pk):
        Module.objects.execute_delete(pk=pk)
        return Response(status=status.HTTP_204_NO_CONTENT)
