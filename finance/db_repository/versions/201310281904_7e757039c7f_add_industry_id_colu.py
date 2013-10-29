"""Add industry_id column to google_companies table.

Revision ID: 7e757039c7f
Revises: 4960b01461da
Create Date: 2013-10-28 19:04:42.641885

"""

# revision identifiers, used by Alembic.
revision = '7e757039c7f'
down_revision = '4960b01461da'

from alembic import op
import sqlalchemy as sa


def upgrade():
  op.add_column("google_companies", sa.Column("industry_id", sa.Integer, sa.ForeignKey("google_sectors.id")))


def downgrade():
  op.drop_column("google_companies", "industry_id")
