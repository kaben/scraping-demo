
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
      primaryjoin = "GoogleSector.id==google_sectors_assoc.c.parent_id",
      secondaryjoin = "GoogleSector.id==google_sectors_assoc.c.child_id",
      backref="parents",
    ),
  ),
  GoogleCompany = dict(
    __tablename__ = "google_companies",
    sector = relationship(
      "GoogleSector",
      primaryjoin = "GoogleCompany.sector_id==GoogleSector.id",
    ),
    industry = relationship(
      "GoogleSector",
      primaryjoin = "GoogleCompany.industry_id==GoogleSector.id",
    ),
)
orm = ORM(orm_defs, SQLALCHEMY_URL)

