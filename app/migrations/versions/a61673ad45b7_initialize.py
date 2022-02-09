"""initialize

Revision ID: a61673ad45b7
Revises: 
Create Date: 2022-02-08 14:31:57.632214

"""

from alembic import op
import sqlalchemy as sa
# revision identifiers, used by Alembic.
from sqlalchemy import Integer, DateTime, func, Enum, String, Boolean

revision = 'a61673ad45b7'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('users',
                    sa.Column('id', Integer, primary_key=True, index=True),
                    sa.Column('created_at', DateTime, nullable=False, default=func.utc_timestamp()),
                    sa.Column('updated_at', DateTime, nullable=False, default=func.utc_timestamp(), onupdate=func.utc_timestamp()),
                    sa.Column('status', Enum("active", "deleted", "blocked"), default="active"),
                    sa.Column('email', String(length=255), nullable=True),
                    sa.Column('pw', String(length=2000), nullable=True),
                    sa.Column('name', String(length=255), nullable=True),
                    sa.Column('phone_number', String(length=20), nullable=True, unique=True),
                    sa.Column('profile_img', String(length=1000), nullable=True),
                    sa.Column('sns_type', Enum("FB", "G", "K"), nullable=True),
                    sa.Column('marketing_agree', Boolean, nullable=True, default=True))


def downgrade():
    op.drop_table('users')
