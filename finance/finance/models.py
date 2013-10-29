
from settings import SQLALCHEMY_URL
from irrealis_orm import ORM
import sqlalchemy as sa
from sqlalchemy.orm import relationship

orm_defs = dict(
  GoogleSector = dict(
    __tablename__ = "google_sectors",
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
    sector = relationship(
      "GoogleSector",
      primaryjoin = "google_companies.c.sector_id==google_sectors.c.id",
    ),
    industry = relationship(
      "GoogleSector",
      primaryjoin = "google_companies.c.industry_id==google_sectors.c.id",
    ),
  ),
)
orm = ORM(orm_defs, SQLALCHEMY_URL)

