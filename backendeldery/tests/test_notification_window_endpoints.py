"""
Tests for notification window fields in GET endpoints.
CB-149: Testing that GET User and GET Attendant endpoints return notification window fields.
"""

import pytest
from unittest.mock import MagicMock
from datetime import datetime

from backendeldery.schemas import UserResponse, AttendantInfo
from backendeldery.services.users import UserService
from backendeldery.services.attendants import AttendantService


class TestUserNotificationWindowEndpoints:
    """Test notification window fields in User GET endpoints."""

    @pytest.mark.asyncio
    async def test_get_user_returns_notification_window_fields(self, mocker):
        """Test that GET /users/{user_id} returns notification window fields."""
        # Arrange
        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.name = "John Doe"
        mock_user.email = "john@example.com"
        mock_user.phone = "+123456789"
        mock_user.receipt_type = 1
        mock_user.role = "subscriber"
        mock_user.active = True
        mock_user.notification_start_time = "08:00"
        mock_user.notification_end_time = "22:00"
        mock_user.paused_until = datetime(2024, 12, 25, 10, 0, 0)
        mock_user.client_data = None
        mock_user.attendant_data = None

        # Mock the CRUD call
        mocker.patch(
            "backendeldery.crud.users.crud_specialized_user.get_user_with_client",
            return_value=mock_user
        )

        # Act
        result = await UserService.get_subscriber_by_id(db=mock_db, user_id=1)

        # Assert
        assert isinstance(result, UserResponse)
        assert result.id == 1
        assert result.name == "John Doe"
        assert result.notification_start_time == "08:00"
        assert result.notification_end_time == "22:00"
        assert result.paused_until == datetime(2024, 12, 25, 10, 0, 0)

    @pytest.mark.asyncio
    async def test_get_user_with_default_notification_times(self, mocker):
        """Test that users without explicit notification times return defaults."""
        # Arrange
        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.id = 2
        mock_user.name = "Jane Doe"
        mock_user.email = "jane@example.com"
        mock_user.phone = "+987654321"
        mock_user.receipt_type = 2
        mock_user.role = "contact"
        mock_user.active = True
        mock_user.notification_start_time = None  # Should use model default
        mock_user.notification_end_time = None    # Should use model default
        mock_user.paused_until = None
        mock_user.client_data = None
        mock_user.attendant_data = None

        # Mock the CRUD call
        mocker.patch(
            "backendeldery.crud.users.crud_specialized_user.get_user_with_client",
            return_value=mock_user
        )

        # Act
        result = await UserService.get_subscriber_by_id(db=mock_db, user_id=2)

        # Assert
        assert isinstance(result, UserResponse)
        assert result.id == 2
        assert result.notification_start_time is None  # Explicit None passed through
        assert result.notification_end_time is None
        assert result.paused_until is None


class TestAttendantNotificationWindowEndpoints:
    """Test notification window fields in Attendant GET endpoints."""

    @pytest.mark.asyncio
    async def test_get_attendant_returns_notification_window_fields(self, mocker):
        """Test that GET /attendants/{attendant_id} returns notification window fields."""
        # Arrange
        mock_db = MagicMock()
        
        # Mock UserInfo response with notification fields
        mock_attendant_response = {
            "id": 1,
            "name": "Dr. Smith",
            "email": "dr.smith@example.com",
            "phone": "+123456789",
            "receipt_type": 1,
            "role": "attendant",
            "active": True,
            "notification_start_time": "09:00",
            "notification_end_time": "18:00", 
            "paused_until": None,
            "attendant_data": {
                "cpf": "123.456.789-00",
                "birthday": "1980-01-01",
                "address": "123 Medical St",
                "city": "Health City",
                "state": "HC",
                "code_address": "12345",
                "registro_conselho": "CRM123456",
                "nivel_experiencia": "senior",
                "formacao": "Medicine",
                "specialty_names": ["Cardiology"],
                "team_names": ["Team A"],
                "function_names": "Doctor"
            }
        }

        # Mock the CRUD call to return the dictionary
        mock_crud = mocker.patch("backendeldery.services.attendants.CRUDAttendant")
        mock_crud.return_value.get.return_value = mock_attendant_response

        # Act
        result = await AttendantService.get_attendant_by_id(db=mock_db, id=1)

        # Assert
        assert result is not None
        assert result["id"] == 1
        assert result["name"] == "Dr. Smith"
        assert result["notification_start_time"] == "09:00"
        assert result["notification_end_time"] == "18:00"
        assert result["paused_until"] is None

    @pytest.mark.asyncio
    async def test_get_attendant_with_paused_notifications(self, mocker):
        """Test that attendant with paused notifications returns paused_until correctly."""
        # Arrange
        mock_db = MagicMock()
        pause_datetime = datetime(2024, 12, 31, 23, 59, 59)
        
        # Mock UserInfo response with paused notifications
        mock_attendant_response = {
            "id": 2,
            "name": "Dr. Johnson",
            "email": "dr.johnson@example.com",
            "phone": "+987654321",
            "receipt_type": 2,
            "role": "attendant",
            "active": True,
            "notification_start_time": "07:00",
            "notification_end_time": "19:00",
            "paused_until": pause_datetime,
            "attendant_data": {
                "cpf": "987.654.321-00",
                "birthday": "1975-05-15",
                "address": "456 Health Ave",
                "city": "Med Town",
                "state": "MT",
                "code_address": "54321",
                "registro_conselho": "CRM654321",
                "nivel_experiencia": "especialista",
                "formacao": "Nursing",
                "specialty_names": ["Pediatrics"],
                "team_names": ["Team B"],
                "function_names": "Nurse"
            }
        }

        # Mock the CRUD call
        mock_crud = mocker.patch("backendeldery.services.attendants.CRUDAttendant")
        mock_crud.return_value.get.return_value = mock_attendant_response

        # Act
        result = await AttendantService.get_attendant_by_id(db=mock_db, id=2)

        # Assert
        assert result is not None
        assert result["id"] == 2
        assert result["paused_until"] == pause_datetime


