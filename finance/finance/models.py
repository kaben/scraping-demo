
from settings import SQLALCHEMY_URL
from irrealis_orm import ORM
from sqlalchemy.orm import relationship

orm_defs = dict(
    GoogleSectorAssoc = dict(
      __tablename__ = "google_sectors_assoc",
    ),
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
)
orm = ORM(orm_defs, SQLALCHEMY_URL)

