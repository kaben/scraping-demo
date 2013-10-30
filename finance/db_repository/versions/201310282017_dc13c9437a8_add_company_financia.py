"""Add company financials table.

Revision ID: dc13c9437a8
Revises: 7e757039c7f
Create Date: 2013-10-28 20:17:41.628080

"""

# revision identifiers, used by Alembic.
revision = 'dc13c9437a8'
down_revision = '7e757039c7f'

from alembic import op
import sqlalchemy as sa


def upgrade():
  op.create_table(
    "company_financials",
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("company_id", sa.Integer, sa.ForeignKey("google_companies.id")),
    # The statement's release date.
    sa.Column("period_ending", sa.Date),
    # The statement's duration (1:quarterly, 2:annual) 
    sa.Column("duration", sa.Integer),

    # Data from income statement:
    # Sales, aka. total revenue
    sa.Column("sales", sa.Float),
    # Cost of goods sold, aka. cost of revenue, total cost of revenue
    sa.Column("cost_of_goods_sold", sa.Float),
    # Net income 
    sa.Column("net_income", sa.Float),
    # Sharehold net income, aka. net income applicable to common shareholders,
    # income available to common incl. extra items
    sa.Column("shareholder_net_income", sa.Float),
    # Multiplier string from income statement
    sa.Column("income_statement_multiplier", sa.Float),

    # Data from balance sheet:
    # Cash and equivalents, aka. cash and cash equivalents
    sa.Column("cash_and_equivalents", sa.Float),
    # Current assets, aka. total current assets
    sa.Column("current_assets", sa.Float),
    # Short term debt, aka. short term debt/current portion of long term debt,
    # notes payable/short term debt
    sa.Column("short_term_debt", sa.Float),
    # Accounts payable
    sa.Column("accounts_payable", sa.Float),
    # Other current liabilities
    sa.Column("other_current_liabilities", sa.Float),
    # Current liabilities, aka. total current liabilities
    sa.Column("current_liabilities", sa.Float),
    # Long term debut
    sa.Column("long_term_debt", sa.Float),
    # Multiplier string from balance sheet
    sa.Column("balance_sheet_multiplier", sa.Float),

    # Data from cash flow statement:
    # Operating cash flow, aka. net operating cash flow
    sa.Column("operating_cash_flow", sa.Float),
    # Capital expenditures
    sa.Column("capital_expenditures", sa.Float),
    # Multiplier string from cash flow statement
    sa.Column("cash_flow_statement_multiplier", sa.Float),

    # Data from revenue / EPS summary:
    # Earnings per share
    sa.Column("eps", sa.Float),
    
    # Cached computation:
    # Approximate diluted shares outstanding, computed as shareholder_net_income/eps
    sa.Column("shares_outstanding", sa.Float),
    # Ranker stats:
    sa.Column("gross_margin", sa.Float),
    sa.Column("net_margin", sa.Float),
    sa.Column("cash_to_debt_ratio", sa.Float),
    sa.Column("net_cash", sa.Float),
    sa.Column("foolish_flow_ratio", sa.Float),
    sa.Column("cash_king_margin", sa.Float),
  )


def downgrade():
  op.drop_table("company_financials")
