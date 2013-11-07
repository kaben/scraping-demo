# Scrapy settings for finance project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

BOT_NAME = 'finance'

SPIDER_MODULES = ['finance.spiders']
NEWSPIDER_MODULE = 'finance.spiders'
DOWNLOAD_DELAY = 1

# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = "Finance bot by Kaben Nanlohy (+kaben.nanlohy@gmail.com)"

ITEM_PIPELINES = [
  "finance.pipelines.FinanceDbPipeline",
]

LOG_FILE = "scrapy.log"
#LOG_LEVEL = "WARNING"

#SQLALCHEMY_URL = "sqlite:///finance.sqlitedb"
SQLALCHEMY_URL = "mysql://irrealis_finance:irrealis_finance@localhost/irrealis_finance"
#SCRAPE_COMPANIES_FROM_SECTORS = True
