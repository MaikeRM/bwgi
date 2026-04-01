import unittest

from computed_property import computed_property


class ComputedPropertyTests(unittest.TestCase):
    def test_caches_until_dependencies_change(self) -> None:
        class Vector:
            def __init__(self, x: int, y: int, z: int) -> None:
                self.x = x
                self.y = y
                self.z = z
                self.color = None
                self.calls = 0

            @computed_property("x", "y", "z")
            def magnitude(self) -> int:
                self.calls += 1
                return self.x + self.y + self.z

        vector = Vector(9, 2, 6)

        self.assertEqual(vector.magnitude, 17)
        self.assertEqual(vector.magnitude, 17)
        self.assertEqual(vector.calls, 1)

        vector.color = "red"
        self.assertEqual(vector.magnitude, 17)
        self.assertEqual(vector.calls, 1)

        vector.y = 18
        self.assertEqual(vector.magnitude, 33)
        self.assertEqual(vector.calls, 2)

    def test_missing_dependency_is_treated_as_stable_until_it_appears(self) -> None:
        class Circle:
            def __init__(self, radius: int = 1) -> None:
                self.radius = radius
                self.calls = 0

            @computed_property("radius", "area")
            def diameter(self) -> int:
                self.calls += 1
                return self.radius * 2

        circle = Circle()

        self.assertEqual(circle.diameter, 2)
        self.assertEqual(circle.diameter, 2)
        self.assertEqual(circle.calls, 1)

        circle.area = 3.14
        self.assertEqual(circle.diameter, 2)
        self.assertEqual(circle.calls, 2)

    def test_supports_setter_and_deleter(self) -> None:
        class Circle:
            def __init__(self, radius: float = 1) -> None:
                self.radius = radius

            @computed_property("radius")
            def diameter(self) -> float:
                return self.radius * 2

            @diameter.setter
            def diameter(self, diameter: float) -> None:
                self.radius = diameter / 2

            @diameter.deleter
            def diameter(self) -> None:
                self.radius = 0

        circle = Circle()
        self.assertEqual(circle.diameter, 2)

        circle.diameter = 3
        self.assertEqual(circle.radius, 1.5)

        del circle.diameter
        self.assertEqual(circle.radius, 0)

    def test_preserves_docstring(self) -> None:
        class Circle:
            @computed_property("radius")
            def diameter(self) -> int:
                """Circle diameter from radius"""
                return 2

        self.assertEqual(Circle.diameter.__doc__, "Circle diameter from radius")


if __name__ == "__main__":
    unittest.main()

