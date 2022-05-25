from os import stat
from xml.dom import ValidationErr

from django.core.exceptions import ValidationError
from django.shortcuts import render
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
            serializer.is_valid()
            new_module = Module.objects.execute_create(
                **serializer.validated_data)

            resp_seri = ModuleSerializer(new_module)

            return Response(resp_seri.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({}, status=status.HTTP_400_BAD_REQUEST)


class MenuDetailApi(APIView):
    def get(self, request):
        return Response()
