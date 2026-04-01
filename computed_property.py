from __future__ import annotations

from typing import Any, Callable, Optional, Tuple, Type, Union
from weakref import WeakKeyDictionary


_CACHE_MISSING = object()
_DEPENDENCY_MISSING = object()


class _ComputedProperty(property):
    def __init__(
        self,
        fget: Optional[Callable[[Any], Any]] = None,
        fset: Optional[Callable[[Any, Any], None]] = None,
        fdel: Optional[Callable[[Any], None]] = None,
        doc: Optional[str] = None,
        dependencies: tuple[str, ...] = (),
    ) -> None:
        super().__init__(fget, fset, fdel, doc)
        self._dependencies = dependencies
        self._cache_name: Optional[str] = None
        self._fallback_cache: WeakKeyDictionary[Any, tuple[tuple[Any, ...], Any]] = (
            WeakKeyDictionary()
        )

    def __set_name__(self, owner: Type[Any], name: str) -> None:
        self._cache_name = f"__computed_property_cache_{owner.__name__}_{name}_{id(self)}"

    def __get__(self, instance: Any, owner: Optional[Type[Any]] = None) -> Any:
        if instance is None:
            return self
        if self.fget is None:
            raise AttributeError("unreadable attribute")

        snapshot = self._snapshot(instance)
        cached = self._get_cached(instance)
        if cached is not _CACHE_MISSING and cached[0] == snapshot:
            return cached[1]

        value = self.fget(instance)
        self._set_cached(instance, (snapshot, value))
        return value

    def __set__(self, instance: Any, value: Any) -> None:
        if self.fset is None:
            raise AttributeError("can't set attribute")
        self.fset(instance, value)
        self._clear_cached(instance)

    def __delete__(self, instance: Any) -> None:
        if self.fdel is None:
            raise AttributeError("can't delete attribute")
        self.fdel(instance)
        self._clear_cached(instance)

    def getter(self, fget: Callable[[Any], Any]) -> _ComputedProperty:
        return type(self)(fget, self.fset, self.fdel, self.__doc__, self._dependencies)

    def setter(self, fset: Callable[[Any, Any], None]) -> _ComputedProperty:
        return type(self)(self.fget, fset, self.fdel, self.__doc__, self._dependencies)

    def deleter(self, fdel: Callable[[Any], None]) -> _ComputedProperty:
        return type(self)(self.fget, self.fset, fdel, self.__doc__, self._dependencies)

    def _snapshot(self, instance: Any) -> tuple[Any, ...]:
        return tuple(
            getattr(instance, attribute, _DEPENDENCY_MISSING)
            for attribute in self._dependencies
        )

    def _get_cached(self, instance: Any) -> Union[Tuple[Tuple[Any, ...], Any], object]:
        storage, key = self._storage(instance)
        return storage.get(key, _CACHE_MISSING)

    def _set_cached(self, instance: Any, value: tuple[tuple[Any, ...], Any]) -> None:
        storage, key = self._storage(instance)
        storage[key] = value

    def _clear_cached(self, instance: Any) -> None:
        storage, key = self._storage(instance)
        storage.pop(key, None)

    def _storage(self, instance: Any) -> tuple[Any, Any]:
        instance_dict = getattr(instance, "__dict__", None)
        if instance_dict is not None and self._cache_name is not None:
            return instance_dict, self._cache_name
        return self._fallback_cache, instance


def computed_property(*dependencies: str) -> Callable[[Callable[[Any], Any]], property]:
    """Build a cached property invalidated by dependent attributes."""

    def decorator(func: Callable[[Any], Any]) -> property:
        return _ComputedProperty(func, dependencies=tuple(dependencies))

    return decorator
