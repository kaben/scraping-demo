# This package will contain the spiders of your Scrapy project
#
# Please refer to the documentation for information on how to create and manage
# your spiders.

from finance.items import GoogleSectorItem

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


class GoogleFinanceNameSpider(BaseSpider):
  name = "google_finance_names"
  start_urls = ["https://www.google.com/finance"]

  def parse_sectors(self, sectors, parent_catid):
    names = sectors.select('text()').extract()
    links = sectors.select('@href').extract()
    catids = [get_catid_from_url(link) for link in links]
    for name, link, catid in zip(names, links, catids):
      # The first time we scrape the sector's name, the name is often
      # abbreviated. But then we request a visit to a page dedicated to that
      # sector, where we can scrape its full, unabbreviated name.
      yield GoogleSectorItem(name=name, catid=catid, parent_catid=parent_catid)
      yield Request("https://www.google.com{}".format(link), callback=self.parse_subsectors)

  def parse(self, response):
    hxs = HtmlXPathSelector(response)
    # Scrape all child sectors on page.
    sectors = hxs.select('//div[@id="secperf"]//a')
    return self.parse_sectors(sectors, parent_catid=None)

  def parse_subsectors(self, response):
    hxs = HtmlXPathSelector(response)
    # Scrape parent's full, unabbreviated name.
    parent_catid = get_catid_from_url(response.request.url)
    parent_name = hxs.select("//title/text()").extract()[0].split(" - ")[0]
    yield GoogleSectorItem(name=parent_name, catid=parent_catid)
    # Scrape all child sectors on page.
    sectors = hxs.select('//div[@class="sfe-section"]//a')
    # Having earlier used "yield", this function is now a generator, so Python
    # won't permit use of "return".
    for x in self.parse_sectors(sectors, parent_catid): yield x
