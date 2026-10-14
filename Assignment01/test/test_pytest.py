from src.physics_calc import *
from src.constants import *


def test_kinetic_energy():
    assert kinetic_energy(2, 3) == 9.0


def test_potential_energy():
    assert potential_energy(2, 5) == 98.0
    assert potential_energy(2, 5) != 100


def test_force():
    assert force(10) == 98.0
    assert force(10) != 100.0


def test_work():
    assert work(10, 5) == 50.0


def test_momentum():
    assert momentum(5, 10) == 50.0


def test_acceleration_value():
    assert ACCELERATION == 9.8
    assert ACCELERATION != 10.0


def test_speed_of_light():
    assert C == 299792458
    assert C != 3e8


def test_celsius_to_fahrenheit():
    assert celsius_to_fahrenheit(0) == 32.0
    assert celsius_to_fahrenheit(100) == 212.0
    assert celsius_to_fahrenheit(-40) == -40.0


def test_fahrenheit_to_celsius():
    assert fahrenheit_to_celsius(32) == 0.0
    assert fahrenheit_to_celsius(212) == 100.0
    assert fahrenheit_to_celsius(-40) == -40.0


def test_celsius_to_kelvin():
    assert celsius_to_kelvin(0) == 273.15
    assert celsius_to_kelvin(100) == 373.15
    assert celsius_to_kelvin(-273.15) == 0.0


def test_kelvin_to_celsius():
    assert kelvin_to_celsius(273.15) == 0.0
    assert kelvin_to_celsius(373.15) == 100.0
    assert kelvin_to_celsius(0) == -273.15


def test_fahrenheit_to_kelvin():
    assert fahrenheit_to_kelvin(32) == 273.15
    assert fahrenheit_to_kelvin(212) == 373.15


def test_kelvin_to_fahrenheit():
    assert kelvin_to_fahrenheit(273.15) == 32.0
    assert kelvin_to_fahrenheit(373.15) == 212.0


def test_temperature_roundtrip():
    c = 25.0
    f = celsius_to_fahrenheit(c)
    k = celsius_to_kelvin(c)
    assert fahrenheit_to_celsius(f) == c
    assert kelvin_to_celsius(k) == c
    assert fahrenheit_to_kelvin(f) == k
    assert kelvin_to_fahrenheit(k) == f


def test_einstein_formula():
    assert einstein_formula(1) == pow(C, 2)
    assert einstein_formula(2) == 2 * pow(C, 2)
    assert einstein_formula(0) == 0
