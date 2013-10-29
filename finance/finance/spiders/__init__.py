# This package will contain the spiders of your Scrapy project
#
# Please refer to the documentation for information on how to create and manage
# your spiders.

from finance import settings
from finance.items import FinancialStatementItem, GoogleCompanyItem, GoogleSectorItem
from finance.models import orm

from cdecimal import Decimal

from scrapy.http import Request, FormRequest
from scrapy.selector import HtmlXPathSelector
from scrapy.spider import BaseSpider
from scrapy import log

from datetime import datetime
from urlparse import parse_qs, urlparse
import re


def get_querydict(url):
  return parse_qs(urlparse(url).query)

def get_catid_from_url(url):
  d = get_querydict(url)
  if 'catid' in d: return d['catid'][0].split("us-")[-1]
  else: return None

def get_stock_symbol_from_url(url):
  d = get_querydict(url)
  if 'q' in d: return d['q'][0]
  else: return None

def remove_commas(string):
  return string.replace(",","")

def remove_dollars(string):
  return string.replace("$","")

neg_amt_re = re.compile("\((\d+)\)")
def get_decimal_from_dollars(dollar_string):
  dollar_string = remove_dollars(remove_commas(dollar_string))
  neg_amt_search = neg_amt_re.search(dollar_string)
  if neg_amt_search: return Decimal("-{}".format(neg_amt_search.group(1)))
  else: return Decimal(dollar_string)

def get_multiplier(multiplier_string):
  return Decimal("1{}".format(remove_commas(multiplier_string)))

def get_date(date_string):
  return datetime.strptime(date_string, '%m/%d/%Y').date()

def convert_date_row(row_data):
  return [get_date(date_string) for date_string in row_data[1:]]

def convert_dollar_row(row_data, multiplier):
  return [multiplier*get_decimal_from_dollars(dollar_string) for dollar_string in row_data]

def get_row_data(rows):
  # Row data has lots of whitespace we don't need; remove.
  rows = [[datum.strip() for datum in row.select('.//*/text()').extract()] for row in rows]
  # Removing whitespace left lots of empty data; remove.
  rows = [[datum for datum in row if datum] for row in rows]
  # On Nasdaq fundamentals, each row begins with a row title; get titles and
  # remaining data, if any.
  rows = [(row[0], row[1:]) for row in rows if row]
  # Convert to a dictionary of row data, keyed by row title.
  row_data_dict = dict((key, row_data) for (key, row_data) in rows if row_data)
  return row_data_dict


class GoogleFinanceSectorSpider(BaseSpider):
  name = "google_finance_sectors"
  start_urls = ["https://www.google.com/finance"]

  def process_sectors(self, sectors, parent_catid):
    items = list()
    requests = list()
    names = sectors.select('text()').extract()
    links = sectors.select('@href').extract()
    catids = [get_catid_from_url(link) for link in links]
    for name, link, catid in zip(names, links, catids):
      # The first time we scrape the sector's name, the name is often
      # abbreviated, so we discard it. But then we request a visit to a page
      # dedicated to that sector, where we can scrape its full, unabbreviated
      # name. Then we can update the name in the database.
      items.append(GoogleSectorItem(catid=catid, parent_catid=parent_catid))
      requests.append(Request("https://www.google.com{}".format(link), callback=self.parse_sector_page))
    return items, requests

  def process_companies(self, companies, sector_catid):
    items = list()
    names = companies.select('text()').extract()
    links = companies.select('@href').extract()
    stock_symbols = [get_stock_symbol_from_url(link) for link in links]
    for name, link, stock_symbol in zip(names, links, stock_symbols):
      items.append(GoogleCompanyItem(name=name, stock_symbol=stock_symbol, sector_catid=sector_catid))
    return items

  def parse(self, response):
    hxs = HtmlXPathSelector(response)
    # Scrape all child sectors on page.
    sectors = hxs.select('//div[@id="secperf"]//a')
    items, requests = self.process_sectors(sectors, parent_catid=None)
    return items + requests

  def parse_sector_page(self, response):
    items = list()
    requests = list()
    hxs = HtmlXPathSelector(response)
    # Scrape parent's catid and full, unabbreviated name.
    parent_catid = get_catid_from_url(response.request.url)
    page_title = hxs.select("//title/text()").extract()[0]

    parent_name = u" - ".join(page_title.split(u" - ")[:-1])
    items.append(GoogleSectorItem(name=parent_name, catid=parent_catid))

    if settings.SCRAPE_COMPANIES_FROM_SECTORS:
      # Scrape all company names on page.
      companies = hxs.select('//table[@id="main"]//td[@align="right"]/a')
      items.extend(self.process_companies(companies, parent_catid))
      # Scrape link to next page for sector.
      next_page_link = hxs.select('//td[@class="nav_b"]//a/@href').extract()
      if next_page_link:
        requests.append(Request(next_page_link[0], callback=self.parse_next_sector_page))

    # Scrape all child sectors on page.
    sectors = hxs.select('//div[@class="sfe-section"]//a')
    child_items, child_requests = self.process_sectors(sectors, parent_catid)
    return items + child_items + requests + child_requests

  def parse_next_sector_page(self, response):
    items = list()
    requests = list()
    hxs = HtmlXPathSelector(response)
    # Scrape parent's catid.
    parent_catid = get_catid_from_url(response.request.url)
    # Scrape all company names on page.
    companies = hxs.select('//table[@id="main"]//td[@align="right"]/a')
    items.extend(self.process_companies(companies, parent_catid))
    # Scrape link to next page for sector.
    next_page_link = hxs.select('//td[@class="nav_b"]//a/@href').extract()
    if next_page_link:
      requests.append(Request(next_page_link[0], callback=self.parse_next_sector_page))
    return items + requests


