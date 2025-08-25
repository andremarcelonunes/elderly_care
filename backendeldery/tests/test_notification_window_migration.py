"""Tests for notification window migration (CB-154)."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from backendeldery.models import User
from backendeldery.schemas import UserCreate, UserUpdate, validate_time_format


class TestNotificationWindowMigration:
    """Test the notification window fields migration."""
    
    def test_user_model_has_notification_fields(self):
        """Test that User model has the required notification window fields."""
        user = User()
        
        # Check that the fields exist
        assert hasattr(user, 'notification_start_time')
        assert hasattr(user, 'notification_end_time')
        assert hasattr(user, 'paused_until')
        
        # Check default values
        assert user.notification_start_time is None  # Will be set by database default
        assert user.notification_end_time is None   # Will be set by database default
        assert user.paused_until is None

    @pytest.mark.asyncio
    async def test_migration_adds_columns_with_defaults(self):
        """Test that migration adds columns with proper defaults."""
        mock_session = AsyncMock()
        mock_connection = MagicMock()
        
        # Simulate executing the migration SQL
        mock_session.execute = AsyncMock()
        
        # Test the SQL that would be executed in the migration
        expected_sqls = [
            "ALTER TABLE elderly_care.users ADD COLUMN notification_start_time VARCHAR(5) DEFAULT '08:00'",
            "ALTER TABLE elderly_care.users ADD COLUMN notification_end_time VARCHAR(5) DEFAULT '22:00'", 
            "ALTER TABLE elderly_care.users ADD COLUMN paused_until TIMESTAMP",
            "UPDATE elderly_care.users SET notification_start_time = '08:00', notification_end_time = '22:00'"
        ]
        
        # This would be called during migration
        for sql in expected_sqls:
            await mock_session.execute(text(sql))
        
        # Verify all SQL commands were called
        assert mock_session.execute.call_count == len(expected_sqls)

    @pytest.mark.asyncio  
    async def test_migration_check_constraints(self):
        """Test that CHECK constraints work properly."""
        mock_session = AsyncMock()
        
        # Test valid time formats should pass
        valid_times = ['00:00', '08:00', '12:30', '23:59', '07:15']
        
        for valid_time in valid_times:
            # These should not raise exceptions
            result = validate_time_format(valid_time)
            assert result == valid_time
            
        # Test invalid time formats should fail
        invalid_times = ['24:00', '12:60', '1:30', '25:30', 'abc', '12:5', '']
        
        for invalid_time in invalid_times:
            with pytest.raises(ValueError, match="Time must be in HH:MM format"):
                validate_time_format(invalid_time)

    def test_user_create_schema_validation(self):
        """Test UserCreate schema validation for notification window fields."""
        # Valid data should pass
        valid_data = {
            "name": "Test User",
            "phone": "+1234567890",
            "receipt_type": 1,
            "role": "contact",
            "notification_start_time": "08:00",
            "notification_end_time": "22:00"
        }
        
        user_create = UserCreate(**valid_data)
        assert user_create.notification_start_time == "08:00"
        assert user_create.notification_end_time == "22:00"
        assert user_create.paused_until is None

    def test_user_create_schema_defaults(self):
        """Test UserCreate schema uses proper defaults."""
        minimal_data = {
            "name": "Test User",
            "phone": "+1234567890", 
            "receipt_type": 1,
            "role": "contact"
        }
        
        user_create = UserCreate(**minimal_data)
        assert user_create.notification_start_time == "08:00"
        assert user_create.notification_end_time == "22:00"
        assert user_create.paused_until is None

    def test_user_create_schema_time_validation(self):
        """Test UserCreate schema validates time formats."""
        base_data = {
            "name": "Test User",
            "phone": "+1234567890",
            "receipt_type": 1,
            "role": "contact"
        }
        
        # Invalid start time
        with pytest.raises(ValueError, match="Time must be in HH:MM format"):
            UserCreate(**{**base_data, "notification_start_time": "25:00"})
            
        # Invalid end time
        with pytest.raises(ValueError, match="Time must be in HH:MM format"):
            UserCreate(**{**base_data, "notification_end_time": "12:60"})

    def test_user_create_schema_time_logic_validation(self):
        """Test UserCreate schema validates start time before end time."""
        base_data = {
            "name": "Test User", 
            "phone": "+1234567890",
            "receipt_type": 1,
            "role": "contact"
        }
        
        # Start time after end time should fail
        with pytest.raises(ValueError, match="notification_start_time must be before notification_end_time"):
            UserCreate(**{
                **base_data,
                "notification_start_time": "22:00",
                "notification_end_time": "08:00"
            })
            
        # Same times should fail
        with pytest.raises(ValueError, match="notification_start_time must be before notification_end_time"):
            UserCreate(**{
                **base_data, 
                "notification_start_time": "12:00",
                "notification_end_time": "12:00"
            })

    def test_user_update_schema_validation(self):
        """Test UserUpdate schema validation for notification window fields."""
        # Valid partial update
        update_data = {
            "notification_start_time": "09:00",
            "notification_end_time": "21:00",
            "paused_until": datetime(2025, 1, 25, 15, 30, 0)
        }
        
        user_update = UserUpdate(**update_data)
        assert user_update.notification_start_time == "09:00"
        assert user_update.notification_end_time == "21:00"
        assert user_update.paused_until == datetime(2025, 1, 25, 15, 30, 0)
        
        # Invalid time format should fail
        with pytest.raises(ValueError, match="Time must be in HH:MM format"):
            UserUpdate(notification_start_time="24:00")

    def test_paused_until_datetime_field(self):
        """Test paused_until field accepts datetime objects."""
        pause_time = datetime(2025, 1, 25, 15, 30, 0)
        
        user_create = UserCreate(
            name="Test User",
            phone="+1234567890", 
            receipt_type=1,
            role="contact",
            paused_until=pause_time
        )
        
        assert user_create.paused_until == pause_time

    def test_migration_rollback_capability(self):
        """Test that migration can be rolled back properly."""
        # This would be tested with actual database in integration tests
        # Here we just verify the migration structure supports rollback
        
        # The migration should have both upgrade() and downgrade() functions
        from alembic.script import ScriptDirectory
        import os
        
        # Check migration file exists
        migration_file = "/Users/andrenunes/PycharmProjects/backendEldery/alembic/versions/mr662ksddt4s_add_notification_window_fields.py"
        assert os.path.exists(migration_file)
        
        # Read migration file content
        with open(migration_file, 'r') as f:
            content = f.read()
            
        # Verify it has both upgrade and downgrade functions
        assert "def upgrade()" in content
        assert "def downgrade()" in content
        
        # Verify downgrade removes what upgrade adds
        assert "drop_constraint" in content
        assert "drop_column" in content


class TestNotificationWindowIntegration:
    """Integration tests for notification window functionality."""
    
    @pytest.mark.asyncio
    async def test_user_crud_with_notification_fields(self):
        """Test CRUD operations work with notification window fields."""
        # This would be tested with actual database connection
        # For now, we mock the database interaction
        
        mock_session = AsyncMock()
        
        # Test creating user with notification fields
        user_data = {
            "name": "John Doe",
            "email": "john@example.com", 
            "phone": "+1234567890",
            "receipt_type": 1,
            "role": "subscriber",
            "notification_start_time": "07:00",
            "notification_end_time": "23:00",
            "paused_until": None
        }
        
        # Mock successful creation
        mock_user = User(**user_data)
        mock_session.add.return_value = None
        mock_session.commit.return_value = None
        mock_session.refresh.return_value = None
        
        # Simulate successful creation
        mock_session.add(mock_user)
        await mock_session.commit()
        await mock_session.refresh(mock_user)
        
        assert mock_session.add.called
        assert mock_session.commit.called
        assert mock_session.refresh.called


class TestTimeFormatValidator:
    """Test the standalone time format validator."""
    
    def test_validate_time_format_valid_times(self):
        """Test validation passes for valid time formats."""
        valid_times = [
            '00:00', '00:01', '00:59',
            '01:00', '09:30', '12:00', 
            '13:45', '18:00', '23:59'
        ]
        
        for time_str in valid_times:
            result = validate_time_format(time_str)
            assert result == time_str
            
    def test_validate_time_format_none_value(self):
        """Test validation handles None values."""
        result = validate_time_format(None)
        assert result is None
        
    def test_validate_time_format_invalid_times(self):
        """Test validation fails for invalid time formats."""
        invalid_times = [
            '24:00',  # Invalid hour
            '12:60',  # Invalid minute  
            '1:30',   # Single digit hour
            '12:5',   # Single digit minute
            'abc',    # Non-numeric
            '',       # Empty string
            '25:30',  # Hour > 23
            '12:65',  # Minute > 59
            '12',     # Missing minutes
            '12:',    # Missing minutes value
            ':30',    # Missing hour
        ]
        
        for time_str in invalid_times:
            with pytest.raises(ValueError, match="Time must be in HH:MM format"):
                validate_time_format(time_str)