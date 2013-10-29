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

    # Data from income statements:
    # Sales, aka. total revenue
    sa.Column("sales", sa.Numeric),
    # Cost of goods sold, aka. cost of revenue, total cost of revenue
    sa.Column("cost_of_goods_sold", sa.Numeric),
    # Net income 
    sa.Column("net_income", sa.Numeric),
    # Sharehold net income, aka. net income applicable to common shareholders,
    # income available to common incl. extra items
    sa.Column("shareholder_net_income", sa.Numeric),

    # Data from balance sheets:
    # Cash and equivalents, aka. cash and cash equivalents
    sa.Column("cash_and_equivalents", sa.Numeric),
    # Current assets, aka. total current assets
    sa.Column("current_assets", sa.Numeric),
    # Short term debt, aka. short term debt/current portion of long term debt,
    # notes payable/short term debt
    sa.Column("short_term_debt", sa.Numeric),
    # Accounts payable
    sa.Column("accounts_payable", sa.Numeric),
    # Other current liabilities
    sa.Column("other_current_liabilities", sa.Numeric),
    # Current liabilities, aka. total current liabilities
    sa.Column("current_liabilities", sa.Numeric),
    # Long term debut
    sa.Column("long_term_debt", sa.Numeric),

    # Data from cash flow statements:
    # Operating cash flow, aka. net operating cash flow
    sa.Column("operating_cash_flow", sa.Numeric),
    # Capital expenditures
    sa.Column("capital_expenditures", sa.Numeric),

    # Data from revenue / EPS summary:
    # Earnings per share
    sa.Column("eps", sa.Numeric),
    
    # Cached computation:
    # Approximate diluted shares outstanding, computed as shareholder_net_income/eps
    sa.Column("shares_outstanding", sa.Numeric),
    # Ranker stats:
    sa.Column("gross_margin", sa.Numeric),
    sa.Column("net_margin", sa.Numeric),
    sa.Column("cash_to_debt_ratio", sa.Numeric),
    sa.Column("net_cash", sa.Numeric),
    sa.Column("foolish_flow_ratio", sa.Numeric),
    sa.Column("cash_king_margin", sa.Numeric),
  )


def downgrade():
  op.drop_table("company_financials")
