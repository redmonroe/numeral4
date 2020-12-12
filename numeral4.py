# numeral4.py

from app import app
from app.models import User, Accounts, Categories, Transactions, Reports, engine, Session

@app.shell_context_processor
def make_shell_context():
    return {'engine': engine, 'Session': Session, 'User': User, 'Reports': Reports, 'Accounts': Accounts, 'Categories': Categories, 'Transactions': Transactions}