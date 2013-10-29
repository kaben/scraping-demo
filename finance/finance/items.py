# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field

class GoogleSectorItem(Item):
  name = Field()
  catid = Field()
  parent_catid = Field()

class GoogleCompanyItem(Item):
  name = Field()
  stock_symbol = Field()
  sector_catid = Field()

class FinanceItem(Item):
  stock_symbol = Field()
  period_ending = Field()
  duration = Field()
  sales = Field()
  cost_of_goods_sold = Field()
  net_income = Field()
  shareholder_net_income = Field()
  cash_and_equivalents = Field()
  current_assets = Field()
  short_term_debt = Field()
  accounts_payable = Field()
  other_current_liabilities = Field()
  current_liabilities = Field()
  long_term_debt = Field()
  operating_cash_flow = Field()
  capital_expenditures = Field()
  eps = Field()
