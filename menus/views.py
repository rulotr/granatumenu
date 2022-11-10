
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.generics import GenericAPIView

from menus.mixins_custom import (
    CreateModelMixinCustom,
    DestroyModelMixinCustom,
    ListModelMixinCustom,
    RetrieveModelMixinCustom,
    UpdateModelMixinCustom,
)
from menus.models import Menu, Module
from menus.serializers import MenuSerializer, MenuTreeSerializer, ModuleSerializer

# Create your views here.


class ModuleViewSetApi(CreateModelMixinCustom, ListModelMixinCustom, RetrieveModelMixinCustom, UpdateModelMixinCustom, DestroyModelMixinCustom, viewsets.GenericViewSet):
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer
    model_operations = Module


class MenuViewSetApi(CreateModelMixinCustom, ListModelMixinCustom, RetrieveModelMixinCustom, UpdateModelMixinCustom, DestroyModelMixinCustom, viewsets.GenericViewSet):
    queryset = Menu.objects.all().select_related('module')
    serializer_class = MenuSerializer
    model_operations = Menu
    dict_serializer_classes = {
        'list': MenuTreeSerializer,
    }
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['module__id']

    def get_serializer_class(self):
        serializer = self.dict_serializer_classes.get(
            self.action, self.serializer_class)
        return serializer

    def perform_list(self, queryset):
        return Menu.objects.get_tree_complete(queryset)


''' 
class MenuListApi(CreateModelMixinCustom, ListModelMixinCustom, GenericAPIView):
    queryset = Menu.objects.all().select_related('module')
    model_operations = Menu

    dict_serializer_classes = {
        'GET': MenuTreeSerializer,
        'POST': MenuSerializer
    }
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['module__id']

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
    model_operations = Menu

    def get(self, request,  *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
 '''
