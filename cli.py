import click

import argparse
from utils import utils
from numeral4.models import engine, Base, Accounts, Transactions, Categories, NotPosted, Handler, Session, Reports, Helper, Reconciliation


@click.group()
def cli():
    pass

@cli.command()
@click.argument('arg')
@click.option('--c', type=str)
def db(arg, c=None):
    click.echo('dbtools')
    if arg == 'show_tables':
        utils.DB_Utilities.show_existing_tables(engine)
    elif arg == 'show_class_structure':
        utils.DB_Utilities.show_class_structure(c)
    elif arg == 'recreate_all':
        click.confirm('Do you want to continue (may erase all data)?', abort=True)
        utils.DB_Utilities.recreate_database(engine, Base)
    elif arg == 'recreate_nodrop':
        click.confirm('Do you want to continue (does not drop table but may erase data)?', abort=True)
        utils.DB_Utilities.recreate_no_drop(engine, Base, Session)
    elif arg == 'upgrade':
        lt = utils.Liltilities() # alembic style
        lt.generic_db_revision()
    elif arg == 'db_dump':
        utils.DB_Utilities.pg_dump_one()
    elif arg == 'db_restore':
        utils.DB_Utilities.pg_restore_one(infile) # this does not work
    elif arg == 'upgrade_flask_style':
        pass
        #TODO: I am not going to use this

@cli.command() 
@click.argument('args1', nargs=1)
@click.argument('args2', nargs=1)
def CRUD(args1, args2):
    click.echo(args1) # python cli.py crud update Categories
    if args1 == 'create':
        Handler.create_handler(args2)
    elif args1 == 'query':
        Handler.read_handler(args2)
    elif args1 == 'update':
        Handler.update_handler(args2)
    elif args1 == 'delete':
        Handler.delete_handler(args2)

@cli.command()
@click.argument('args1', nargs=1)
def intake(args1):
    click.echo('Functions for importing transactions and categories.')
    if args1 == 'import':
        NotPosted.import_staging()
    elif args1 == 'load_cat':
        Categories.load_categories_from_excel()
    elif args1 == 'ctrl_trans':      
        NotPosted.controlled_transmutation()


@cli.command()
@click.argument('args1', nargs=1)
def report(args1):
    click.echo('Generating reports')
    click.echo(args1)
    if args1 == '1':
        Reports.show_posted_transactions() # ;ass some args for more!
    elif args1 == '2':
        Reports.show_notposted_transactions()
    elif args1 == '3':
        Reports.net_worth()
    elif args1 == '4':
        Reports.category_reports()
    # if args1.reports:
#     choice = int(input(" Press 1 to show just ALL posted transactions,\n Press 2 for ALL unposted transactions.\n Press 3 for back calc posted. \n Press 4 for net worth. \n Press 5 for category reports \n Press 6 to select an account and show all transactions. \n  *this should show all account with curb, then when you select an account it shows ALL txn PROPERLY selected, along with current balance \n Press 7 to check balance of posted. \n Press 8 for best version of summary income and expense by category by month all accounts."))
#     elif args1 == '3':
#         Reports.back_calc_posted()
#     elif args1 == '6':
#         Reports.show_transactions_by_account()
#     elif args1 == '7':
#         Accounts.check_balance_if_posted()
#     elif args1 == '8':
#         Reports.all_accounts_bym_bycat()
#     else:
#         "Please try again."

cli.add_command(db)
cli.add_command(CRUD)
cli.add_command(report)
cli.add_command(intake)

# TODO: I can move a lot of user input up to this level and confirmations, or can I? 
# TODO: INTEGRATE WITH SETUP TOOL

if __name__ == "__main__":
    cli()







# parser.add_argument('--check_balance', help='check an account balance', action='store_true' )
# parser.add_argument('--start_balance', help='check an account starting balance', action='store_true' )

# parser.add_argument('--check_folder', default=None, type=str, help='given path, walk a folder')
# parser.add_argument('--reports', help='check variables in memory', action='store_true')

# """import"""
# parser.add_argument('-i', '--import_func', help='starts import function, excel to db', action='store_true')
# parser.add_argument('--post', help='starts controlled posting to database', action='store_true')
# parser.add_argument('--load_cat', help='loads categories from excel file, be sure to delete existing before', action='store_true')

# """export"""
# parser.add_argument('-ex', '--export', help='export to excel report in export folder in numeral2', action='store_true')

# """reconciliation"""
# parser.add_argument('-rc', '--reconciliation', help='reconcile by account', action='store_true')

# args1 = parser.parse_args()

# """DB management and table management"""


# if args.check_folder:
#     path = walk_download_folder(args.check_folder)
#     print(path)
#     state = State()
#     state.set_path = path
#     print(state.set_path)



# #import and post




# """CRUD"""
# if args.query:
#     Handler.read_handler(args.query)

# if args.check_balance:
#     Accounts.check_balance_if_posted()

# if args.start_balance:
#     get_start_balance()

# """reports"""


# """exporting utilities"""
# if args.export:
#     Helper.export_excel()

# """reconciliation"""
# if args.reconciliation:
#     Reconciliation.start()