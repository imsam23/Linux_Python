"""
Test for Resource class
Command Line: python -m pytest tests/unit/test_resource.py
"""

import pytest
from app.utils.validators import validate_integer
from app.model import inventory


@pytest.fixture
def resource_values():
    return {
        'name': 'Car',
        'manufacturer': 'Maruti',
        'total': 10,
        'allocated': 5
    }

@pytest.fixture
def resource(resource_values):
    return inventory.Resource(**resource_values)


def test_create_resource(resource_values, resource):
    # 1st ways
    # resource = inventory.Resource('Car', 'Maruti', 10, 5)
    # assert resource.name == 'Car'
    # assert resource.manufacturer == 'Maruti'
    # 2nd Way
    # assert resource.name == resource_values['name']
    # assert resource.manufacturer == resource_values['manufacturer']
    # 3rd way
    for attr_name in resource_values:
        assert getattr(resource, attr_name) == resource_values.get(attr_name)


def test_create_invalid_resource():
    with pytest.raises(TypeError):
        inventory.Resource('Car', 'Maruti', 10.5, 5)
