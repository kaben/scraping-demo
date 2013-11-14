# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

from finance.items import FinancialStatementItem, GoogleSectorItem, GoogleCompanyItem, GenericFinancialStatement, GenericEpsSummary, GoogleHistoricPriceItem
from finance.models import orm

from scrapy import log
import pymongo

import datetime

class PipelineBaseORM(object):
  def __init__(self):
    self.orm = orm
    self.mongo_client = pymongo.MongoClient()
    self.mongo_db = self.mongo_client.finance_db2

  def change_and_note_attributes(self, thing, **keyword_args):
    for key, arg in keyword_args.iteritems():
      log.msg(u"Setting {}='{}' in {}".format(key, arg, thing))
      setattr(thing, key, arg)

  def update_attrs_with_notes(self, thing, **kw):
    changed_keyword_args = dict((k, v) for k, v in kw.iteritems() if getattr(thing, k)!=v)
    self.change_and_note_attributes(thing, **changed_keyword_args)


class FinanceDbPipeline(PipelineBaseORM):
  def __init__(self, *l, **d):
    super(FinanceDbPipeline, self).__init__(*l, **d)
    
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

    elif type(item) == FinancialStatementItem:
      stock_symbol = item["stock_symbol"]
      duration = item["duration"]
      period_ending = item["period_ending"]
      company = self.orm.get_or_create(self.orm.GoogleCompany, stock_symbol=stock_symbol)
      financial_statement = self.orm.get_or_create(self.orm.CompanyFinancials, company=company, period_ending=period_ending, duration=duration)
      # There's no stock_symbol attribute in the database table; there's a
      # related company instead; so we need to remove the attribute from a copy
      # of the item.
      del item["stock_symbol"]
      self.update_attrs_with_notes(financial_statement, **item)
      self.orm.session.commit()

    elif type(item) == GenericFinancialStatement:
      self.mongo_db.financials.insert(dict(item_dict))

    elif type(item) == GenericEpsSummary:
      self.mongo_db.earnings.insert(dict(item_dict))

    elif type(item) == GoogleHistoricPriceItem:
      price_date = item["date"]
      if type(price_date) == datetime.datetime:
        stock_symbol = item["stock_symbol"]
        #if self.last_stock_symbol != stock_symbol:
        #  self.orm.session.commit()
        #  self.last_stock_symbol = stock_symbol
        price_open = item["open"]
        high = item["high"]
        low = item["low"]
        price_close = item["close"]
        volume = item["volume"]
        company = self.orm.get_or_create(self.orm.GoogleCompany, stock_symbol=stock_symbol)
        query_dict = dict(company=company, date=price_date)
        update_dict = dict(item)
        del update_dict["date"]
        del update_dict["stock_symbol"]
        try:
          historic_price = self.orm.get_or_create_and_update(self.orm.GoogleHistoricPrice, query_dict, update_dict)
          self.orm.session.commit()
        except:
          self.orm.session.rollback()

    else: log.msg(u"unknown item type {} for item {}".format(type(item), item), level=log.WARNING)

    return item
