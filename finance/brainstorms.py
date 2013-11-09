import pymongo
import re

def get_client_db():
  client = pymongo.MongoClient()
  db = client.finance_db
  return client, db

def get_stock_symbols(db):
  stock_symbols = set(statement['stock_symbol'] for statement in db.financials.find() if 'stock_symbol' in statement)
  return stock_symbols

def store_stock_symbols(db, stock_symbols):
  for stock_symbol in stock_symbols:
    stock = dict(stock_symbol=stock_symbol)
    db.stocks.insert(stock)

def get_data_fields(db):
  data_fields = dict((key, statement['data'][key]) for statement in db.financials.find() if 'data' in statement for key in statement['data'].keys())
  return data_fields

def get_financials_for(db, stock_symbol_regex):
  l = list(db.financials.find(dict(stock_symbol={"$regex":stock_symbol_regex})))
  return l

def common_data_list_fixup(l):
  return l[1:]
data_fixups = dict([
  (u'Net Income Applicable to', common_data_list_fixup),
  (u'Quarter:', common_data_list_fixup),
  (u'Period Ending:', common_data_list_fixup),
])
def fixup_data(data):
  copy = dict(data)
  for key, l in copy.iteritems():
    if key in data_fixups: copy[key] = data_fixups[key](l)
  return copy

def rewrite_dates(l):
  return [datetime.strptime(date, "(%m/%d/%Y)")) for date in l]

def remove_commas(string):
  return string.replace(",","")
def remove_dollars(string):
  return string.replace("$","")
neg_amt_re = re.compile("\((\d+)\)")
def get_float_from_dollars(dollar_string):
  dollar_string = remove_dollars(remove_commas(dollar_string))
  neg_amt_search = neg_amt_re.search(dollar_string)
  if neg_amt_search: return float("-{}".format(neg_amt_search.group(1)))
  else: return float(dollar_string)

 
data_rewrites = dict([
  (u'Net Cash Flow-Operating', u'Net cash flow, operating'),
  (u'Other Operating Items', u'Other operating items'),
  (u'Net Income Applicable to', u'Net income applicable to common chareholders'),
  (u'Common Stocks', u'Common stocks'),
  (u'Capital Expenditures', u'Capital expenditures'),
  (u'Short Term Debt/Current Portion of Long Term Debt', u'Short-term debt and current portion of long-term debt'),
  (u'Preferred Stocks', u'Preferred stocks'),
  (u'Cost of Revenue', u'Cost of Revenue'),
  (u'Accumulated Amortization', u'Accumulated amortization'),
  (u'Other Current Liabilities', u'Other current liabilities'),
  (u'Other Current Assets', u'Other current assets'),
  (u'Inventory', u'Inventory'),
  (u'Equity Earnings Unconsolidated Subsidiary', u'Equity earnings unconsolidated subsidiary'),
  (u'Total Current Liabilities', u'Total current liabilities'),
  (u'Interest Expense', u'Interest expense'),
  (u'Deferred Asset Charges', u'Deferred asset charges'),
  (u'Other Financing Activities', u'Other financing activities'),
  (u'Retained Earnings', u'Retained earnings'),
  (u'Long Term Debt', u'Long term debt'),
  (u'Effect of Exchange Rate', u'Effect of exchange rate'),
  (u'Research and Development', u'Research and development'),
  (u'Redeemable Stocks', u'Redeemable stocks'),
  (u'Quarter:', u'Quarter'),
  (u'Net Cash Flow', u'Net cash flow'),
  (u'Net Cash Flows-Investing', u'Net cash flow from investing'),
  (u'Other Items', u'Other items'),
  (u'Investments', u'Investments'),
  (u'Misc Stocks', u'Misc stocks'),
  (u'Sales, General and Admin', u'Sales, general and admin'),
  (u'Long Term Investments', u'Long term investments'),
  (u'Discontinued Operations', u'Discontinued operations'),
  (u'Negative Goodwill', u'Negative goodwill'),
  (u'Net Income Adjustments', u'Net income adjustments'),
  (u'Net Borrowings', u'Net borrowings'),
  (u'Quarter Ending:', u'Quarter ending'),
  (u'Other Operating Activities', u'Other operating activities'),
  (u'Sale and Purchase of Stock', u'Sale and purchase of stock'),
  (u'Total Revenue', u'Total revenue'),
  (u'Deferred Liability Charges', u'Deferred liability charges'),
  (u'Income Tax', u'Income tax'),
  (u'Non-Recurring Items', u'Non-recurring items'),
  (u'Total Liabilities', u'Total liabilities'),
  (u'Goodwill', u'Goodwill'),
  (u'Net Cash Flows-Financing', u'Net cash flow from financing'),
  (u'Period Ending:', u'Period ending'),
  (u'Other Assets', u'Other assets'),
  (u'Gross Profit', u'Gross profit'),
  (u'Net Receivables', u'Net receivables'),
  (u'Minority Interest', u'Minority interest'),
  (u'Cash and Cash Equivalents', u'Cash and cash equivalents'),
  (u'Accounts Payable', u'Accounts payable'),
  (u'Short Term Investments', u'Short term investments'),
  (u'Accounts Receivable', u'Accounts receivable'),
  (u'Depreciation', u'Depreciation'),
  (u'Operating Income', u'Operating income'),
  (u'Earnings Before Interest and Tax', u'Earnings before interest and tax'),
  (u'Total Current Assets', u'Total current assets'),
  (u'Capital Surplus', u'Capital surplus'),
  (u'Liabilities', u'Liabilities'),
  (u'Extraordinary Items', u'Extraordinary items'),
  (u'Dividends Paid', u'Dividends paid'),
  (u'Accounting Changes', u'Accounting changes'),
  (u"Add'l income/expense items", u"Additional income/expense items"),
  (u'Treasury Stock', u'Treasury stock'),
  (u'Other Investing Activities', u'Other investing activities'),
  (u'Total Equity', u'Total equity'),
  (u'Intangible Assets', u'Intangible assets'),
  (u'Adjustments to Net Income', u'Adjustments to net income'),
  (u'Total Assets', u'Total assets'),
  (u'Net Income', u'Net income'),
  (u'Earnings Before Tax', u'Earnings before tax'),
  (u'Other Equity', u'Other equity'),
  (u'Net Income-Cont Operations', u'Net income from continuing operations'),
  (u'Other Liabilities', u'Other liabilities'),
  (u'Fixed Assets', u'Fixed assets'),
])


