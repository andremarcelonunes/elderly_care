"""add notification window fields

Revision ID: mr662ksddt4s
Revises: c310f66bd748
Create Date: 2025-01-25 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'mr662ksddt4s'
down_revision: Union[str, None] = 'c310f66bd748'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add notification window fields to users table."""
    
    # Add the new columns
    op.add_column('users', sa.Column('notification_start_time', sa.String(5), 
                                     nullable=True, server_default='08:00'), schema='elderly_care')
    op.add_column('users', sa.Column('notification_end_time', sa.String(5), 
                                     nullable=True, server_default='22:00'), schema='elderly_care')
    op.add_column('users', sa.Column('paused_until', sa.DateTime(), 
                                     nullable=True), schema='elderly_care')
    
    # Add CHECK constraints for strict HH:MM format validation (exactly 2 digits)
    op.create_check_constraint(
        'ck_users_notification_start_time_format',
        'users',
        "notification_start_time ~ '^([0-1][0-9]|2[0-3]):[0-5][0-9]$'",
        schema='elderly_care'
    )
    
    op.create_check_constraint(
        'ck_users_notification_end_time_format',
        'users', 
        "notification_end_time ~ '^([0-1][0-9]|2[0-3]):[0-5][0-9]$'",
        schema='elderly_care'
    )
    
    # Update existing users with default values
    op.execute(
        "UPDATE elderly_care.users SET "
        "notification_start_time = '08:00', "
        "notification_end_time = '22:00' "
        "WHERE notification_start_time IS NULL OR notification_end_time IS NULL"
    )


def downgrade() -> None:
    """Remove notification window fields from users table."""
    
    # Drop CHECK constraints first
    op.drop_constraint('ck_users_notification_start_time_format', 'users', 
                       schema='elderly_care', type_='check')
    op.drop_constraint('ck_users_notification_end_time_format', 'users', 
                       schema='elderly_care', type_='check')
    
    # Drop the columns
    op.drop_column('users', 'paused_until', schema='elderly_care')
    op.drop_column('users', 'notification_end_time', schema='elderly_care')
    op.drop_column('users', 'notification_start_time', schema='elderly_care')