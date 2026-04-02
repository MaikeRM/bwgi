import unittest
from math import sqrt
from computed_property import computed_property

class TestComputedProperty(unittest.TestCase):

    def test_cache_and_recomputation_based_on_dependencies(self):
        class Vector:
            def __init__(self, x, y, z, color=None):
                self.x, self.y, self.z = x, y, z
                self.color = color
                self.compute_calls = 0

            @computed_property('x', 'y', 'z')
            def magnitude(self):
                self.compute_calls += 1
                return sqrt(self.x**2 + self.y**2 + self.z**2)
                
        v = Vector(9, 2, 6)
        self.assertEqual(v.compute_calls, 0)
        
        # First access, computes value
        self.assertEqual(v.magnitude, 11.0)
        self.assertEqual(v.compute_calls, 1)

        # Access without changing dependencies uses cached value
        v.color = 'red'
        self.assertEqual(v.magnitude, 11.0)
        self.assertEqual(v.compute_calls, 1) 

        # Access after changing a dependency recomputes value
        v.y = 18
        self.assertEqual(v.magnitude, 21.0)
        self.assertEqual(v.compute_calls, 2) 

    def test_missing_dependency(self):
        class Circle:
            def __init__(self, radius=1):
                self.radius = radius
                self.compute_calls = 0

            @computed_property('radius', 'area')
            def diameter(self):
                self.compute_calls += 1
                return self.radius * 2

        circle = Circle()
        # Computes first access
        self.assertEqual(circle.diameter, 2)
        self.assertEqual(circle.compute_calls, 1)
        
        # Missing attribute doesn't prevent caching
        self.assertEqual(circle.diameter, 2)
        self.assertEqual(circle.compute_calls, 1)

    def test_setter_and_deleter(self):
        class Circle:
            def __init__(self, radius=1):
                self.radius = radius

            @computed_property('radius')
            def diameter(self):
                return self.radius * 2

            @diameter.setter
            def diameter(self, diameter):
                self.radius = diameter / 2

            @diameter.deleter
            def diameter(self):
                self.radius = 0

        circle = Circle()
        self.assertEqual(circle.diameter, 2)
        
        circle.diameter = 3
        self.assertEqual(circle.radius, 1.5)
        self.assertEqual(circle.diameter, 3)
        
        del circle.diameter
        self.assertEqual(circle.radius, 0)
        self.assertEqual(circle.diameter, 0)

    def test_preserves_docstring(self):
        class Circle:
            def __init__(self, radius=1):
                self.radius = radius

            @computed_property('radius')
            def diameter(self):
                """Circle diameter from radius"""
                return self.radius * 2

        self.assertEqual(Circle.diameter.__doc__, "Circle diameter from radius")

    # ------------------------------------------------------------------
    # Edge cases
    # ------------------------------------------------------------------

    def test_no_dependencies(self):
        """Decorator with zero deps caches once and never recomputes."""
        class Constant:
            call_count = 0

            @computed_property()
            def answer(self):
                Constant.call_count += 1
                return 42

        c = Constant()
        self.assertEqual(c.answer, 42)
        self.assertEqual(c.answer, 42)
        self.assertEqual(Constant.call_count, 1)

    def test_independent_cache_per_instance(self):
        """Each instance has its own isolated cache."""
        class Box:
            def __init__(self, side):
                self.side = side

            @computed_property('side')
            def volume(self):
                return self.side ** 3

        a = Box(2)
        b = Box(3)
        self.assertEqual(a.volume, 8)
        self.assertEqual(b.volume, 27)
        # Mutating one instance does not affect the other
        a.side = 4
        self.assertEqual(a.volume, 64)
        self.assertEqual(b.volume, 27)

    def test_dependency_deleted_after_caching(self):
        """Deleting a dependency attribute causes recomputation."""
        class Item:
            def __init__(self, price):
                self.price = price

            @computed_property('price')
            def label(self):
                price = getattr(self, 'price', None)
                return f'${price}' if price is not None else 'N/A'

        item = Item(10)
        self.assertEqual(item.label, '$10')
        del item.price
        self.assertEqual(item.label, 'N/A')

    def test_list_dependency_mutated_in_place_recomputes(self):
        """In-place list mutations must invalidate the cached value."""
        class Basket:
            def __init__(self):
                self.items = [1]
                self.calls = 0

            @computed_property('items')
            def total(self):
                self.calls += 1
                return sum(self.items)

        basket = Basket()
        self.assertEqual(basket.total, 1)
        self.assertEqual(basket.total, 1)
        self.assertEqual(basket.calls, 1)

        basket.items.append(2)
        self.assertEqual(basket.total, 3)
        self.assertEqual(basket.calls, 2)

    def test_dict_dependency_mutated_in_place_recomputes(self):
        """In-place dict mutations must invalidate the cached value."""
        class Portfolio:
            def __init__(self):
                self.positions = {'AAPL': 10}
                self.calls = 0

            @computed_property('positions')
            def position_count(self):
                self.calls += 1
                return len(self.positions)

        portfolio = Portfolio()
        self.assertEqual(portfolio.position_count, 1)
        self.assertEqual(portfolio.position_count, 1)
        self.assertEqual(portfolio.calls, 1)

        portfolio.positions['MSFT'] = 5
        self.assertEqual(portfolio.position_count, 2)
        self.assertEqual(portfolio.calls, 2)

    def test_falsy_dependency_values_cache_correctly(self):
        """Dependencies with falsy values (0, None, False, '') must not be
        confused with _MISSING and must still be cached."""
        class Falsy:
            def __init__(self):
                self.value = 0
                self.calls = 0

            @computed_property('value')
            def doubled(self):
                self.calls += 1
                return self.value * 2

        f = Falsy()
        self.assertEqual(f.doubled, 0)
        self.assertEqual(f.doubled, 0)   # must hit cache, not recompute
        self.assertEqual(f.calls, 1)

    def test_no_setter_raises_descriptive_error(self):
        """__set__ without a registered setter raises AttributeError with name."""
        class Point:
            def __init__(self, x):
                self.x = x

            @computed_property('x')
            def double(self):
                return self.x * 2

        p = Point(3)
        with self.assertRaises(AttributeError) as ctx:
            p.double = 99
        self.assertIn('double', str(ctx.exception))

    def test_no_deleter_raises_descriptive_error(self):
        """__delete__ without a registered deleter raises AttributeError with name."""
        class Point:
            def __init__(self, x):
                self.x = x

            @computed_property('x')
            def double(self):
                return self.x * 2

        p = Point(3)
        with self.assertRaises(AttributeError) as ctx:
            del p.double
        self.assertIn('double', str(ctx.exception))

    def test_getter_exception_does_not_poison_cache(self):
        """If the getter raises, no stale value is stored — next access retries."""
        class Flaky:
            def __init__(self):
                self.x = 1
                self.fail = True

            @computed_property('x', 'fail')
            def result(self):
                if self.fail:
                    raise RuntimeError('not ready')
                return self.x * 10

        obj = Flaky()
        with self.assertRaises(RuntimeError):
            _ = obj.result
        # Fix the object and verify the value is now computed correctly
        obj.fail = False
        self.assertEqual(obj.result, 10)

    def test_class_level_access_returns_descriptor(self):
        """Accessing the property from the class returns the descriptor itself."""
        class Widget:
            def __init__(self, w):
                self.w = w

            @computed_property('w')
            def width(self):
                """Widget width."""
                return self.w

        self.assertIsInstance(Widget.width, computed_property)
        self.assertEqual(Widget.width.__doc__, 'Widget width.')

    def test_setter_invalidates_cache_without_dependencies(self):
        """Setter must invalidate cached values even when there are no deps."""
        class Counter:
            def __init__(self):
                self.calls = 0
                self._value = 1

            @computed_property()
            def value(self):
                self.calls += 1
                return self._value

            @value.setter
            def value(self, value):
                self._value = value

        counter = Counter()
        self.assertEqual(counter.value, 1)
        self.assertEqual(counter.calls, 1)

        counter.value = 10
        self.assertEqual(counter.value, 10)
        self.assertEqual(counter.calls, 2)

    def test_subclass_setter_does_not_mutate_base_descriptor(self):
        """Subclass setter must not leak back into the base descriptor."""
        class Base:
            def __init__(self, x):
                self.x = x

            @computed_property('x')
            def doubled(self):
                return self.x * 2

        class Child(Base):
            @Base.doubled.setter
            def doubled(self, value):
                self.x = value / 2

        base = Base(2)
        child = Child(2)

        with self.assertRaises(AttributeError):
            base.doubled = 10

        child.doubled = 10
        self.assertEqual(child.x, 5)


if __name__ == '__main__':
    unittest.main()
