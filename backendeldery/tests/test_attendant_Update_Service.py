from unittest.mock import MagicMock, AsyncMock

import pytest
from fastapi import HTTPException

from backendeldery.models import (
    Attendant,
)
from backendeldery.schemas import UserUpdate, AttendantUpdate
from backendeldery.services.attendantUpdateService import AttendantUpdateService


@pytest.mark.asyncio
async def test_update_user_success(mocker):
    # Arrange
    db = mocker.AsyncMock()
    updated_by = 1
    user_ip = "192.168.1.1"
    service = AttendantUpdateService(db, updated_by, user_ip)

    user_id = 123
    update_data = UserUpdate(email="new@example.com", phone="+123456789")

    # Mock the CRUDUser instance
    mock_crud_user = mocker.patch(
        "backendeldery.services.attendantUpdateService.CRUDUser"
    )
    mock_instance = mock_crud_user.return_value
    mock_user = mocker.MagicMock()

    # Make the update method awaitable by using AsyncMock
    mock_instance.update = mocker.AsyncMock(return_value=mock_user)

    # Act
    result = await service.update_user(user_id, update_data, updated_by, user_ip)

    # Assert
    assert result == mock_user
    mock_instance.update.assert_called_once_with(
        db, user_id, update_data, updated_by, user_ip
    )


@pytest.mark.asyncio
async def test_get_attendant_success(mocker):
    # Arrange
    mock_db = AsyncMock()

    # Create a mock attendant
    mock_attendant = Attendant(user_id=1, cpf="12345678900", created_by=1)

    # Create a regular MagicMock for the result after awaiting
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_attendant

    # Configure execute to return mock_result when awaited
    mock_db.execute = AsyncMock(return_value=mock_result)

    # Create service instance
    service = AttendantUpdateService(mock_db, updated_by=1, user_ip="127.0.0.1")

    # Act
    result = await service.get_attendant(user_id=1)

    # Assert
    assert result == mock_attendant


@pytest.mark.asyncio
async def test_get_attendant_not_found(mocker):
    # Arrange
    mock_db = AsyncMock()

    # Create a regular MagicMock for the result after awaiting
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None

    # Configure execute to return mock_result when awaited
    mock_db.execute = AsyncMock(return_value=mock_result)

    # Create service instance
    service = AttendantUpdateService(mock_db, updated_by=1, user_ip="127.0.0.1")

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await service.get_attendant(user_id=999)

    # Verify exception details
    assert exc_info.value.status_code == 404
    assert "Attendant not found" in exc_info.value.detail


@pytest.mark.asyncio
async def test_update_attendant_with_valid_attendant_update(mocker):
    # Arrange
    db = mocker.AsyncMock()
    updated_by = 123
    user_ip = "192.168.1.1"
    service = AttendantUpdateService(db, updated_by, user_ip)

    # Create a mock attendant
    mock_attendant = Attendant(user_id=1, cpf="12345678900", created_by=1)

    # Create a valid AttendantUpdate with all required fields
    attendant_update = AttendantUpdate(
        address="New Address",
        neighborhood="New Neighborhood",
        city="New City",
        state="New State",
        code_address="12345",
        registro_conselho="New Registry",
        formacao="New Formation",
        nivel_experiencia="senior",
        team_names=["Team A"],
        function_names="Doctor",
        specialties=["Cardiology"]
    )

    # Mock the get_attendant method
    service.get_attendant = AsyncMock(return_value=mock_attendant)

    # Act
    result = await service.update_attendant_core_fields(mock_attendant, attendant_update)

    # Assert
    assert result == mock_attendant
    assert mock_attendant.address == attendant_update.address
    assert mock_attendant.neighborhood == attendant_update.neighborhood
    assert mock_attendant.city == attendant_update.city
    assert mock_attendant.state == attendant_update.state
    assert mock_attendant.code_address == attendant_update.code_address
    assert mock_attendant.registro_conselho == attendant_update.registro_conselho
    assert mock_attendant.formacao == attendant_update.formacao
    assert mock_attendant.nivel_experiencia == attendant_update.nivel_experiencia


@pytest.mark.asyncio
async def test_update_attendant_skips_relationship_fields_in_dict(mocker):
    # Arrange
    db = mocker.AsyncMock()
    updated_by = 456
    user_ip = "10.0.0.1"
    service = AttendantUpdateService(db, updated_by, user_ip)

    attendant = Attendant(user_id=2, cpf="98765432101", created_by=200)

    # Dictionary with both regular and relationship fields
    update_data = {
        "address": "Updated Address",
        "neighborhood": "Updated Neighborhood",
        "specialties": ["Specialty1", "Specialty2"],  # Should be skipped
        "team_names": ["Team1"],  # Should be skipped
        "function_names": "Function1",  # Should be skipped
    }

    # Act
    await service.update_attendant_core_fields(attendant, update_data)

    # Assert
    assert attendant.address == "Updated Address"
    assert attendant.neighborhood == "Updated Neighborhood"
    # Verify relationship fields were not set directly
    assert not hasattr(attendant, "specialties_direct")
    assert not hasattr(attendant, "team_names_direct")
    assert not hasattr(attendant, "function_names_direct")
    assert attendant.updated_by == updated_by
    assert attendant.user_ip == user_ip
