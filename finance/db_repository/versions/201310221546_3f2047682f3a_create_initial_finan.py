"""Create initial finance tables.

Revision ID: 3f2047682f3a
Revises: None
Create Date: 2013-10-22 15:46:10.179978

"""

# revision identifiers, used by Alembic.
revision = '3f2047682f3a'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
  op.create_table(
    "google_sectors",
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("catid", sa.String(64)),
    sa.Column("name", sa.String(512)),
  )
  op.create_table(
    "google_sectors_assoc",
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("parent_id", sa.Integer, sa.ForeignKey("google_sectors.id")),
    sa.Column("child_id", sa.Integer, sa.ForeignKey("google_sectors.id")),
  )

def downgrade():
  op.drop_table("google_sectors_assoc")
  op.drop_table("google_sectors")

