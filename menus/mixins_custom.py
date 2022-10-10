"""
Basic building blocks for generic class based views.
We don't bind behaviour to http method handlers yet,
which allows mixin classes to be composed in interesting ways.
"""
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.deletion import ProtectedError
from rest_framework import status
from rest_framework.mixins import (
    CreateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.response import Response
from rest_framework.settings import api_settings


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


class RetrieveModelMixinCustom(RetrieveModelMixin):
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
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
        except ProtectedError as e:
            return Response({'message': e.args[0]}, status=status.HTTP_400_BAD_REQUEST)

    def perform_destroy(self, pk):
        self.model_operations.objects.execute_delete(pk)
