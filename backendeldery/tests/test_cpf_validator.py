from unittest.mock import Mock

import pytest

from backendeldery.validators.cpf_validator import validate_cpf_format


def test_valid_cpf_returns_formatted_cpf():
    # Create a mock ValidationInfo
    mock_info = Mock()
    mock_info.config = {}

    # Mock the handler function to return the input
    def mock_handler(value):
        return value

    # Use the mock_info instead of creating a ValidationInfo instance
    result = validate_cpf_format("12345678901", mock_handler, mock_info)
    assert result == "123.456.789-01"

    # Test with already formatted CPF
    result = validate_cpf_format("123.456.789-01", mock_handler, mock_info)
    assert result == "123.456.789-01"


def test_none_input_handled_appropriately():
    # Create a mock ValidationInfo
    mock_info = Mock()
    mock_info.config = {}

    # Track if handler was called with None
    handler_called_with_none = False

    def mock_handler(value):
        nonlocal handler_called_with_none
        if value is None:
            handler_called_with_none = True
        return value

    # Use the mock_info
    result = validate_cpf_format(None, mock_handler, mock_info)
    assert handler_called_with_none is True
    assert result is None


def test_cpf_with_insufficient_digits_after_cleaning():
    from pydantic_core import PydanticCustomError

    # Create a mock ValidationInfo
    mock_info = Mock()
    mock_info.config = {}

    def mock_handler(value):
        return value

    # Use the mock_info
    with pytest.raises(PydanticCustomError) as exc_info:
        validate_cpf_format("123.abc.456", mock_handler, mock_info)

    # Option 1: Match the exact string format
    assert "CPF deve conter 11 dígitos" in str(exc_info.value)
