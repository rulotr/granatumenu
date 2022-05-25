from django.urls import path

from .views import ModuleListApi

app_name = "users"
urlpatterns = [
    # path("api/menu/", view=MenuApi.as_view(), name="menu_list"),
    path("modules/", ModuleListApi.as_view(), name='module-list')

]
