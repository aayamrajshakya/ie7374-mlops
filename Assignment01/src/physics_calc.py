from .constants import ACCELERATION, C


def kinetic_energy(mass, velocity):
    return 0.5 * mass * pow(velocity, 2)


def potential_energy(mass, height, gravity=ACCELERATION):
    return mass * gravity * height


def force(mass):
    return mass * ACCELERATION


def work(force, distance):
    return force * distance


def momentum(mass, velocity):
    return mass * velocity


def celsius_to_fahrenheit(celsius):
    return celsius * (9 / 5) + 32


def fahrenheit_to_celsius(fahrenheit):
    return (fahrenheit - 32) * (5 / 9)


def celsius_to_kelvin(celsius):
    return celsius + 273.15


def kelvin_to_celsius(kelvin):
    return kelvin - 273.15


def fahrenheit_to_kelvin(fahrenheit):
    return (fahrenheit - 32) * (5 / 9) + 273.15


def kelvin_to_fahrenheit(kelvin):
    return (kelvin - 273.15) * (9 / 5) + 32


def einstein_formula(mass):
    return mass * pow(C, 2)  # e=mc^2
