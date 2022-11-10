from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import MenuViewSetApi, ModuleViewSetApi

app_name = "users"

router = DefaultRouter()
router.register("modules", ModuleViewSetApi, basename="module")
router.register("menus", MenuViewSetApi, basename="menu")

urlpatterns = [
    path('', include(router.urls))
]
