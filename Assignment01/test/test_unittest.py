import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.physics_calc import *
from src.constants import *


class TestPhysics(unittest.TestCase):

    def test_kinetic_energy(self):
        self.assertEqual(kinetic_energy(2, 3), 9.0)

    def test_potential_energy(self):
        self.assertEqual(potential_energy(2, 5), 98.0)

    def test_force(self):
        self.assertEqual(force(10), 98.0)
        self.assertNotEqual(force(10), 100.0)

    def test_work(self):
        self.assertEqual(work(10, 5), 50.0)

    def test_momentum(self):
        self.assertEqual(momentum(5, 10), 50.0)

    def test_acceleration_value(self):
        self.assertEqual(ACCELERATION, 9.8)

    def test_acceleration_not_equal(self):
        self.assertNotEqual(ACCELERATION, 10.0)
        self.assertNotEqual(ACCELERATION, 9.81)

    def test_speed_of_light(self):
        self.assertEqual(C, 299792458)
        self.assertEqual(C, 3e8)

    def test_celsius_to_fahrenheit(self):
        self.assertEqual(celsius_to_fahrenheit(0), 32.0)
        self.assertEqual(celsius_to_fahrenheit(100), 212.0)
        self.assertEqual(celsius_to_fahrenheit(-40), -40.0)

    def test_fahrenheit_to_celsius(self):
        self.assertEqual(fahrenheit_to_celsius(32), 0.0)
        self.assertEqual(fahrenheit_to_celsius(212), 100.0)
        self.assertEqual(fahrenheit_to_celsius(-40), -40.0)

    def test_celsius_to_kelvin(self):
        self.assertEqual(celsius_to_kelvin(0), 273.15)
        self.assertEqual(celsius_to_kelvin(100), 373.15)
        self.assertEqual(celsius_to_kelvin(-273.15), 0.0)

    def test_kelvin_to_celsius(self):
        self.assertEqual(kelvin_to_celsius(273.15), 0.0)
        self.assertEqual(kelvin_to_celsius(373.15), 100.0)
        self.assertEqual(kelvin_to_celsius(0), -273.15)

    def test_fahrenheit_to_kelvin(self):
        self.assertEqual(fahrenheit_to_kelvin(32), 273.15)
        self.assertEqual(fahrenheit_to_kelvin(212), 373.15)

    def test_kelvin_to_fahrenheit(self):
        self.assertEqual(kelvin_to_fahrenheit(273.15), 32.0)
        self.assertEqual(kelvin_to_fahrenheit(373.15), 212.0)

    def test_temperature_roundtrip(self):
        c = 25.0
        f = celsius_to_fahrenheit(c)
        k = celsius_to_kelvin(c)
        self.assertEqual(fahrenheit_to_celsius(f), c)
        self.assertEqual(kelvin_to_celsius(k), c)
        self.assertEqual(fahrenheit_to_kelvin(f), k)
        self.assertEqual(kelvin_to_fahrenheit(k), f)

    def test_einstein_formula(self):
        self.assertEqual(einstein_formula(1), pow(C, 2))
        self.assertEqual(einstein_formula(2), 2 * pow(C, 2))
        self.assertEqual(einstein_formula(0), 0)


if __name__ == "__main__":
    unittest.main()
