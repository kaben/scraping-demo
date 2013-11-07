scraping-demo
=============

Web scraping, with website displaying data analysis.

Notes:
======

I've just quickly hacked together a generic financial statements scraper using
MongoDB as a datastore. Partially refactored to reduce code duplication; need
further refactoring before proceeding.

PythonAnywhere doesn't appear to support MongoDB; maybe I can do data analysis
offline, and push analysis results to SQL? or setup financials site on Heroku
or Google Cloud... Or, after analysis of generic financial data, switch back
from MongoDB to SQL... or try vertical table mappings in SQL...