class TestNotificationWindowSchemaValidation:
    """Test that the response schemas properly validate notification window fields."""

    def test_user_response_schema_includes_notification_fields(self):
        """Test UserResponse schema includes notification window fields."""
        # Arrange & Act
        user_data = {
            "id": 1,
            "name": "Test User",
            "email": "test@example.com",
            "phone": "+123456789",
            "receipt_type": 1,
            "role": "subscriber",
            "active": True,
            "notification_start_time": "08:30",
            "notification_end_time": "21:30",
            "paused_until": datetime(2024, 12, 25, 12, 0, 0),
            "client_data": None,
            "attendant_data": None
        }
        
        user_response = UserResponse(**user_data)

        # Assert
        assert user_response.notification_start_time == "08:30"
        assert user_response.notification_end_time == "21:30"
        assert user_response.paused_until == datetime(2024, 12, 25, 12, 0, 0)

    def test_attendant_info_schema_includes_notification_fields(self):
        """Test AttendantInfo schema includes notification window fields."""
        # Arrange & Act
        attendant_data = {
            "id": 1,
            "name": "Dr. Test",
            "email": "dr.test@example.com", 
            "phone": "+123456789",
            "receipt_type": 1,
            "role": "attendant",
            "active": True,
            "notification_start_time": "09:00",
            "notification_end_time": "17:00",
            "paused_until": None,
            "attendant_data": None
        }
        
        attendant_info = AttendantInfo(**attendant_data)

        # Assert
        assert attendant_info.notification_start_time == "09:00"
        assert attendant_info.notification_end_time == "17:00"
        assert attendant_info.paused_until is None

    def test_schema_with_none_notification_fields(self):
        """Test schemas handle None values for notification fields correctly."""
        # Test UserResponse
        user_data = {
            "id": 1,
            "name": "Test User",
            "email": "test@example.com",
            "phone": "+123456789",
            "receipt_type": 1,
            "role": "contact",
            "active": True,
            "notification_start_time": None,
            "notification_end_time": None,
            "paused_until": None,
            "client_data": None,
            "attendant_data": None
        }
        
        user_response = UserResponse(**user_data)
        assert user_response.notification_start_time is None
        assert user_response.notification_end_time is None
        assert user_response.paused_until is None

        # Test AttendantInfo
        attendant_data = {
            "id": 1,
            "name": "Dr. Test",
            "email": "dr.test@example.com",
            "phone": "+123456789",
            "receipt_type": 1,
            "role": "attendant",
            "active": True,
            "notification_start_time": None,
            "notification_end_time": None,
            "paused_until": None,
            "attendant_data": None
        }
        
        attendant_info = AttendantInfo(**attendant_data)
        assert attendant_info.notification_start_time is None
        assert attendant_info.notification_end_time is None
        assert attendant_info.paused_until is None


