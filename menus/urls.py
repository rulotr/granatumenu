from django.urls import path

from .views import MenuListApi, ModuleDetailApi, ModuleListApi

app_name = "users"
urlpatterns = [
    path("modules/", ModuleListApi.as_view(), name='module-list'),
    path("modules/<int:pk>/", ModuleDetailApi.as_view(), name='module-detail'),
    path("menu/", MenuListApi.as_view(), name='menu-list'),

]
