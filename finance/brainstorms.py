import pymongo
import datetime, re
import finance.models

# Data cleanup functions.
def remove_first_element(l, _):
  "Data-cleanup-pipeline function to remove first element from data arrays with extra first element."
  return l[1:]

def rewrite_dates(l, _):
  "Data-cleanup-pipeline function to convert date strings to Python datetime objects."
  return [datetime.datetime.strptime(date, "%m/%d/%Y") for date in l]

def _remove_commas(string):
  return string.replace(",","")
def _remove_dollars(string):
  return string.replace("$","")
neg_amt_re = re.compile("\((\d+)\)")
def _get_float_from_dollars(dollar_string):
  dollar_string = _remove_dollars(_remove_commas(dollar_string))
  neg_amt_search = neg_amt_re.search(dollar_string)
  if neg_amt_search: return float("-{}".format(neg_amt_search.group(1)))
  else: return float(dollar_string)
def rewrite_dollars(l, multiplier):
  "Data-cleanup-pipeline function to convert dollar-currency strings to floats."
  return [multiplier*_get_float_from_dollars(s) for s in l]

# Data cleanup pipelines.
data_fixups = dict([
  (u'Net Income Applicable to', (remove_first_element, rewrite_dollars,)),
  (u'Quarter:', (remove_first_element,)),
  (u'Quarter Ending:', (rewrite_dates,)),
  (u'Period Ending:', (remove_first_element, rewrite_dates,)),
])
def fixup_data(data, multiplier):
  "Runs data cleanup pipelines."
  copy = dict(data)
  for key, l in copy.iteritems():
    if key in data_fixups:
      for fixup in data_fixups[key]: l = fixup(l, multiplier)
    else: l = rewrite_dollars(l, multiplier)
    copy[key] = l
  return copy

# Field name cleanup.
field_renames = dict([
  (u'Accounting Changes', u'Accounting changes'),
  (u'Accounts Payable', u'Accounts payable'),
  (u'Accounts Receivable', u'Accounts receivable'),
  (u'Accumulated Amortization', u'Accumulated amortization'),
  (u"Add'l income/expense items", u"Additional income/expense items"),
  (u'Adjustments to Net Income', u'Adjustments to net income'),
  (u'Capital Expenditures', u'Capital expenditures'),
  (u'Capital Surplus', u'Capital surplus'),
  (u'Cash and Cash Equivalents', u'Cash and cash equivalents'),
  (u'Common Stocks', u'Common stocks'),
  (u'Cost of Revenue', u'Cost of Revenue'),
  (u'Deferred Asset Charges', u'Deferred asset charges'),
  (u'Deferred Liability Charges', u'Deferred liability charges'),
  (u'Depreciation', u'Depreciation'),
  (u'Discontinued Operations', u'Discontinued operations'),
  (u'Dividends Paid', u'Dividends paid'),
  (u'Earnings Before Interest and Tax', u'Earnings before interest and tax'),
  (u'Earnings Before Tax', u'Earnings before tax'),
  (u'Effect of Exchange Rate', u'Effect of exchange rate'),
  (u'Equity Earnings Unconsolidated Subsidiary', u'Equity earnings unconsolidated subsidiary'),
  (u'Extraordinary Items', u'Extraordinary items'),
  (u'Fixed Assets', u'Fixed assets'),
  (u'Goodwill', u'Goodwill'),
  (u'Gross Profit', u'Gross profit'),
  (u'Income Tax', u'Income tax'),
  (u'Intangible Assets', u'Intangible assets'),
  (u'Interest Expense', u'Interest expense'),
  (u'Inventory', u'Inventory'),
  (u'Investments', u'Investments'),
  (u'Liabilities', u'Liabilities'),
  (u'Long Term Debt', u'Long term debt'),
  (u'Long Term Investments', u'Long term investments'),
  (u'Minority Interest', u'Minority interest'),
  (u'Misc Stocks', u'Misc stocks'),
  (u'Negative Goodwill', u'Negative goodwill'),
  (u'Net Borrowings', u'Net borrowings'),
  (u'Net Cash Flow-Operating', u'Net cash flow, operating'),
  (u'Net Cash Flows-Financing', u'Net cash flow from financing'),
  (u'Net Cash Flows-Investing', u'Net cash flow from investing'),
  (u'Net Cash Flow', u'Net cash flow'),
  (u'Net Income Adjustments', u'Net income adjustments'),
  (u'Net Income Applicable to', u'Net income applicable to common chareholders'),
  (u'Net Income-Cont Operations', u'Net income from continuing operations'),
  (u'Net Income', u'Net income'),
  (u'Net Receivables', u'Net receivables'),
  (u'Non-Recurring Items', u'Non-recurring items'),
  (u'Operating Income', u'Operating income'),
  (u'Other Assets', u'Other assets'),
  (u'Other Current Assets', u'Other current assets'),
  (u'Other Current Liabilities', u'Other current liabilities'),
  (u'Other Equity', u'Other equity'),
  (u'Other Financing Activities', u'Other financing activities'),
  (u'Other Investing Activities', u'Other investing activities'),
  (u'Other Items', u'Other items'),
  (u'Other Liabilities', u'Other liabilities'),
  (u'Other Operating Activities', u'Other operating activities'),
  (u'Other Operating Items', u'Other operating items'),
  (u'Period Ending:', u'Period ending'),
  (u'Preferred Stocks', u'Preferred stocks'),
  (u'Quarter Ending:', u'Quarter ending'),
  (u'Quarter:', u'Quarter'),
  (u'Redeemable Stocks', u'Redeemable stocks'),
  (u'Research and Development', u'Research and development'),
  (u'Retained Earnings', u'Retained earnings'),
  (u'Sale and Purchase of Stock', u'Sale and purchase of stock'),
  (u'Sales, General and Admin', u'Sales, general and admin'),
  (u'Short Term Debt/Current Portion of Long Term Debt', u'Short-term debt and current portion of long-term debt'),
  (u'Short Term Investments', u'Short term investments'),
  (u'Total Assets', u'Total assets'),
  (u'Total Current Assets', u'Total current assets'),
  (u'Total Current Liabilities', u'Total current liabilities'),
  (u'Total Equity', u'Total equity'),
  (u'Total Liabilities', u'Total liabilities'),
  (u'Total Revenue', u'Total revenue'),
  (u'Treasury Stock', u'Treasury stock'),
])
def rename_fields(data):
  "Renames fieldnames."
  return dict((field_renames[key], value) for key, value in data.iteritems())

