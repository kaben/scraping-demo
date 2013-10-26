"""Add companies table.

Revision ID: 4960b01461da
Revises: 3f2047682f3a
Create Date: 2013-10-24 16:45:14.374386

"""

# revision identifiers, used by Alembic.
revision = '4960b01461da'
down_revision = '3f2047682f3a'

from alembic import op
import sqlalchemy as sa


def upgrade():
  op.create_table(
    "google_companies",
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("stock_symbol", sa.String),
    sa.Column("name", sa.String),
    sa.Column("sector_id", sa.Integer, sa.ForeignKey("google_sectors.id")),
  )


def downgrade():
  op.drop_table("google_companies")
