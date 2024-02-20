"""
Test for CPU class
Command Line: python -m pytest tests/unit/test_cpu.py
"""

import pytest
from app.utils.validators import validate_integer
from app.model import inventory


@pytest.fixture
def cpu_values():
    return {
        'name': 'Ryzen 7000',
        'manufacturer': 'AMD',
        'total': 10,
        'allocated': 5,
        'cores': 32,
        'socket': 'sTR4',
        'power_wattage': 250
    }

@pytest.fixture
def cpu(cpu_values):
    return inventory.Resource(**cpu_values)

def test_create_cpu(cpu_values, cpu):
    for attr_name in cpu_values:
        assert getattr(cpu, attr_name) == cpu_values.get(attr_name)