class NasdaqCompanyFinancialsSpider(BaseSpider):
  name = "nasdaq_company_financials"
  fundamentals_fmt = "http://fundamentals.nasdaq.com/nasdaq_fundamentals.asp?NumPeriods={num_periods}&Duration={duration}&documentType={doc_type}&selected={stock}"
  redpage_fmt = "http://fundamentals.nasdaq.com/redpage.asp?selected={stock}&page={page}"

  def start_requests(self):
    #company_query = orm.session.query(orm.GoogleCompany)
    company_query = orm.session.query(orm.GoogleCompany).filter(orm.GoogleCompany.stock_symbol.like("%:AAPL%"))
    #durations = (1, 2)
    durations = (2,)
    financials_parsers = (self.parse_income_statement, self.parse_balance_sheet, self.parse_cash_flow_statement)
    #financials_parsers = (self.parse_income_statement, self.parse_balance_sheet)
    for company in company_query:
      stock_symbol = company.stock_symbol
      stock = stock_symbol.split(':')[-1]
      for duration in durations:
        for doc_type, callback in enumerate(financials_parsers):
          formdata = dict(num_periods = 100, duration = duration, doc_type = doc_type+1, stock = stock, stock_symbol = stock_symbol)
          yield Request(self.fundamentals_fmt.format(**formdata), meta = formdata, callback=callback)
      formdata = dict(selected = stock, page = 1, stock_symbol = stock_symbol)
      #yield Request(self.redpage_fmt.format(**formdata), meta = formdata, callback=self.parse_redpage)

  def parse_data_rows(self, response):
    hxs = HtmlXPathSelector(response)
    # Get multiplier infor from string of the form "... (values in 000's)".
    multiplier_string = hxs.select('//td[@class="bubblemiddle"]/text()').re(r"values in (\d*)'s")[0]
    multiplier = get_multiplier(multiplier_string)
    # Get all data rows, which have lots of whitespace formatting.
    rows = hxs.select('//table[@class="ipos"]//tr')
    # Clean up the rows, and extract row titles.
    data_dict = get_row_data(rows)
    return multiplier, data_dict

  def parse_income_statement(self, response):
    stock_symbol = response.meta["stock_symbol"]
    duration = response.meta["duration"]
    mult, data_dict = self.parse_data_rows(response)

    income_statement_items = [
      FinancialStatementItem(
        stock_symbol = stock_symbol,
        duration = duration,
        period_ending = row[0],

        income_statement_multiplier = mult,
        sales = row[1],
        cost_of_goods_sold = row[2],
        net_income = row[3],
        shareholder_net_income = row[4],
      )
      for row in zip(
        convert_date_row(data_dict["Period Ending:"]),

        convert_dollar_row(data_dict["Total Revenue"], mult),
        convert_dollar_row(data_dict["Cost of Revenue"], mult),
        convert_dollar_row(data_dict["Net Income"], mult),
        convert_dollar_row(data_dict["Net Income Applicable to"][1:], mult),
      )
    ]

    print "parse_income_statement:"
    for income_statement_item in income_statement_items:
      print "income_statement_item:"
      print income_statement_item

  def parse_balance_sheet(self, response):
    stock_symbol = response.meta["stock_symbol"]
    duration = response.meta["duration"]
    mult, data_dict = self.parse_data_rows(response)

    balance_sheet_items = [
      FinancialStatementItem(
        stock_symbol = stock_symbol,
        duration = duration,
        period_ending = row[0],

        balance_sheet_multiplier = mult,
        cash_and_equivalents = row[1],
        current_assets = row[2],
        short_term_debt = row[3],
        accounts_payable = row[4],
        other_current_liabilities = row[5],
        current_liabilities = row[6],
        long_term_debt = row[7],
      )
      for row in zip(
        convert_date_row(data_dict["Period Ending:"]),

        convert_dollar_row(data_dict["Cash and Cash Equivalents"], mult),
        convert_dollar_row(data_dict["Total Current Assets"], mult),
        convert_dollar_row(data_dict["Short Term Debt/Current Portion of Long Term Debt"], mult),
        convert_dollar_row(data_dict["Accounts Payable"], mult),
        convert_dollar_row(data_dict["Other Current Liabilities"], mult),
        convert_dollar_row(data_dict["Total Current Liabilities"], mult),
        convert_dollar_row(data_dict["Long Term Debt"], mult),
      )
    ]

    print "parse_balance_sheet:"
    for balance_sheet_item in balance_sheet_items:
      print "balance_sheet_items:"
      print balance_sheet_item

  def parse_cash_flow_statement(self, response):
    stock_symbol = response.meta["stock_symbol"]
    duration = response.meta["duration"]
    mult, data_dict = self.parse_data_rows(response)

    cash_flow_statement_items = [
      FinancialStatementItem(
        stock_symbol = stock_symbol,
        duration = duration,
        period_ending = row[0],

        cash_flow_statement_multiplier = mult,
        operating_cash_flow = row[1],
        capital_expenditures = row[2],
      )
      for row in zip(
        convert_date_row(data_dict["Period Ending:"]),

        convert_dollar_row(data_dict["Net Cash Flow-Operating"], mult),
        convert_dollar_row(data_dict["Capital Expenditures"], mult),
      )
    ]

    print "parse_cash_flow_statement:"
    for cash_flow_statement_item in cash_flow_statement_items:
      print "cash_flow_statement_items:"
      print cash_flow_statement_item

  def parse_eps(self, response):
    print "parse_eps:", response, response.meta

