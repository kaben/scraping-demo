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

class FinancialStatementItem(Item):
  stock_symbol = Field()
  duration = Field()
  period_ending = Field()

  # Data from income statement:
  income_statement_multiplier = Field()
  sales = Field()
  cost_of_goods_sold = Field()
  net_income = Field()
  shareholder_net_income = Field()

  # Data from balance sheet:
  balance_sheet_multiplier = Field()
  cash_and_equivalents = Field()
  current_assets = Field()
  short_term_debt = Field()
  accounts_payable = Field()
  other_current_liabilities = Field()
  current_liabilities = Field()
  long_term_debt = Field()

  # Data from cash flow statement:
  cash_flow_statement_multiplier = Field()
  operating_cash_flow = Field()
  capital_expenditures = Field()

  # Data from revenue / EPS summary:
  eps = Field()

class GenericFinancialStatement(Item):
  stock_symbol = Field()
  duration = Field()
  period_ending_key = Field()
  mult = Field()
  data = Field()

class GenericEpsSummary(Item):
  stock_symbol = Field()
  duration = Field()
  period_ending = Field()
  eps = Field()

class GoogleHistoricPriceItem(Item):
  stock_symbol = Field()
  date = Field()
  open = Field()
  high = Field()
  low = Field()
  close = Field()
  volume = Field()