def fixup_data_and_rename_fields(data, multiplier):
  "Runs data-cleanup pipelines, then runs field-name cleanup."
  return rename_fields(fixup_data(data, multiplier))

def verify_data_lengths(data):
  "Verifies that every data array has the same length."
  lengths = [len(x) for x in data.itervalues()]
  return min(lengths) == max(lengths)

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

def get_financials_for(db, query):
  l = list(db.financials.find(dict(**query)))
  return l

def get_statements_from_financial_object(financial_object):
  financial_data_arrays = fixup_data_and_rename_fields(financial_object['data'], financial_object['mult'])
  keys, value_arrays = zip(*financial_data_arrays.iteritems())
  value_sets = zip(*value_arrays)
  statements = [dict(zip(keys, values)) for values in value_sets]
  updates_dict = {
    u'Stock symbol':financial_object['stock_symbol'],
    u'Dollar multiplier when scraped':financial_object['mult'],
  }
  for statement in statements: statement.update(updates_dict)
  return financial_data_arrays, statements

def insert_data_dicts_in(collection, data_dicts):
  for data_dict in data_dicts: collection.insert(data_dict)

def extract_and_insert_statements(collection, financial_object):
  stock_symbol = financial_object['stock_symbol']
  if 'data' in financial_object:
    data_arrays, statements = get_statements_from_financial_object(financial_object)
    if verify_data_lengths(data_arrays):
      insert_data_dicts_in(collection, statements)
    else:
      raise ValueError("Bad financial data for stock {} (number of data rows should be the same for each column, but isn't).".format(stock_symbol))
  else:
    print "No financial data for stock {} (this usually means Nasdaq had no data available for the company).".format(stock_symbol)