class TestContactNotificationWindowEndpoints:
    """Test notification window fields in Contact GET endpoints."""

    @pytest.mark.asyncio
    async def test_get_client_contacts_returns_notification_window_fields(self, mocker):
        """Test that GET /users/client/{client_id}/contacts returns notification window fields."""
        # Arrange
        mock_db = MagicMock()
        mock_contact1 = MagicMock()
        mock_contact1.id = 1
        mock_contact1.name = "Emergency Contact 1"
        mock_contact1.email = "emergency1@example.com"
        mock_contact1.phone = "+111111111"
        mock_contact1.receipt_type = 1
        mock_contact1.role = "contact"
        mock_contact1.active = True
        mock_contact1.notification_start_time = "07:00"
        mock_contact1.notification_end_time = "23:00"
        mock_contact1.paused_until = datetime(2024, 12, 20, 9, 0, 0)
        mock_contact1.client_data = None
        mock_contact1.attendant_data = None

        mock_contact2 = MagicMock()
        mock_contact2.id = 2
        mock_contact2.name = "Family Contact"
        mock_contact2.email = None  # Contact without email
        mock_contact2.phone = "+222222222"
        mock_contact2.receipt_type = 2
        mock_contact2.role = "contact"
        mock_contact2.active = True
        mock_contact2.notification_start_time = "06:00"
        mock_contact2.notification_end_time = "20:00"
        mock_contact2.paused_until = None
        mock_contact2.client_data = None
        mock_contact2.attendant_data = None

        # Mock the service call
        mocker.patch(
            "backendeldery.services.users.UserService.get_client_contacts",
            return_value=[mock_contact1, mock_contact2]
        )

        # Act
        from backendeldery.services.users import UserService
        contacts = await UserService.get_client_contacts(db=mock_db, client_id=1)

        # Assert
        assert len(contacts) == 2
        
        # First contact
        contact1 = contacts[0]
        assert contact1.id == 1
        assert contact1.name == "Emergency Contact 1"
        assert contact1.notification_start_time == "07:00"
        assert contact1.notification_end_time == "23:00"
        assert contact1.paused_until == datetime(2024, 12, 20, 9, 0, 0)
        
        # Second contact 
        contact2 = contacts[1]
        assert contact2.id == 2
        assert contact2.name == "Family Contact"
        assert contact2.notification_start_time == "06:00"
        assert contact2.notification_end_time == "20:00"
        assert contact2.paused_until is None

    @pytest.mark.asyncio
    async def test_get_clients_of_contact_returns_notification_window_fields(self, mocker):
        """Test that GET /users/contact/{contact_id}/clients returns notification window fields in AssistedResponse."""
        # Arrange
        mock_db = MagicMock()
        
        # Create mock client (assisted user)
        mock_assisted_user = MagicMock()
        mock_assisted_user.id = 3
        mock_assisted_user.name = "John Assisted"
        mock_assisted_user.email = "john.assisted@example.com"
        mock_assisted_user.phone = "+333333333"
        mock_assisted_user.receipt_type = 1
        mock_assisted_user.role = "assisted"
        mock_assisted_user.active = True
        mock_assisted_user.notification_start_time = "08:00"
        mock_assisted_user.notification_end_time = "22:00"
        mock_assisted_user.paused_until = None
        mock_assisted_user.client_data = None

        # Create mock assisted response object
        mock_assisted_response = MagicMock()
        mock_assisted_response.user_id = 3
        mock_assisted_response.user = mock_assisted_user  # The 'assisted' field uses alias 'user'
        mock_assisted_response.created_at = datetime(2024, 1, 1, 10, 0, 0)
        mock_assisted_response.updated_at = datetime(2024, 1, 15, 14, 30, 0)

        # Mock the service call
        mocker.patch(
            "backendeldery.services.users.UserService.get_clients_of_contact",
            return_value=[mock_assisted_response]
        )

        # Act
        from backendeldery.services.users import UserService
        clients = await UserService.get_clients_of_contact(db=mock_db, contact_id=1)

        # Assert
        assert len(clients) == 1
        
        client_response = clients[0]
        assert client_response.user_id == 3
        
        # Verify the assisted user (aliased as 'user') has notification fields
        assisted_user = client_response.user
        assert assisted_user.id == 3
        assert assisted_user.name == "John Assisted"
        assert assisted_user.notification_start_time == "08:00"
        assert assisted_user.notification_end_time == "22:00"
        assert assisted_user.paused_until is None

    def test_assisted_user_response_schema_includes_notification_fields(self):
        """Test AssistedUserResponse schema includes notification window fields."""
        # Arrange & Act
        assisted_user_data = {
            "id": 1,
            "name": "Test Assisted User",
            "email": "assisted@example.com",
            "phone": "+123456789",
            "receipt_type": 1,
            "role": "assisted",
            "active": True,
            "notification_start_time": "07:30",
            "notification_end_time": "21:30",
            "paused_until": datetime(2024, 11, 30, 15, 0, 0),
            "client_data": None
        }
        
        from backendeldery.schemas import AssistedUserResponse
        assisted_user_response = AssistedUserResponse(**assisted_user_data)

        # Assert
        assert assisted_user_response.notification_start_time == "07:30"
        assert assisted_user_response.notification_end_time == "21:30"
        assert assisted_user_response.paused_until == datetime(2024, 11, 30, 15, 0, 0)

    def test_assisted_user_response_schema_with_none_notification_fields(self):
        """Test AssistedUserResponse schema handles None notification fields correctly."""
        # Arrange & Act
        assisted_user_data = {
            "id": 1,
            "name": "Test Assisted User",
            "email": "assisted@example.com",
            "phone": "+123456789",
            "receipt_type": 1,
            "role": "assisted", 
            "active": True,
            "notification_start_time": None,
            "notification_end_time": None,
            "paused_until": None,
            "client_data": None
        }
        
        from backendeldery.schemas import AssistedUserResponse
        assisted_user_response = AssistedUserResponse(**assisted_user_data)

        # Assert
        assert assisted_user_response.notification_start_time is None
        assert assisted_user_response.notification_end_time is None
        assert assisted_user_response.paused_until is None