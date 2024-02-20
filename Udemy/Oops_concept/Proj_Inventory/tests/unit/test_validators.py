"""
Test the validators functions
Command Line: python -m pytest tests/test_validators.py
"""

import pytest
from app.utils.validators import validate_integer


class TestIntegerValidator:
    def test_valid(self):
        validate_integer('arg', 10, 0, 20, 'custom_min_msg', 'custom_max_msg')

    def test_type_error(self):
        with pytest.raises(TypeError):
            validate_integer('arg', 10.5, 0, 20, 'custom_min_msg', 'custom_max_msg')