def process_statements_for(db, query):
  financials = get_financials_for(db, query)
  if financials:
    try:
      qtr_inc, qtr_bal_sheet, qtr_cash_flow, ann_inc, ann_bal_sheet, ann_cash_flow = financials[:6]
      eps_summaries = financials[6:]
      extract_and_insert_statements(db.quarterly_income_statements, qtr_inc)
      extract_and_insert_statements(db.quarterly_balance_sheets, qtr_bal_sheet)
      extract_and_insert_statements(db.quarterly_cash_flow_statements, qtr_cash_flow)
      extract_and_insert_statements(db.annual_income_statements, ann_inc)
      extract_and_insert_statements(db.annual_balance_sheets, ann_bal_sheet)
      extract_and_insert_statements(db.annual_cash_flow_statements, ann_cash_flow)
      insert_data_dicts_in(db.eps_summaries, eps_summaries)
    except Exception as e:
      print "Couldn't process statements for query '{}' ({}).".format(query, e) 
    
def drop_processed_statements(db):
  db.quarterly_income_statements.drop()
  db.quarterly_balance_sheets.drop()
  db.quarterly_cash_flow_statements.drop()
  db.annual_income_statements.drop()
  db.annual_balance_sheets.drop()
  db.annual_cash_flow_statements.drop()
  db.eps_summaries.drop()

sql_financial_colmap = dict([
  (u"Period ending", u"period_ending"),
  (u"Quarter ending", u"quarter_ending"),
  (u"Accounting changes", u"accounting_changes"),
  (u"Accounts payable", u"accounts_payable"),
  (u"Accounts receivable", u"accounts_receivable"),
  (u"Accumulated amortization", u"accumulated_amortization"),
  (u"Additional income/expense items", u"additional_income_or_expense_items"),
  (u"Adjustments to net income", u"adjustments_to_net_income"),
  (u"Capital expenditures", u"capital_expenditures"),
  (u"Capital surplus", u"capital_surpolus"),
  (u"Cash and cash equivalents", u"cash_and_equivalents"),
  (u"Common stocks", u"common_stocks"),
  (u"Cost of Revenue", u"cost_of_revenue"),
  (u"Deferred asset charges", u"deferred_asset_charges"),
  (u"Deferred liability charges", u"deferred_liability_charges"),
  (u"Depreciation", u"depreciation"),
  (u"Discontinued operations", u"discontinued_operations"),
  (u"Dividends paid", u"dividends_paid"),
  (u"Earnings before interest and tax", u"earnings_before_interest_and_tax"),
  (u"Earnings before tax", u"earnings_before_tax"),
  (u"Effect of exchange rate", u"effect_of_exchange_rate"),
  (u"Equity earnings unconsolidated subsidiary", u"equity_earnings_unconsolidated_subsidiary"),
  (u"Extraordinary items", u"extraordinary_items"),
  (u"Fixed assets", u"fixed_assets"),
  (u"Goodwill", u"goodwill"),
  (u"Gross profit", u"gross_profit"),
  (u"Income tax", u"income_tax"),
  (u"Intangible assets", u"intangible_assets"),
  (u"Interest expense", u"interest_expense"),
  (u"Inventory", u"inventory"),
  (u"Investments", u"investments"),
  (u"Liabilities", u"liabilities"),
  (u"Long term debt", u"long_term_debt"),
  (u"Long term investments", u"long_term_investments"),
  (u"Minority interest", u"minority_interest"),
  (u"Misc stocks", u"misc_stocks"),
  (u"Negative goodwill", u"negative_goodwill"),
  (u"Net borrowings", u"net_borrowing"),
  (u"Net cash flow", u"net_cash_flow"),
  (u"Net cash flow, operating", u"net_operating_cash_flow"),
  (u"Net cash flow from financing", u"net_cash_flow_from_financing"),
  (u"Net cash flow from investing", u"net_cash_flow_from_investing"),
  (u"Net income", u"net_income"),
  (u"Net income adjustments", u"net_income_adjustments"),
  (u"Net income applicable to common chareholders", u"shareholder_net_income"),
  (u"Net income from continuing operations", u"net_income_from_continuing_operations"),
  (u"Net receivables", u"net_receivables"),
  (u"Non-recurring items", u"non_recurring_items"),
  (u"Operating income", u"operating_income"),
  (u"Other assets", u"other_assets"),
  (u"Other current assets", u"other_current_assets"),
  (u"Other current liabilities", u"other_current_liabilities"),
  (u"Other equity", u"other_equity"),
  (u"Other financing activities", u"other_financing_activities"),
  (u"Other investing activities", u"other_investing_activities"),
  (u"Other items", u"other_items"),
  (u"Other liabilities", u"other_liabilities"),
  (u"Other operating activities", u"other_operating_activities"),
  (u"Other operating items", u"other_operating_items"),
  (u"Preferred stocks", u"preferred_stocks"),
  (u"Redeemable stocks", u"redeemable_stocks"),
  (u"Research and development", u"research_and_development"),
  (u"Retained earnings", u"retained_earnings"),
  (u"Sale and purchase of stock", u"sale_and_purchase_of_stock"),
  (u"Sales, general and admin", u"sales_general_and_admin"),
  (u"Short-term debt and current portion of long-term debt", u"short_term_debt"),
  (u"Short term investments", u"short_term_investments"),
  (u"Total assets", u"total_assets"),
  (u"Total current assets", u"total_current_assets"),
  (u"Total current liabilities", u"total_current_liabilities"),
  (u"Total equity", u"total_equity"),
  (u"Total liabilities", u"total_liabilities"),
  (u"Total revenue", u"total_revenue"),
  (u"Treasury stock", u"treasury_stock"),
])
quarter_fixups = {u'1st':1, u'2nd':2, u'3rd':3, u'4th':4}

