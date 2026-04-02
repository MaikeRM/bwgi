from copy import deepcopy
from typing import Any, Callable, Optional, Tuple

_MISSING: object = object()  # sentinel for absent attributes


class computed_property:
    """Caching descriptor that invalidates when declared dependencies change.

    Works like ``property`` but stores results alongside a snapshot of the
    dependency values.  The cache is recomputed only when the snapshot differs
    from the current attribute values, mimicking SecDB-style reactive fields.

    Example::

        class Circle:
            def __init__(self, r):
                self.radius = r

            @computed_property("radius")
            def area(self):
                return 3.14159 * self.radius ** 2
    """

    def __init__(self, *deps: str) -> None:
        """Initialise the descriptor with the names of its dependencies.

        Args:
            *deps: Attribute names on the owner instance whose values are
                   tracked to decide when to invalidate the cache.
        """
        self._deps: Tuple[str, ...] = deps
        self._fget: Optional[Callable] = None
        self._fset: Optional[Callable] = None
        self._fdel: Optional[Callable] = None
        self.__doc__: Optional[str] = None

    def __call__(self, fget: Callable) -> "computed_property":
        """Register the getter and return self so the instance acts as a descriptor.

        Args:
            fget: The getter function being decorated.

        Returns:
            This descriptor instance.
        """
        self._fget = fget
        self.__doc__ = fget.__doc__
        self.__name__: str = fget.__name__
        return self

    def setter(self, fset: Callable) -> "computed_property":
        """Attach a setter to the descriptor.

        Args:
            fset: The setter function.

        Returns:
            This descriptor instance.
        """
        self._fset = fset
        return self

    def deleter(self, fdel: Callable) -> "computed_property":
        """Attach a deleter to the descriptor.

        Args:
            fdel: The deleter function.

        Returns:
            This descriptor instance.
        """
        self._fdel = fdel
        return self

    @property
    def _cache_key(self) -> str:
        """Private key used to store the cached value in the owner's ``__dict__``."""
        return f"_cp_cache_{self.__name__}"

    @property
    def _snap_key(self) -> str:
        """Private key used to store the dependency snapshot in the owner's ``__dict__``."""
        return f"_cp_snap_{self.__name__}"

    def _snapshot(self, obj: Any) -> Tuple:
        """Return a tuple of the current dependency values for *obj*.

        Missing attributes are represented by ``_MISSING``, so a transition
        from absent to present (or vice-versa) correctly triggers recomputation.
        Dependency values are deep-copied when possible so in-place mutations of
        lists, dicts, and similar containers also invalidate the cache.

        Args:
            obj: The owner instance.

        Returns:
            Tuple of current dependency values.
        """
        return tuple(self._freeze(getattr(obj, dep, _MISSING)) for dep in self._deps)

    def _freeze(self, value: Any) -> Any:
        """Return a detached snapshot of a dependency value when possible."""
        if value is _MISSING:
            return value

        try:
            return deepcopy(value)
        except Exception:
            return value

    def __get__(self, obj: Any, objtype: Optional[type] = None) -> Any:
        """Return the cached value, recomputing it if dependencies have changed.

        Args:
            obj: The owner instance, or ``None`` when accessed from the class.
            objtype: The owner class.

        Returns:
            The descriptor itself when accessed from the class; otherwise the
            (possibly recomputed) property value.
        """
        if obj is None:
            return self

        current = self._snapshot(obj)
        cached = obj.__dict__.get(self._cache_key, _MISSING)
        snap = obj.__dict__.get(self._snap_key, _MISSING)

        if cached is not _MISSING and snap == current:
            return cached

        if self._fget is None:
            raise AttributeError(f"unreadable attribute '{self.__name__}'")

        value = self._fget(obj)
        obj.__dict__[self._cache_key] = value
        obj.__dict__[self._snap_key] = current
        return value

    def __set__(self, obj: Any, value: Any) -> None:
        """Delegate to the registered setter, or raise if none is set.

        Args:
            obj: The owner instance.
            value: The value to assign.

        Raises:
            AttributeError: If no setter has been registered.
        """
        if self._fset is None:
            name = getattr(self, "__name__", "?")
            raise AttributeError(f"can't set attribute '{name}'")
        self._fset(obj, value)

    def __delete__(self, obj: Any) -> None:
        """Delegate to the registered deleter, or raise if none is set.

        Args:
            obj: The owner instance.

        Raises:
            AttributeError: If no deleter has been registered.
        """
        if self._fdel is None:
            name = getattr(self, "__name__", "?")
            raise AttributeError(f"can't delete attribute '{name}'")
        self._fdel(obj)
