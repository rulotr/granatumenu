import factory

# My app
from menus.models import Menu, Module


class ModuleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Module
    pk = factory.Sequence(lambda n: n+1)
    name = factory.Sequence(lambda n: 'Module {}'.format(n+1))


class MenuFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Menu
    pk = factory.Sequence(lambda n: n+1)
    name = factory.Sequence(lambda n: 'Menu {}'.format(n+1))
    module = factory.LazyAttribute(lambda x: ModuleFactory())
    parent = None  # factory.LazyAttribute(lambda x: MenuFactory(parent=None))
    order = factory.Sequence(lambda n: n+1)

    @classmethod
    def _adjust_kwargs(cls, **kwargs):
        if kwargs['parent']:
            kwargs['module'] = kwargs['parent'].module
        return kwargs
