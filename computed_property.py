_CACHE_MISSING = object()
_DEPENDENCY_MISSING = object()


class _ComputedProperty(property):
    def __init__(
        self,
        fget=None,
        fset=None,
        fdel=None,
        doc=None,
        dependencies=(),
    ):
        super().__init__(fget, fset, fdel, doc)
        self._dependencies = dependencies
        self._cache_name = None

    def __set_name__(self, owner, name):
        self._cache_name = f"__computed_property_cache_{owner.__name__}_{name}_{id(self)}"

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        if self.fget is None:
            raise AttributeError("unreadable attribute")

        snapshot = self._snapshot(instance)
        cache = getattr(instance, "__dict__", None)
        cached = _CACHE_MISSING if cache is None else cache.get(self._cache_name, _CACHE_MISSING)
        if cached is not _CACHE_MISSING and cached[0] == snapshot:
            return cached[1]

        value = self.fget(instance)
        if cache is not None:
            cache[self._cache_name] = (snapshot, value)
        return value

    def __set__(self, instance, value):
        if self.fset is None:
            raise AttributeError("can't set attribute")
        self.fset(instance, value)
        self._clear_cached(instance)

    def __delete__(self, instance):
        if self.fdel is None:
            raise AttributeError("can't delete attribute")
        self.fdel(instance)
        self._clear_cached(instance)

    def getter(self, fget):
        return type(self)(fget, self.fset, self.fdel, self.__doc__, self._dependencies)

    def setter(self, fset):
        return type(self)(self.fget, fset, self.fdel, self.__doc__, self._dependencies)

    def deleter(self, fdel):
        return type(self)(self.fget, self.fset, fdel, self.__doc__, self._dependencies)

    def _snapshot(self, instance):
        return tuple(
            getattr(instance, attribute, _DEPENDENCY_MISSING)
            for attribute in self._dependencies
        )

    def _clear_cached(self, instance):
        cache = getattr(instance, "__dict__", None)
        if cache is not None:
            cache.pop(self._cache_name, None)


def computed_property(*dependencies):
    """Build a cached property invalidated by dependent attributes."""

    def decorator(func):
        return _ComputedProperty(func, dependencies=tuple(dependencies))

    return decorator
