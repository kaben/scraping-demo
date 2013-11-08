# This package will contain the spiders of your Scrapy project
#
# Please refer to the documentation for information on how to create and manage
# your spiders.

from finance import settings
from finance.items import FinancialStatementItem, GoogleSectorItem, GoogleCompanyItem, GenericIncomeStatement, GenericBalanceSheet, GenericCashFlowStatement, GenericEpsSummary
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
  if neg_amt_search: return float("-{}".format(neg_amt_search.group(1)))
  else: return float(dollar_string)

def get_multiplier(multiplier_string):
  return float("1{}".format(remove_commas(multiplier_string)))

def get_date(date_string):
  return datetime.strptime(date_string, '%m/%d/%Y')

def convert_date_row(row_data, duration):
  if duration == 2: del row_data[0]
  return [get_date(date_string) for date_string in row_data]

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
  # Convert to a list of row data keyed by row title.
  rows = [(key.replace('.',''), row_data) for (key, row_data) in rows if row_data]
  return rows

def get_fundamentals_row_data(rows):
  row_data_dict = dict(get_row_data(rows))
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



class GenericNasdaqCompanyFinancialsSpider(BaseSpider):
  name = "generic_nasdaq_company_financials"
  fundamentals_fmt = "http://fundamentals.nasdaq.com/nasdaq_fundamentals.asp?NumPeriods={num_periods}&Duration={duration}&documentType={doc_type}&selected={stock}"
  redpage_fmt = "http://fundamentals.nasdaq.com/redpage.asp?selected={stock}&page={page}"

  def start_requests(self):
    company_query = orm.session.query(orm.GoogleCompany)
    durations = (1, 2)
    financials_parsers = (self.parse_income_statement, self.parse_balance_sheet, self.parse_cash_flow_statement)
    for company in company_query:
      stock_symbol = company.stock_symbol
      stock = stock_symbol.split(':')[-1]
      for duration in durations:
        for doc_type, callback in enumerate(financials_parsers):
          formdata = dict(num_periods = 100, duration = duration, doc_type = doc_type+1, stock = stock, stock_symbol = stock_symbol)
          yield Request(self.fundamentals_fmt.format(**formdata), meta = formdata, callback=callback)
      formdata = dict(stock = stock, stock_symbol = stock_symbol, page = 1)
      yield Request(self.redpage_fmt.format(**formdata), meta = formdata, callback=self.parse_eps_summary)


  def parse_fundamentals_rows(self, response):
    hxs = HtmlXPathSelector(response)
    # Get multiplier infor from string of the form "... (values in 000's)".
    multiplier_string_l = hxs.select('//td[@class="bubblemiddle"]/text()').re(r"values in (\d*)'s")
    if multiplier_string_l:
      multiplier_string = multiplier_string_l[0]
      multiplier = get_multiplier(multiplier_string)
      # Get all data rows, which have lots of whitespace formatting.
      rows = hxs.select('//table[@class="ipos"]//tr')
      # Clean up the rows, and extract row titles.
      data_dict = get_fundamentals_row_data(rows)
      return multiplier, data_dict
    else:
      return float(0), dict()

  def get_common_fundamental_data(self, response):
    stock_symbol = response.meta["stock_symbol"]
    duration = response.meta["duration"]
    period_ending_dict = {1:"Quarter Ending:", 2:"Period Ending:"}
    period_ending_key = period_ending_dict[duration]
    mult, data_dict = self.parse_fundamentals_rows(response)
    return stock_symbol, duration, period_ending_key, mult, data_dict

  def handle_generic_statement(self, response, generic_class):
    stock_symbol, duration, period_ending_key, mult, data = self.get_common_fundamental_data(response)
    if data:
      return generic_class(
        stock_symbol = stock_symbol,
        duration = duration,
        period_ending_key = period_ending_key,
        mult = mult,
        data = data,
      )

  def parse_income_statement(self, response):
    item = self.handle_generic_statement(response, GenericIncomeStatement)
    if item: yield item
  def parse_balance_sheet(self, response):
    item = self.handle_generic_statement(response, GenericBalanceSheet)
    if item: yield item
  def parse_cash_flow_statement(self, response):
    item = self.handle_generic_statement(response, GenericCashFlowStatement)
    if item: yield item

  def parse_eps_summary(self, response):
    stock_symbol = response.meta["stock_symbol"]
    page = response.meta["page"]
    hxs = HtmlXPathSelector(response)
    # Get all data rows, which have lots of whitespace formatting.
    rows = hxs.select('//table[@class="ipos"]//tr')
    # Clean up the rows, and extract row titles.
    data_rows = get_row_data(rows)
    # Extract EPS data from rows.
    data_rows = [row for (key, row) in data_rows if key == u"EPS"]
    data_rows = [entry.split(u"\xa0") for row in data_rows for entry in row]
    # Keep all EPS quarterly data, identified by date of period end.
    data_rows = [(row[0], row[1]) for row in data_rows if 2 == len(row)]
    # Convert EPS to number, and date string to date.
    data_rows = [(float(eps), datetime.strptime(date, "(%m/%d/%Y)")) for eps, date in data_rows]
    return_items = [
      GenericEpsSummary(
        stock_symbol = stock_symbol,
        duration = 1,
        period_ending = row[1],
        eps = row[0],
      )
      for row in data_rows
    ]
    if return_items:
      formdata = response.meta.copy()
      formdata["page"] = page+1
      return_items.append(Request(self.redpage_fmt.format(**formdata), meta=formdata, callback=self.parse_eps_summary))
    return return_items

