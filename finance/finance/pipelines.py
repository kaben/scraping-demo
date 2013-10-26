# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

from finance.items import GoogleSectorItem, GoogleCompanyItem
from finance.models import orm

from scrapy import log


class PipelineBaseORM(object):
  def __init__(self):
    self.orm = orm

  def change_and_note_attributes(self, thing, **keyword_args):
    for key, arg in keyword_args.iteritems():
      log.msg(u"Setting {}='{}' in {}".format(key, arg, thing))
      setattr(thing, key, arg)

  def update_attrs_with_notes(self, thing, **kw):
    changed_keyword_args = dict((k, v) for k, v in kw.iteritems() if getattr(thing, k)!=v)
    self.change_and_note_attributes(thing, **changed_keyword_args)


class FinanceDbPipeline(PipelineBaseORM):
  def process_item(self, item, spider):
    if type(item) == GoogleCompanyItem:
      stock_symbol = item["stock_symbol"]
      name = item["name"]
      sector_catid = item["sector_catid"]
      sector = self.orm.get_or_create(self.orm.GoogleSector, catid=sector_catid)
      company = self.orm.get_or_create(self.orm.GoogleCompany, stock_symbol=stock_symbol)
      self.update_attrs_with_notes(company, name=name, sector=sector)
      self.orm.session.commit()

    elif type(item) == GoogleSectorItem:
      catid = item["catid"]
      sector = self.orm.get_or_create(self.orm.GoogleSector, catid=catid)
      if "name" in item: self.update_attrs_with_notes(sector, name=item["name"])
      if "parent_catid" in item:
        parent_sector = self.orm.get_or_create(self.orm.GoogleSector, catid=item["parent_catid"])
        if not parent_sector in sector.parents:
          log.msg(u"Adding parent {} to child {}".format(parent_sector, sector))
          sector.parents.append(parent_sector)
      self.orm.session.commit()

    else: log.msg(u"unknown item type {} for item {}".format(type(item), item), level=log.WARNING)

    return item