def convert_statement_to_sql_dict(statement):
  return dict((sql_financial_colmap[k], v) for k, v in statement.iteritems() if k in sql_financial_colmap)

def get_google_company_for_stock_symbol(stock_symbol, orm):
  return orm.session.query(orm.GoogleCompany).filter(orm.GoogleCompany.stock_symbol == stock_symbol).one()

def get_sql_lookup_keys_and_update_dict(statement, orm):
  sql_dict = convert_statement_to_sql_dict(statement)
  if u'quarter' in sql_dict:
    quarter_string = sql_dict[u'quarter']
    sql_dict[u'quarter'] = quarter_fixups[quarter_string]
  google_company = get_google_company_for_stock_symbol(statement[u'Stock symbol'], orm)
  for ending_key in (u'period_ending', u'quarter_ending'):
    sql_dict[ending_key] = sql_dict[ending_key].date() if ending_key in sql_dict else None
  period_ending = sql_dict[u'period_ending']
  quarter_ending = sql_dict[u'quarter_ending']
  lookup_keys = dict(
    company = google_company,
    period_ending = period_ending,
    quarter_ending = quarter_ending,
  )
  return lookup_keys, sql_dict

def lookup_nasdaq_financials_by(lookup_keys, orm):
  return orm.get_or_create(orm.NasdaqCompanyFinancials, **lookup_keys)

def update_nasdaq_financials_with(sql_dict, nasdaq_financials):
  for k, v in sql_dict.iteritems(): setattr(nasdaq_financials, k, v)

def copy_financial_statement_to_nasdaq_financials(statement, orm):
  try:
    lookup_keys, update_dict = get_sql_lookup_keys_and_update_dict(statement, orm)
    nasdaq_financials = lookup_nasdaq_financials_by(lookup_keys, orm)
    update_nasdaq_financials_with(update_dict, nasdaq_financials)
    orm.session.commit()
  except Exception as e:
    orm.session.rollback()
    print "Error while copying financial statement ({}) to nasdaq_financials sql table ({}).".format(nasdaq_financials, e)

# Example use:
# >>> client, db = get_client_db()
# >>> query = dict(stock_symbol={"$regex":".*AAPL"})
# >>> query = dict(stock_symbol=u"NASDAQ:AAPL")
# >>> financials = get_financials_for(db, query)
# >>> financial_object = financials[0]
# >>> financial_data_arrays, financial_statements = get_statements_from_financial_object(financial_object)
# >>> print "Verification status:", verify_data_lengths(financial_data_arrays)

# Idea:
# >>> qtr_inc, qtr_bal_sheet, qtr_cash_flow, ann_inc, ann_bal_sheet, ann_cash_flow = financials[:6]

# >>> for stock_symbol in stock_symbols:
# ...     query = dict(stock_symbol=stock_symbol)
# ...     print "processing statements for {}".format(stock_symbol)
# ...     process_statements_for(db, query)

# >>> for stmt in db.quarterly_income_statements.find():
# ...     copy_financial_statement_to_nasdaq_financials(stmt, orm)
