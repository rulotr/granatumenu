from django.urls import path

from .views import ModuleDetailApi, ModuleListApi

app_name = "users"
urlpatterns = [
    # path("api/menu/", view=MenuApi.as_view(), name="menu_list"),
    path("modules/", ModuleListApi.as_view(), name='module-list'),
    path("modules/<int:pk>/", ModuleDetailApi.as_view(), name='module-detail')

]
