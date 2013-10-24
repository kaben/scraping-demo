# This package will contain the spiders of your Scrapy project
#
# Please refer to the documentation for information on how to create and manage
# your spiders.

from finance.items import GoogleCompanyItem, GoogleSectorItem

from scrapy.http import Request
from scrapy.selector import HtmlXPathSelector
from scrapy.spider import BaseSpider

from urlparse import parse_qs, urlparse


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


class GoogleFinanceNameSpider(BaseSpider):
  name = "google_finance_names"
  start_urls = ["https://www.google.com/finance"]

  def process_sectors(self, sectors, parent_catid):
    names = sectors.select('text()').extract()
    links = sectors.select('@href').extract()
    catids = [get_catid_from_url(link) for link in links]
    for name, link, catid in zip(names, links, catids):
      # The first time we scrape the sector's name, the name is often
      # abbreviated. But then we request a visit to a page dedicated to that
      # sector, where we can scrape its full, unabbreviated name.
      yield GoogleSectorItem(name=name, catid=catid, parent_catid=parent_catid)
      yield Request("https://www.google.com{}".format(link), callback=self.parse_sector_page)

  def process_companies(self, companies, sector_catid):
    names = companies.select('text()').extract()
    links = companies.select('@href').extract()
    stock_symbols = [get_stock_symbol_from_url(link) for link in links]
    for name, link, stock_symbol in zip(names, links, stock_symbols):
      yield GoogleCompanyItem(name=name, stock_symbol=stock_symbol, sector_catid=sector_catid)

  def parse(self, response):
    hxs = HtmlXPathSelector(response)
    # Scrape all child sectors on page.
    sectors = hxs.select('//div[@id="secperf"]//a')
    return self.process_sectors(sectors, parent_catid=None)

  def parse_sector_page(self, response):
    hxs = HtmlXPathSelector(response)
    # Scrape parent's catid and full, unabbreviated name.
    parent_catid = get_catid_from_url(response.request.url)
    parent_name = hxs.select("//title/text()").extract()[0].split(" - ")[0]
    yield GoogleSectorItem(name=parent_name, catid=parent_catid)
    # Scrape all company names on page.
    companies = hxs.select('//table[@id="main"]//td[@align="right"]/a')
    for x in self.process_companies(companies, parent_catid): yield x
    # Scrape link to next page for sector.
    next_page_link = hxs.select('//td[@class="nav_b"]//a/@href').extract()[0]
    yield Request(next_page_link, callback=self.parse_next_sector_page)
    # Scrape all child sectors on page.
    sectors = hxs.select('//div[@class="sfe-section"]//a')
    for x in self.process_sectors(sectors, parent_catid): yield x

  def parse_next_sector_page(self, response):
    hxs = HtmlXPathSelector(response)
    # Scrape parent's catid.
    parent_catid = get_catid_from_url(response.request.url)
    # Scrape all company names on page.
    companies = hxs.select('//table[@id="main"]//td[@align="right"]/a')
    for x in self.process_companies(companies, parent_catid): yield x
    # Scrape link to next page for sector.
    next_page_link = hxs.select('//td[@class="nav_b"]//a/@href').extract()[0]
    yield Request(next_page_link, callback=self.parse_next_sector_page)
