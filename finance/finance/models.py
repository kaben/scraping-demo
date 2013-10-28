
from settings import SQLALCHEMY_URL
from irrealis_orm import ORM
import sqlalchemy as sa
from sqlalchemy.orm import relationship

orm_defs = dict(
  GoogleSectorAssoc = dict(
    __tablename__ = "google_sectors_assoc",
    id = sa.Column("id", sa.Integer, primary_key=True),
    parent_id = sa.Column("parent_id", sa.Integer, sa.ForeignKey("google_sectors.id")),
    child_id = sa.Column("child_id", sa.Integer, sa.ForeignKey("google_sectors.id")),
  ),
  GoogleSector = dict(
    __tablename__ = "google_sectors",
    id = sa.Column("id", sa.Integer, primary_key=True),
    catid = sa.Column("catid", sa.String(64)),
    name = sa.Column("name", sa.String(512)),
    children = relationship(
      "GoogleSector",
      secondary = "google_sectors_assoc",
      primaryjoin = "google_sectors.c.id==google_sectors_assoc.c.parent_id",
      secondaryjoin = "google_sectors.c.id==google_sectors_assoc.c.child_id",
      backref="parents",
    ),
  ),
  GoogleCompany = dict(
    __tablename__ = "google_companies",
    id = sa.Column("id", sa.Integer, primary_key=True),
    stock_symbol = sa.Column("stock_symbol", sa.String(64)),
    name = sa.Column("name", sa.String(512)),
    sector_id = sa.Column("sector_id", sa.Integer, sa.ForeignKey("google_sectors.id")),
    sector = relationship("GoogleSector"),
  ),
)
orm = ORM(orm_defs, SQLALCHEMY_URL, deferred_reflection = False)