field_renames = dict([
  (u'Net Cash Flow-Operating', u'Net cash flow, operating'),
  (u'Other Operating Items', u'Other operating items'),
  (u'Net Income Applicable to', u'Net income applicable to common chareholders'),
  (u'Common Stocks', u'Common stocks'),
  (u'Capital Expenditures', u'Capital expenditures'),
  (u'Short Term Debt/Current Portion of Long Term Debt', u'Short-term debt and current portion of long-term debt'),
  (u'Preferred Stocks', u'Preferred stocks'),
  (u'Cost of Revenue', u'Cost of Revenue'),
  (u'Accumulated Amortization', u'Accumulated amortization'),
  (u'Other Current Liabilities', u'Other current liabilities'),
  (u'Other Current Assets', u'Other current assets'),
  (u'Inventory', u'Inventory'),
  (u'Equity Earnings Unconsolidated Subsidiary', u'Equity earnings unconsolidated subsidiary'),
  (u'Total Current Liabilities', u'Total current liabilities'),
  (u'Interest Expense', u'Interest expense'),
  (u'Deferred Asset Charges', u'Deferred asset charges'),
  (u'Other Financing Activities', u'Other financing activities'),
  (u'Retained Earnings', u'Retained earnings'),
  (u'Long Term Debt', u'Long term debt'),
  (u'Effect of Exchange Rate', u'Effect of exchange rate'),
  (u'Research and Development', u'Research and development'),
  (u'Redeemable Stocks', u'Redeemable stocks'),
  (u'Quarter:', u'Quarter'),
  (u'Net Cash Flow', u'Net cash flow'),
  (u'Net Cash Flows-Investing', u'Net cash flow from investing'),
  (u'Other Items', u'Other items'),
  (u'Investments', u'Investments'),
  (u'Misc Stocks', u'Misc stocks'),
  (u'Sales, General and Admin', u'Sales, general and admin'),
  (u'Long Term Investments', u'Long term investments'),
  (u'Discontinued Operations', u'Discontinued operations'),
  (u'Negative Goodwill', u'Negative goodwill'),
  (u'Net Income Adjustments', u'Net income adjustments'),
  (u'Net Borrowings', u'Net borrowings'),
  (u'Quarter Ending:', u'Quarter ending'),
  (u'Other Operating Activities', u'Other operating activities'),
  (u'Sale and Purchase of Stock', u'Sale and purchase of stock'),
  (u'Total Revenue', u'Total revenue'),
  (u'Deferred Liability Charges', u'Deferred liability charges'),
  (u'Income Tax', u'Income tax'),
  (u'Non-Recurring Items', u'Non-recurring items'),
  (u'Total Liabilities', u'Total liabilities'),
  (u'Goodwill', u'Goodwill'),
  (u'Net Cash Flows-Financing', u'Net cash flow from financing'),
  (u'Period Ending:', u'Period ending'),
  (u'Other Assets', u'Other assets'),
  (u'Gross Profit', u'Gross profit'),
  (u'Net Receivables', u'Net receivables'),
  (u'Minority Interest', u'Minority interest'),
  (u'Cash and Cash Equivalents', u'Cash and cash equivalents'),
  (u'Accounts Payable', u'Accounts payable'),
  (u'Short Term Investments', u'Short term investments'),
  (u'Accounts Receivable', u'Accounts receivable'),
  (u'Depreciation', u'Depreciation'),
  (u'Operating Income', u'Operating income'),
  (u'Earnings Before Interest and Tax', u'Earnings before interest and tax'),
  (u'Total Current Assets', u'Total current assets'),
  (u'Capital Surplus', u'Capital surplus'),
  (u'Liabilities', u'Liabilities'),
  (u'Extraordinary Items', u'Extraordinary items'),
  (u'Dividends Paid', u'Dividends paid'),
  (u'Accounting Changes', u'Accounting changes'),
  (u"Add'l income/expense items", u"Additional income/expense items"),
  (u'Treasury Stock', u'Treasury stock'),
  (u'Other Investing Activities', u'Other investing activities'),
  (u'Total Equity', u'Total equity'),
  (u'Intangible Assets', u'Intangible assets'),
  (u'Adjustments to Net Income', u'Adjustments to net income'),
  (u'Total Assets', u'Total assets'),
  (u'Net Income', u'Net income'),
  (u'Earnings Before Tax', u'Earnings before tax'),
  (u'Other Equity', u'Other equity'),
  (u'Net Income-Cont Operations', u'Net income from continuing operations'),
  (u'Other Liabilities', u'Other liabilities'),
  (u'Fixed Assets', u'Fixed assets'),
])
def rename_fields(data):
  return dict((field_renames[key], value) for key, value in data.iteritems())

def fixup_data_and_rename_fields(data):
  return rename_fields(fixup_data(data))

def verify_data_lengths(data):
  lengths = [len(x) for x in data.itervalues()]
  return min(lengths) == max(lengths)

