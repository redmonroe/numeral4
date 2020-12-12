import csv
import logging
import sys
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import ROUND_05UP, ROUND_HALF_UP, Decimal

import numpy as np
import pandas as pd
from config import Config
from dateutil.rrule import DAILY, MONTHLY, rrule
from app import login
from sqlalchemy import (Column, Date, ForeignKey, Integer, Numeric, String,
                        between, create_engine, extract, or_)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, with_polymorphic
from utils import utils
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin

log = logging.getLogger(__name__)
logging.basicConfig(
        filename = 'models.log', 
        filemode = 'w', 
        level    = logging.DEBUG, 
)

Base = declarative_base() # We need to inherit Base in order to register models with SQA.
engine = create_engine(Config.DATABASE_URI_PANDAS, pool_size=20)
Session = sessionmaker(bind=engine, expire_on_commit=False)

#python-dateutils


"""SEARCH FOR TODO"""
#TODO: consolidate current_balance methods so that if I change scheme I don't get lost in a nightmare of twists and sqlturns: there is one in Accounts and one in Reports
#TODO: I have an issue where when basic transaction repr shows the 'other' amount when transaction is a transfer, I can type this out in a query but this type of consideration has to be paramount when I am consolidating reporting functions; I want more from my repr!!!
#TODO: automatically pull period beginning balance for reconcilation (instead of manually entered)

@login.user_loader
def load_user(id):
    s = Session()
    return s.query(User).get(int(id))

class User(UserMixin, Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(String(64), index=True, unique=True)
    email = Column(String(120), index=True, unique=True)
    password_hash = Column(String(128))
    accounts = relationship('Accounts', backref='user')
    categories = relationship('Categories', backref='user')

    def __repr__(self):
        return '<User {}>'.format(self.username) 

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)       

class Accounts(Base):
    __tablename__ = 'accountlist'

    id = Column(Integer, primary_key=True)
    acct_name = Column(String)
    startbal = Column(Numeric)
    type = Column(String)
    status = Column(String) #either open or closed
    user_id = Column(Integer, ForeignKey('user.id'))

    def __repr__(self): # do not fuck with this lightly
        return f'id:{self.id} name:{self.acct_name:<25} | type:{self.type:<10} sbal:{self.startbal:^8} status:{self.status}'

    @staticmethod
    def create_accounts(s, clsname, instance, display_names):
        Accounts.just_show_all_accounts()

        acct_name=Helper.fancy_input(meat='acct_name')
        startbal=Helper.fancy_input(meat='starting_balance')

        selection=Helper.fancy_int_input(text='Press 1 for asset account, Press 2 for liability account.')
        if selection == 1:
            type = 'asset'
        elif selection == 2:
            type = 'liability'
        else:
            print('fail setting adjusted to ON')

        status=Helper.fancy_input(meat='status')
        new_account = Accounts(
                                id=None,
                                acct_name=acct_name,
                                startbal=startbal,
                                type=type,
                                status=status,
                                )

        s.add(new_account)
        s.commit()
        s.close()

        print(new_account)

    @staticmethod
    def just_show_all_accounts():
        s = Session()
        choices = []
        rows = []
        r = s.query(Accounts).order_by(Accounts.id)

        for count, row in enumerate(r, 1):
            cur_bal = Accounts.current_balance_for_just_show_all_accounts(row.id)
            choices.append(count)
            rows.append(row.id)
            print(count, row, '| current:', cur_bal) # this should just print the repr

        choice_row = dict(zip(choices, rows))

        return choice_row

    @staticmethod
    def just_show_all_accounts_flask():
        s = Session()
        choices = []
        rows = []
        cb_list = []
        r = s.query(Accounts).order_by(Accounts.id)

        for count, row in enumerate(r, 1):
            cur_bal = Accounts.current_balance_for_just_show_all_accounts(row.id)
            choices.append(count)
            rows.append(row.acct_name)
            cb_list.append(cur_bal)
            print(count, row, '| current:', cur_bal) # this should just print the repr

        accounts_plus_balance = dict(zip(rows, cb_list))
        
        return accounts_plus_balance

    @staticmethod
    def current_balance_for_just_show_all_accounts(id):
        s = Session()
        results = []
        r = s.query(Transactions).filter(Transactions.acct_id2 == id, Transactions.type != 'notposted').all()
        r2 = s.query(Transactions).filter(Transactions.acct_id == id, Transactions.type != 'notposted').all()
        for item in r:
            results.append(item)
        for item in r2:
            results.append(item)

        bal_list = []
        starting_balance = s.query(Accounts).filter(Accounts.id == id).first()

        for item in results:
            if item.type == 'transfers' and item.acct_id2 == id:
                bal_list.append(item.amount2)
            elif item.type == 'transfers' and item.acct_id== id:
                bal_list.append(item.amount)
            elif item.type == 'transactions':
                bal_list.append(item.amount)

        cur_bal = Decimal(starting_balance.startbal) + sum(bal_list)

        return cur_bal

    @staticmethod
    def delete_accounts(s, clsname, instance):
        choice_row = Accounts.just_show_all_accounts()

        selection = int(input('Please select a row (int) to delete: '))
        record_to_delete = 0
        for k, v in choice_row.items():
            if selection == k:
                record_to_delete = v

        s.query(Accounts).filter(Accounts.id == record_to_delete).\
            delete(synchronize_session=False)
        s.commit()
        s.close()

    @staticmethod
    def update_accounts(s, clsname, instance):
        print(f'These are existing {clsname}\n')
        choice_row = Accounts.just_show_all_accounts()

        selection = int(input('Please select a row (int) to update with: '))
        record_to_update = 0
        for k, v in choice_row.items():
            if selection == k:
                record_to_update = v

        current = s.query(Accounts).filter(Accounts.id == record_to_update).first()

        current_dict = {
                'id': current.id,
                'acct_name': current.acct_name ,
                'startbal': current.startbal,
                'type': current.type,
                'status': current.status
                }

        for k, v in current_dict.items():
            ui = Helper.class_optional_input(k, v)
            current_dict[k] = ui
            setattr(current, k, ui)
            s.commit()

    @staticmethod
    def check_balance_if_posted():
        print('Checking balance . . . ')
        s = Session()
        choice_row = Accounts.just_show_all_accounts()
        selection = int(input('Which account would you like to check the balance? '))
        check_this_account_balance = 0
        for k, v in choice_row.items():
            if selection == k:
                check_this_account_balance = v

        print('new transaction account id:', check_this_account_balance)

        def get_net_change(id): #needs the type discriminator here

            s = Session()
            account_start = s.query(Accounts).filter(Accounts.id == id).all()

            startbal = [item.startbal for item in account_start]
            startbal = startbal.pop()

            name = [item.acct_name for item in account_start]
            name = name.pop()

            type = [item.type for item in account_start]
            type = type.pop()

            transactions = s.query(Transactions).filter(Transactions.acct_id == id).all()

            cum_sum = [row.amount for row in transactions]

            amounts = 0
            for item in cum_sum:
                if item == None:
                    item = 0
                amounts += item

            end_balance = startbal + amounts

            return amounts, id, name, type, end_balance, startbal


        net_change, id, name, type, end_balance, startbal = get_net_change(check_this_account_balance)
        print(net_change, id, name, type, 'end balance:', end_balance, startbal)
        """


        # all, choice = get_txn_by_account()
        # for items in all:
        #     print(items.acct_id)
        #
        # r = s.query(Accounts).filter(Accounts.id == choice).all()
        #
        # for item in r:
        #     startbal = item.startbal
        #     print(item.startbal)
        # print(f'Start balance = {startbal}')
        #
        # cum_sum = [row.amount for row in all]
        #
        # amounts = 0
        # for item in cum_sum:
        #     amounts += item
        #
        # end_balance = startbal + amounts
        # print(f'End balance = {end_balance}')
        """

class Categories(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True)
    short_name = Column(String)
    name = Column(String)
    inorex = Column(String)
    user_id = Column(Integer, ForeignKey('user.id'))
    """revisit this when I clean up queries"""
    # txn = relationship("Transactions", uselist=False, backref="cat")

    def __repr__(self):
        spacer = '**'
        return f'{self.name:-^40} {spacer:>2} {self.inorex:^20}'

    @staticmethod
    def create_categories(s, clsname, instance, display_names):
        print(f'These are existing {clsname}')
        s = Session()
        choice_row = Categories.just_show_all_categories()

        name=Helper.fancy_input(meat='name')
        choice = Helper.fancy_int_input(text='Press 1 for income, Press 2 for expense account.')
        if choice == 1:
            income_or_expense = 'income'
        elif choice == 2:
            income_or_expense = 'expense'

        new_category = Categories(
                                    id=None,
                                    name=name,
                                    inorex=income_or_expense
                                    )
        s.add(new_category)
        s.commit()
        s.close()

    @staticmethod
    def load_categories_from_excel():
        print('Loading categories from excel.  Did you remember to delete existing??????????????')
        s = Session()
        # """
        lt = utils.Liltilities()
        path = lt.sheet_finder('loading categories', DL_FILE_PATH)
        df = pd.read_excel(path)

        print(df.head(5))

        for index, row in df.iterrows():
            new_cat = Categories(
                                id=row['id'],
                                name=row['category'],
                                inorex=row['type']
                                )
            s.add(new_cat)
            s.commit()
            print(new_cat)

        s.close()

    @staticmethod
    def just_show_all_categories():
        """This function is (it is hoped) just a utility function for returning the enumerated repr of Categories

        Returns:
            dictionary: key is row presented to user; value is categories id string
        """
        s = Session()
        choices = []
        rows = []
        r = s.query(Categories).order_by(Categories.inorex)
        for count, row in enumerate(r, 1):
            choices.append(count)
            rows.append(row.id)
            print(count, row)

        choice_row = dict(zip(choices, rows))
        return choice_row

    @staticmethod
    def just_show_all_categories_flask():
        """This function is (it is hoped) just a utility function for returning the enumerated repr of Categories

        Returns:
            dictionary: key is row presented to user; value is categories id string
        """
        s = Session()
        choices = []
        rows = []
        r = s.query(Categories).order_by(Categories.inorex)
        for count, row in enumerate(r, 1):
            choices.append(count)
            rows.append(row.id)
            print(count, row)

        choice_row = dict(zip(choices, rows))
        return r

    @staticmethod
    def update_categories(s, clsname, instance):
        print(f'These are existing {clsname}')
        s = Session()
        choice_row = Categories.just_show_all_categories()
        selection = int(input('Please select a row (int) to update with: '))
        record_to_update = 0
        for k, v in choice_row.items():
            if selection == k:
                record_to_update = v

        current = s.query(Categories).filter(Categories.id == record_to_update).first()

        current_dict = {
                'id': current.id,
                'name': current.name ,
                'inorex': current.inorex,
                }

        for k, v in current_dict.items():
            ui = Helper.class_optional_input(k, v)
            current_dict[k] = ui
            setattr(current, k, ui)
            s.commit()

    @staticmethod
    def delete_categories(s, clsname, instance):
        print(f'These are existing {clsname}')
        s = Session()
        choice_row = Categories.just_show_all_categories()
        selection = int(input('Please select a row (int) to update with: '))
        record_to_delete = 0
        for k, v in choice_row.items():
            if selection == k:
                record_to_delete = v

        current = s.query(Categories).filter(Categories.id == record_to_delete).first()

        s.query(instance).filter(instance.id == record_to_delete).\
            delete(synchronize_session=False)
        s.commit()
        s.close()

@dataclass
class Transactions(Base):
    __tablename__ = 'transactionlist' # table name in pg

    id = Column(Integer, primary_key=True)
    date = Column(Date)
    amount = Column(Numeric)
    payee_name = Column(String) # would become own column
    type = Column(String)
    # cat_id = Column(String, ForeignKey('categories.id'))
    cat_id = Column(String)
    # split_amt1 = Column(Numeric)
    cat_id2 = Column(String)
    acct_id = Column(Integer, ForeignKey('accountlist.id'))
    amount2 = Column(Numeric)
    acct_id2 = Column(Integer, ForeignKey('accountlist.id'))


    def __repr__(self):
        spacer = '**'
        if self.payee_name == None:
            self.payee_name = ' '
        if self.cat_id == None:
           self.cat_id = ' '
        return f'>>>> {self.id} {self.acct_id} {spacer} | {self.date} | {self.amount:>10} {self.type:<15} cat: {self.cat_id:<8} | payee: {self.payee_name:<20}'

    @staticmethod
    def create_transactions(s, clsname, instance, display_names):
        choice_row = Accounts.just_show_all_accounts()

        selection = int(input('\nPlease select a new transaction account: \n >'))
        account_to_add_to = 0
        for k, v in choice_row.items():
            if selection == k:
                account_to_add_to = v

        print(f'You selected account id {account_to_add_to} to ADD NEW TRANSACTION.')

        """
        explicit input passing
        """
        #id = generated by postgres
        amount = input(f'New amount or press "s" for split or "t" for transfer>>>')

        if amount == 's':
            Splits.create_splits(s=s, acct_id=account_to_add_to)
        elif amount == 't':
            Transactions.create_transfers(s=s, acct_id=account_to_add_to)
            return
        else:
            date = Helper.fancy_input(str='date')
            payee_name = Helper.fancy_optional_input(str='payee_name')
            type2 = 'transactions'
            cat_id = Helper.cat_id(amount)

            """
            test inputs
            """
            """
            def test_create_transaction_inputs():
                date = '08/12/2020'
                ref_no = '9999'
                payee_name = 'mr. powell'
                memo = 'frankly, I dont know'
                type = 'transactionlist'
                txfr_id = None
                cat_id = 2
                # cat_id, cat_name_var = cat_name(amount)
                issplit = None
            """

            new_txn = instance(
                                date=date,
                                amount=amount,
                                payee_name=payee_name,
                                type=type2,
                                cat_id=cat_id,
                                acct_id=account_to_add_to,
                                )

            s.add(new_txn)
            s.commit()
            s.close()

        print(date)
        print(type(date))
        Reports.category_reports(date=date, account_id=account_to_add_to)
        choice = input('\nPress any key to enter another transactions.')
        Handler.create_handler(clsname)

    @staticmethod
    def create_transfers(**kwargs):
        s = kwargs['s']

        print('\nPicking a transfer account NOW!\n')

        choice_row = Accounts.just_show_all_accounts()

        selection = int(input('\nPlease select a new transfer account:'))
        transfer_account = 0
        for k, v in choice_row.items():
            if selection == k:
                transfer_account = v

        date = Helper.fancy_input(str='date')
        amt = input(f'New amount >>>')
        amount = Decimal(amt)
        amount2 = amount * -1
        payee_name = Helper.fancy_optional_input(str='payee_name')
        type = 'transfers'
        cat_id = None
        # cat_id = Helper.cat_id(amount) #transfers have no account, should be None at 09/22/2020

        new_transfer = Transactions(
                            date=date,
                            amount=amount,
                            amount2=amount2,
                            payee_name=payee_name,
                            type=type,
                            cat_id=cat_id,
                            acct_id=kwargs['acct_id'],
                            acct_id2=transfer_account,
                            )
        s.add(new_transfer)
        s.commit()
        s.close()

        choice = input('\nPress any key to enter another transactions.')
        clsname = 'Transactions'
        Handler.create_handler(clsname)

    @staticmethod
    def just_show_all_transactions(): # could do a kwargs here or switches
        s = Session()
        choices = []
        rows = []
        r = s.query(Transactions).order_by(Transactions.id)
        for count, row in enumerate(r, 1):
            choices.append(count)
            rows.append(row.id)
            print(count, row)

        choice_row = dict(zip(choices, rows))
        return choice_row

    @staticmethod
    def update_transactions(s, clsname, instance):
        """#TODO: major issues with update dicts since class structure update

        Args:
            s ([type]): [description]
            clsname ([type]): [description]
            instance ([type]): [description]
        """
        choice_row = Accounts.just_show_all_accounts()

        selection = int(input('Please select an account to update a record from: '))
        delete_from_account = 0
        for k, v in choice_row.items():
            if selection == k:
                delete_from_account = v

        print('transaction update account id:', delete_from_account)

        r = s.query(Transactions).filter(Transactions.acct_id == delete_from_account, Transactions.type != 'notposted').all()
        rows = []
        choices = []
        for count, row in enumerate(r, 1):
            rows.append(row.id)
            choices.append(count)
            print(count, '>>>>', row)

        choice_row2 = dict(zip(choices, rows))

        selection = int(input('Please select a transaction to update: '))

        transaction_to_update = 0
        for k, v in choice_row2.items():
            if selection == k:
                transaction_to_update = v

        print('transaction to update (ID):', transaction_to_update)

        update_target = s.query(Transactions).filter(Transactions.id == transaction_to_update).first()

        if update_target.type == 'transactions':
            current_dict = {
                            'id': update_target.id,
                            'date': update_target.date ,
                            'amount': update_target.amount,
                            'payee_name': update_target.payee_name,
                            'cat_id': Helper.cat_id(update_target.amount),
                            'acct_id': update_target.acct_id,
                            'type': update_target.type
                                }

            for k, v in current_dict.items():
                ui = Helper.class_optional_input(k, v)
                current_dict[k] = ui
                setattr(update_target, k, ui)
                s.commit()

            s.close()

        elif update_target.type == 'transfers':
            current_dict = {
                            'id': update_target.id,
                            'date': update_target.date ,
                            'amount': update_target.amount,
                             # 'cat_id': None,
                            'acct_id': update_target.acct_id
                                }

            inverse_amount = Decimal()

            for k, v in current_dict.items():
                ui = Helper.class_optional_input(k, v)
                current_dict[k] = ui
                amount = current_dict['amount']
                setattr(update_target, k, ui)
                s.commit()

            # 80% of use cases is either switching the transfer account or
            # changing the amount

            fixing_amount = Decimal(amount)
            i_amount = fixing_amount * -1
            setattr(update_target, 'amount2', i_amount)

            acct_id2 = Helper.class_optional_input('TRANSFER ACCOUNT', update_target.acct_id2)
            setattr(update_target, 'acct_id2', acct_id2)

            s.commit()
            s.close()

        elif update_target.type == 'splits':
            print('updating a split transaction')
            current_dict = {
                            'id': update_target.id,
                            'date': update_target.date ,
                            'ref_no': update_target.ref_no,
                            'amount': update_target.amount,
                            'split_amt1':update_target.split_amt1,
                            'payee_name': update_target.payee_name,
                            'memo':  update_target.memo,
                            'cat_id': update_target.cat_id,
                            'cat_id2': update_target.cat_id2,
                            'acct_id': update_target.acct_id,
                            'type': update_target.type
                                }

            for k, v in current_dict.items():
                ui = Helper.class_optional_input(k, v)
                current_dict[k] = ui
                setattr(update_target, k, ui)
                s.commit()

            s.close()
        else:
            pass

    @staticmethod
    def delete_transactions(s, clsname, instance):
        choice_row = Accounts.just_show_all_accounts()

        # query_entity_all = with_polymorphic(Transactions, [Transactions, Splits, Transfers])

        selection = int(input('Please select an account to delete from: '))
        delete_from_account = 0
        for k, v in choice_row.items():
            if selection == k:
                delete_from_account = v

        print('transaction delete account id:', delete_from_account)

        r = s.query(Transactions).filter(Transactions.acct_id == delete_from_account, Transactions.type != 'notposted').all()
        rows = []
        choices = []
        for count, row in enumerate(r, 1):
            rows.append(row.id)
            choices.append(count)
            print(count, '>>>>', row)

        choice_row2 = dict(zip(choices, rows))

        selection = int(input('Please select a transaction to delete: '))

        transaction_to_delete = 0
        for k, v in choice_row2.items():
            if selection == k:
                transaction_to_delete = v

        print('transaction to delete (ID):', transaction_to_delete)

        delete_target = s.query(Transactions).filter(Transactions.id == transaction_to_delete).first()

        if delete_target.type == 'transactions':
            print('deleting regular transaction')
            s.delete(delete_target)
            # s.query(query_entity_all).filter(Transactions.id == delete_target.id).\
            #             delete(synchronize_session=False)
            s.commit()
            s.close()
        elif delete_target.type == 'transfers':
            print('deleting transfers')
            s.query(Transactions).filter(Transactions.id == delete_target.id).\
                        delete(synchronize_session=False)
            s.commit()
            s.close()
        elif delete_target.type == 'splits':
            print('deleting splits')
            s.query(Transactions).filter(Transactions.id == delete_target.id).\
                     delete(synchronize_session=False)
            s.commit()
            s.close()

class NotPosted(Transactions):

    @staticmethod
    def import_staging():
        """
        This function 
            - let's user select a sheet
            - let's user select an account to import transactions 
            - renames excel sheet columns to match Transactions object
            - pushes sheet into database as type NotPosted

        It is available in cla.py as --import_func
        """

        print('you made it to import_staging')
        s = Session()
        # """
        lt = utils.Liltilities()
        path = lt.sheet_finder('for importclass', Config.DL_FILE_PATH)

        try: 
            log.info(path)
            log.debug('Need to create csv parse method.')
            with open(path) as lines:
                rows = csv.reader(lines, delimiter=',')
                headers = next(rows)
                log.info(headers)  

                records = []
                try: 
                    for rowno, row in enumerate(rows, 1):
                        if not row: # Skip rows with no data
                            continue
                        record = dict(zip(headers, row))
                        records.append(record)
                    log.info(records)
                except ValueError as e:
                    log.warning(e)
                        # return Portfolio.from_csv(lines, **opts)
            choice_row = Accounts.just_show_all_accounts()

            selection = int(input('Please select a new transaction account: '))
            account_to_add_to = 0
            for k, v in choice_row.items():
                if selection == k:
                    account_to_add_to = v

            print('new transaction account id:', account_to_add_to)

            print(headers)
            for record in records:
                posted = NotPosted(
                                date= record['Date'],
                                amount=record['Amount'],
                                payee_name=record['Payee Name'],
                                type = 'notposted',
                                cat_id=None,
                                acct_id=account_to_add_to,

                                            )
                s.add(posted)
                s.commit()
                print(posted, type(posted))

        except: 
            df = pd.read_excel(path)

          # in order to match df column names to table columns
            df = df.rename(columns=
                        {
                        "Unnamed: 6": 'id',
                        "Date": "date",
                        "Reference Number": "ref_no",
                        "Payee Name": "payee_name",
                        "Memo": "memo",
                        "Amount": "amount",
                        "Category Name": "cat_id",
                        "Unnamed: 7": "acct_id"}
                        )

            log.info(df)
            column_list = list(df.columns.values.tolist())

            choice_row = Accounts.just_show_all_accounts()

            selection = int(input('Please select a new transaction account: '))
            account_to_add_to = 0
            for k, v in choice_row.items():
                if selection == k:
                    account_to_add_to = v

            print('new transaction account id:', account_to_add_to)

            # create an Transactions object
            for index, row in df.iterrows():
                posted = NotPosted(
                                date= row['date'],
                                amount=row['amount'],
                                payee_name=row['payee_name'],
                                type = 'notposted',
                                cat_id=None,
                                acct_id=account_to_add_to,

                                            )
                s.add(posted)
                s.commit()
                print(posted)

    @staticmethod
    def controlled_transmutation():
        print('\n CONTROLLED TRANSMUTATION v1.0 2020.09.24 \n')
        s = Session()
        result = s.query(Transactions).\
            filter(Transactions.type == 'notposted').\
            order_by(Transactions.date).first()

        print(result)

        choice = int(input(' \n Press 1 to accept as regular and set category. \n Press 2 to accept as transfer. \n PRESS 3 update transaction and leave not posted#TODO. \n Press 4 to accept as split \n Press 5 to select transaction by ID #TODO \n Press 6 to delete notposted transaction and move to next \n Press 7 to go to reconciliations'))

        if choice == 1:
            NotPosted.transmute_to_reg(s, result)
        elif choice == 2:
            NotPosted.transmute_to_txfr(s, result)
        elif choice == 4:
            NotPosted.transmute_to_split(s, result)
        elif choice == 6:
            delete_target = s.query(Transactions).filter(Transactions.id == result.id).first()
                      
            print(f'\n Deleting notposted with id {result.id}\n')
            s.delete(delete_target)
            s.commit()
            s.close()

            choice = input('\n Press any key to continue to next transaction.')
            NotPosted.controlled_transmutation()
        elif choice == 7:
            Reconciliation.start()
            
    @staticmethod
    def transmute_to_split(s, result):
        print('Transmuting to split!!!!')

        print(f'TOTAL AMOUNT: {result.amount}')

        amount = input(f'New amount for first category >>>')
        amount = Decimal(amount)
    
        choice_row = Categories.just_show_all_categories()
        selection = int(input('Please apply first category: '))
        category_to_apply = 0
        for k, v in choice_row.items():
            if selection == k:
                category_to_apply = v

        print(f'\nYou selected {category_to_apply} for amount: {amount}\n')

        remaining_balance = result.amount - amount

        print(f'Remaining amount to apply: {remaining_balance}')

        ui_option = input(f'New amount for second category or press space to enter {remaining_balance} >>>')

        if ui_option == ' ':
            split_amt1 = Decimal(remaining_balance)
        else:
            split_amt1 = Decimal(ui_option)

        choice_row = Categories.just_show_all_categories()
        selection = int(input('Please select a second category: '))
        category_to_apply2 = 0
        for k, v in choice_row.items():
            if selection == k:
                category_to_apply2 = v

        print(f'\nYou selected {category_to_apply2} for amount: {split_amt1}\n')
    

        current_dict = {
                    'date': result.date,
                    'amount': amount,
                    'amount2': split_amt1,
                    'payee_name': None,
                    'type': 'splits',
                    'cat_id': category_to_apply, 
                    'cat_id2': category_to_apply2,
                    'acct_id': result.acct_id,
                    'acct_id2': None,
                    'issplit':False,
                                    }
        for k, v in current_dict.items():
            # print(k, v)
            setattr(result, k, v)
            s.commit()

        s.close()

    @staticmethod
    def transmute_to_txfr(s, result):
        # transmute the NotPosted
        choice_row = Accounts.just_show_all_accounts()

        selection = int(input('Please select a new TRANSFER account: '))
        transfer_account = 0
        for k, v in choice_row.items():
            if selection == k:
                transfer_account = v

        amount1 = Decimal(result.amount)
        amount2 = amount1 * -1

        """
        transmutes NotPosted to Transfer
        """
        current_dict = {
                    'date': result.date,
                    'amount': amount1,
                    'amount2': amount2,
                    'payee_name': None,
                    'type': 'transfers',
                    'cat_id': None,
                    'acct_id': result.acct_id,
                    'acct_id2': transfer_account,
                                    }

        for k, v in current_dict.items():
            setattr(result, k, v)
            s.commit()

        s.close()
        Reports.category_reports(date=result.date, account_id=result.acct_id)
        choice = input('\n Press any key to continue to next transaction.')
        NotPosted.controlled_transmutation()

    @staticmethod
    def transmute_to_reg(s, result):
        current_dict = {
                    'date': result.date,
                    'amount': result.amount,
                    'payee_name': result.payee_name,
                    'type': 'transactions',
                    'cat_id': Helper.cat_id(result.amount),
                    'acct_id': result.acct_id,
                                    }
        for k, v in current_dict.items():
            setattr(result, k, v)
            s.commit()

        s.close()
        # Reports.category_reports(date=result.date, account_id=result.acct_id)
        # choice = input('\n Press any key to continue to next transaction.')
        NotPosted.controlled_transmutation()

class Handler(object):

    def crud_header(clsname):
        print('*******' * 10)
        print('You are working with:', clsname, '\n')

        numeral2 = sys.modules[__name__]
        instance = getattr(numeral2, clsname)

        print("*******" * 10)

        return instance

    def display_names(instance):
        display_names = []
        for item in dir(instance):
            if not item.startswith('_'):
                display_names.append(item)
        display_names.remove('metadata')

        return display_names

    @staticmethod
    def create_handler(clsname):
        instance = Handler.crud_header(clsname)
        s = Session()
        display_names = Handler.display_names(instance)

        if instance == Accounts:
            new_record = Accounts.create_accounts(s, clsname,instance, display_names)
        elif instance == Categories:
            new_record = Categories.create_categories(s, clsname, instance, display_names)
        elif instance == Transactions:
            new_record = Transactions.create_transactions(s, clsname,instance, display_names)
        elif instance == Transfers: # this is just one way to get here
            new_record = Transfers.create_transfers(s, clsname,instance, display_names)

        s.close()

    @staticmethod
    def read_handler(clsname):
        instance = Handler.crud_header(clsname)
        s = Session()
        display_names = Handler.display_names(instance)

        if instance == Accounts:
            new_record = Accounts.just_show_all_accounts()
        elif instance == Categories:
            new_record = Categories.just_show_all_categories()
        elif instance == Transactions:
            new_record = Transactions.just_show_all_transactions()

        s.close()

    @staticmethod
    def delete_handler(clsname):
        instance = Handler.crud_header(clsname)
        s = Session()

        if instance == Accounts:
            Accounts.delete_accounts(s, clsname, instance)
        elif instance == Categories:
            Categories.delete_categories(s, clsname, instance)
        elif instance == Transactions:
            Transactions.delete_transactions(s, clsname, instance)
        else:
            print('07 30 worked fucked up in delete handler')

    @staticmethod
    def update_handler(clsname):
        instance = Handler.crud_header(clsname)
        s = Session()

        if instance == Accounts:
            Accounts.update_accounts(s, clsname, instance)
        elif instance == Categories:
            Categories.update_categories(s, clsname, instance)
        elif instance == Transactions:
            Transactions.update_transactions(s, clsname, instance)
        else:
            print('07 30 worked fucked up in delete handler')

class Helper(object):

    @staticmethod
    def cat_id(amt):
        s = Session()
        amount = Decimal(amt)
        # if amount >= 0:
        #     cat_option = s.query(Categories).filter(Categories.inorex == 'income').all()
        # else:
        #     cat_option = s.query(Categories).filter(Categories.inorex == 'expense').all()
        choice_row = Categories.just_show_all_categories()
        selection = int(input('Please apply a category: '))
        category_to_apply = 0
        for k, v in choice_row.items():
            if selection == k:
                category_to_apply = v

        print(category_to_apply)

        print(f'Entering transactions to category: {category_to_apply}')
        category = s.query(Categories).filter(Categories.id == category_to_apply).first()
        cat_id = category.id
        cat_name = category.name
        print(category.id, "******", category.name)

        return cat_id

    @staticmethod
    def fancy_int_input(**kwargs):
        for item in kwargs.values():
            ui = int(input(f'New {item}?'))
            return ui

    @staticmethod
    def fancy_input(**kwargs):
        for item in kwargs.values():
            ui = input(f'New {item} >>>')
            return ui

    @staticmethod
    def class_optional_input(string, default):
        ui = input(f'New {string} or press SPACE to leave at {default}>>>')
        if ui == ' ':
            return default
        else:
            return ui

    @staticmethod
    def fancy_optional_input(**kwargs):
        for item in kwargs.values():
            ui = input(f'New {item} or press SPACE to leave unchanged >>>')
            return ui

    @staticmethod
    def export_excel():
        """Get transactionlist as sql"""
        df = pd.read_sql('transactionlist', engine)
    
        today = date.today()
        str_date = str(today)

        new_asus_path = Path(
            f'C:/Users/joewa/Google Drive/pythonwork/projects/numeral2/export/export{str_date}.xlsx')
        writer = pd.ExcelWriter(new_asus_path)
        df.to_excel(writer, 'Shee1')
        writer.save()

    @staticmethod
    def show_after_posting(date, account_id):
        """This function is supposed to help me keep track of where I am 
        after I post a transaction.  Note: it only shows the transactions and breakdown for the month of the POSTED TRANSACTION i was just working with
        """
        """
        this is the first function where I learned about the date.month deal with datetime.  learning worth weight in goald
        
        TODO: sync this with category reports and sync category reports with this
        """
        s = Session()
    
        month = date.month
        txn_results = s.query(Transactions).filter(extract('month', Transactions.date)==month).filter(Transactions.type != 'notposted').all()

        month_total_expenses = []
        month_total_income = []
        for count, item in enumerate(txn_results, 1):
            """this would not pickup amount 2"""
            """probably want to do a monthly total col if I haven't already"""
            if item.amount > 0:
                month_total_income.append(item.amount)
            elif item.amount < 0:
                month_total_expenses.append(item.amount)
            else:
                month_total_expenses.append(item.amount)
            print(count, ">", item)
            print(" " * 10)

        name_list = []
        stuff_list = []
        for item in s.query(Categories).all():
            for stuff in s.query(Transactions).filter(Transactions.cat_id == item.id).all():
                name_list.append(item.name)
                stuff_list.append(stuff.amount)
                print(item.id, item.name)
        print(name_list)
        result = {i: [] for i in name_list}
        for i, j in zip(name_list, stuff_list):
            result[i].append(j)

        total = []
        for k, v in result.items():
            total.append(sum(v))
            print(k, sum(v))

        print('*' * 20)
        print('total month expenses', sum(month_total_expenses))
        print('total month income', sum(month_total_income))

        print('total all time:', sum(total))

class Reports(object):

    @staticmethod
    def show_posted_transactions():
        """
        This is a start, goddammit.
        This function shows just posted transactions, be they Transfers, Splits, or reglur ol' Transactions

        This function is also the first to incorporate the sorting mechanism
        for transfers and transactions with acct_id & acct_id2
        """
        s = Session()
        choice_row = Accounts.just_show_all_accounts()

        # query_entity_all = with_polymorphic(Transactions, [Transactions, Splits, Transfers])
        selection = int(input('Please select an account to view posted transactionlists: '))
        view_account = 0
        for k, v in choice_row.items():
            if selection == k:
                view_account = v

        print('view posted transactions account id:', view_account)
        results = []
        r = s.query(Transactions).filter(Transactions.acct_id2 == view_account, Transactions.type != 'notposted').all()
        r2 = s.query(Transactions).filter(Transactions.acct_id == view_account, Transactions.type != 'notposted').all()
        for item in r:
            results.append(item)
        for item in r2:
            results.append(item)

        bal_list = []
        starting_balance = s.query(Accounts).filter(Accounts.id == view_account).first()
        print('\nstarting balance:', starting_balance.startbal, '\n')

        for item in results:
            cat = s.query(Categories).filter(Categories.id == item.cat_id).first()
            if cat is None:
                cat = 'empty'
                print('converted empty cat name probably will clean this up')
            else:
                cat = cat.name


            if item.type == 'transfers' and item.acct_id2 == view_account:
                bal_list.append(item.amount2)
                print('transfer', item.amount2, cat)
            elif item.type == 'transfers' and item.acct_id== view_account:
                bal_list.append(item.amount)
                print('transfer', item.amount, cat)
            elif item.type == 'transactions':
                bal_list.append(item.amount)
                print('transaction', item.amount, cat)


        # for item in posted_sum:
        #     posted_sum_decimal = item

        cur_bal = Decimal(starting_balance.startbal) + sum(bal_list)

        print('\ncurrent balance:', cur_bal)

        # rows = []
        # choices = []
        # for count, row in enumerate(r, 1):
        #     rows.append(row.id)
        #     choices.append(count)
        #     print(count, '>>>>', row, cat)

    @staticmethod
    def show_notposted_transactions():
        """
        Test function, we will figure out how to improve this with practice.
        Shows only notposted transactions
        """
        s = Session()
        choice_row = Accounts.just_show_all_accounts()


        query_entity_all = with_polymorphic(Transactions, NotPosted)
        selection = int(input('Please select an account to view posted transactionlists: '))
        view_account = 0
        for k, v in choice_row.items():
            if selection == k:
                view_account = v

        print('transaction update account id:', view_account)

        r = s.query(query_entity_all).filter(Transactions.type == 'notposted' ).all()
        rows = []
        choices = []
        for count, row in enumerate(r, 1):
            rows.append(row.id)
            choices.append(count)
            print(count, '>>>>', row)

    @staticmethod
    def back_calc_posted():
        """
        This function let's user pick an account,
            -shows that accounts starting balance+
            -shows the current balance of that account based on
            posted transactions+
            -and absolutely nothing else
        """
        s = Session()
        choice_row = Accounts.just_show_all_accounts()

        query_entity_all = with_polymorphic(Transactions, [Transactions, Splits, Transfers])
        selection = int(input('Please select an account to view posted transactionlists: '))
        view_account = 0
        for k, v in choice_row.items():
            if selection == k:
                view_account = v

        account = s.query(Accounts).filter(Accounts.id == view_account).first()

        print('view posted transactions account id:', view_account)

        r = s.query(query_entity_all).filter(Transactions.type != 'notposted' ).all()

        rows = []
        choices = []

        print('\nstarting balance:', account.startbal)

        for count, row in enumerate(r, 1):
            rows.append(row.id)
            choices.append(count)
            print(count, '>>>>', row)

        bal_list = []

        posted_sum = s.query(func.sum(Transactions.amount).filter(Accounts.id == 1, Transactions.type != 'notposted')).first()
        for item in posted_sum:
            posted_sum_decimal = item

        cur_bal = Decimal(account.startbal) + posted_sum_decimal

        print('\ncurrent balance:', cur_bal)

    @staticmethod
    def net_worth():
        s = Session()
        result = s.query(Accounts).all()
        print(result)
        for row in result:
            cum_sum = [row.startbal for row in result if row.type == 'asset']
            cum_liability = [row.startbal for row in result if row.type == 'liability']

        assets = 0
        for item in cum_sum:
            assets += item

        liability = 0
        for item in cum_liability:
            liability += item

        print(f'Starting balance @ 01/01/2020 = {assets}')
        print(f'Starting liability @ 01/01/2020 = {liability}')
        print(f'Starting net worth @ 01/01/2020 = {assets - liability}')

        r = s.query(Accounts).order_by(Accounts.id)

        cur_bal_list = []
        for count, row in enumerate(r, 1):
            cur_bal = Accounts.current_balance_for_just_show_all_accounts(row.id)
            cur_bal_list.append(cur_bal)

        print('Last net worth is = ', sum(cur_bal_list))

    @staticmethod
    def category_reports(**kwargs):
        """
        This is my main report.
        This works with split.

        #TODO fix this fucking issue with kwargs{date}.month (why isn't this excepting)
        #TODO this hangs for some fucking reason in controlled transmutation: it does not need to be this generically-applicable or detailed but I do like being able to see my last transaction
        """
        s = Session()

        # if isinstance(kwargs['date'], str):
        #     month_str = kwargs['date']
        #     month = month_str[0:2]
        # else:
        #     try:
        #         month = kwargs['date'].month
        #     except KeyError as e:
        #         print(e)
        month = int(input('Please enter 2-digit month.'))

        txn_results = s.query(Transactions).filter(extract('month', Transactions.date)==month).filter(Transactions.type != 'notposted').all()
        
        month_total_expenses = []
        month_total_income = []
        month_net_transfers = []
        for count, item in enumerate(txn_results, 1):
            """this would not pickup amount 2"""
            """probably want to do a monthly total col if I haven't already"""

            if item.type == 'splits':
                print(count, ">", item, 'cat2:', item.cat_id2, 'amt2:', item.amount2)
                if item.amount > 0:
                    month_total_income.append(item.amount)
                    month_total_income.append(item.amount2)
                elif item.amount < 0:
                    month_total_expenses.append(item.amount)
                    month_total_expenses.append(item.amount2)
                else:
                    month_total_expenses.append(item.amount)
            elif item.type == 'transactions':
                print(count, '*', item)
                if item.amount > 0:
                    month_total_income.append(item.amount)
                elif item.amount < 0:
                    month_total_expenses.append(item.amount)
                else:
                    month_total_expenses.append(item.amount)
            elif item.type == 'transfers':
                print(count, '*', item)
                if item.amount > 0:
                    month_net_transfers.append(item.amount)
                elif item.amount < 0:
                    month_net_transfers.append(item.amount)
                else:
                    month_net_transfers.append(item.amount)
            print(" " * 10)
   
        name_list = []
        stuff_list = []
        for item in s.query(Categories).all():
            for stuff in s.query(Transactions).filter(or_(Transactions.cat_id == item.id, Transactions.cat_id2 == item.id)).all():
                name_list.append(item.name)
                stuff_list.append(stuff.amount)
                if stuff.amount2 != None:
                    stuff_list.append(stuff.amount2)
                # print(stuff.amount2)

        result = {i:[] for i in name_list}
        for i,j in zip(name_list, stuff_list):
            result[i].append(j)

        total = []
        for k,v in result.items():
            total.append(sum(v))
            print(f'{k:>25} | {sum(v):<}')

    
        print('*' * 20)
        print('total monthly net transfers', sum(month_net_transfers))
        print('total month expenses', sum(month_total_expenses))
        print('total month income', sum(month_total_income))

        print('total all time:', sum(total))
    
    @staticmethod
    def summary_reports(month):
        """
        This isnot bad it has the extract month thing in it that we need to fux wit
        """
        s = Session()

        # get a date range (I can pass in a month)
        # for all transactions in that range, get all transactions
        txn_results = s.query(Transactions).filter(extract('month', Transactions.date)==month).\
            join(Accounts, Accounts.id == Transactions.acct_id).all()

        for count, item in enumerate(txn_results, 1):
            print(count, ">", item, "account:", item.txn.acct_name, "* type:", item.cat.inorex, "* category:", item.cat.name)
            print(" " * 10)

        cat_results = s.query(Categories).all()
        cat_names = {cat.name:cat.id for cat in cat_results}
        end_cat = {cat.name:0 for cat in cat_results}

        for k in txn_results:
            for key, v in cat_names.items():
                if k.cat_name == v:
                    print(v)
                    print("OK")
                    end_cat[key] += k.amount

        print("*****" * 8, '\n')
        print(f"Transactions for {month} 2020")
        print("*****" * 8)

        for k, v in end_cat.items():
            print(k, v)

    @staticmethod
    def show_transactions_by_account():
        """
        THIS IS A PROPER IMPLEMENTATION OF TRANSFER TOTALLING
        """
        """
        This function allows user: 
        *to pick an account

        *and returns ALL transactions for that account (transfers picked correctly)

        *querying on both acct_id and acct_id2

        *show curbal
        """
        s = Session()
        choice_row = Accounts.just_show_all_accounts()
        selection = int(input('Please select account to view transactions: '))
        view_txn_account = 0
        for k, v in choice_row.items():
            if selection == k:
                view_txn_account = v

        print('view transactions for account id:', view_txn_account)

        r = s.query(Transactions).filter(or_(Transactions.acct_id == view_txn_account, Transactions.acct_id2==view_txn_account)).order_by(Transactions.date).all()

        amount2_total = 0
        amount_total = 0

        start_bal = s.query(Accounts).filter(Accounts.id == view_txn_account).first()

        print(start_bal.startbal)
        starting_balance = Decimal(start_bal.startbal)
        print(type(starting_balance))
       
        for item in r:
            """this is where the magic happens: where transfers get sorted and amount2 accumulated into current balance"""
            if item.acct_id2 == view_txn_account:
                amount2_total += item.amount2
                print(f'>>>> {item.id}| {item.date} {item.amount2:>10} {item.type:<15} cat: {item.cat_id}')
            elif item.acct_id == view_txn_account:
                amount_total += item.amount
                print(f'>>>> {item.id}| {item.date} {item.amount:>10} {item.type:<15} cat: {item.cat_id}')

    
        current_balance = (amount2_total + amount_total) + starting_balance
        print('current balance:', current_balance) 
        #pop in date

    @staticmethod
    def all_accounts_bym_bycat():
        """What do I need to pull this off? 
        I want this real nice polished report type thing, will compare with 
        *must eventually get credit card

        YEAR
        get all transactions
        """
        s = Session()

        year1 = date.today().year
        month = date.today().month
        day = date.today().day

        strt_dt = date(year1, 1, 1)
        end_dt = date(year1, month, day)

        dates = [dt for dt in rrule(MONTHLY, dtstart=strt_dt, until=end_dt)]

        for item2 in dates:
            name_list = []
            stuff_list = []
            for item in s.query(Categories).all():
                for stuff in s.query(Transactions).\
                                filter(or_(Transactions.cat_id == item.id, Transactions.cat_id2 == item.id)).\
                                filter(extract('month', Transactions.date) == item2.month).\
                                filter(Transactions.type != 'notposted').\
                                filter(Transactions.type != 'transfers').all():
                    name_list.append(item.name)
                    stuff_list.append(stuff.amount)
                    if stuff.amount2 != None:
                        stuff_list.append(stuff.amount2)
           
            txfr_amount_list1 = []
            txfr_amount_list2 = []
            for transfers in s.query(Transactions).\
                                filter(extract('month', Transactions.date) == item2.month).\
                                filter(Transactions.type == 'transfers').\
                                filter(Transactions.type != 'notposted').all():
                txfr_amount_list1.append(transfers.amount)
                txfr_amount_list2.append(transfers.amount2)


            result = {i:[] for i in name_list}
            for i,j in zip(name_list, stuff_list):
                result[i].append(j)

            total = []
            print(year1, 'month:', item2.month)
            for k,v in result.items():
                total.append(sum(v))
                print(f'{k:>25} | {sum(v):<}')

            print('transfers IN:', sum(txfr_amount_list1))
            print('transfers OUT:', sum(txfr_amount_list2))
            net_txfr = sum(txfr_amount_list1) + sum(txfr_amount_list2)
            print('net transfers:', net_txfr)


            """Get rid of double entries by only picking MAIN acct_id and not acct_id2
            """

    @staticmethod
    def full_year_expenses():
        """
        YEAR
        get all transactions
        """
        s = Session()

        year1 = date.today().year
        # month = date.today().month
        # day = date.today().day

        # strt_dt = date(year1, 1, 1)
        # end_dt = date(year1, month, day)

        # dates = [dt for dt in rrule(MONTHLY, dtstart=strt_dt, until=end_dt)]

        # for item2 in dates:
        name_list = []
        stuff_list = []
        for item in s.query(Categories).all():
            for stuff in s.query(Transactions).\
                            filter(or_(Transactions.cat_id == item.id, Transactions.cat_id2 == item.id)).\
                            filter(extract('year', Transactions.date) == year1).\
                            filter(Transactions.type != 'notposted').\
                            filter(Transactions.type != 'transfers').all():
                name_list.append(item.name)
                stuff_list.append(stuff.amount)
                if stuff.amount2 != None:
                    stuff_list.append(stuff.amount2)
           
            txfr_amount_list1 = []
            txfr_amount_list2 = []
            for transfers in s.query(Transactions).\
                                filter(extract('year', Transactions.date) == year1).\
                                filter(Transactions.type == 'transfers').\
                                filter(Transactions.type != 'notposted').all():
                txfr_amount_list1.append(transfers.amount)
                txfr_amount_list2.append(transfers.amount2)


            result = {i:[] for i in name_list}
            for i,j in zip(name_list, stuff_list):
                result[i].append(j)

            total = []
            headers = []
            figures = []
            # print(year1, 'year1:')
            for k,v in result.items():
                total.append(sum(v))
                headers.append(k)
                figures.append(sum(v))
                # print(f'{k:>25} | {sum(v):<}')

        print('transfers IN:', sum(txfr_amount_list1))
        print('transfers OUT:', sum(txfr_amount_list2))
        net_txfr = sum(txfr_amount_list1) + sum(txfr_amount_list2)
        print('net transfers:', net_txfr)

        return headers, figures, sum(txfr_amount_list1), sum(txfr_amount_list2)


    @staticmethod
    def transaction_report(filter=None, account=None, date=None, cat=None):
        s = Session()

        if filter == 'account':
            r = s.query(Transactions).\
                    filter(or_(Transactions.acct_id == account, Transactions.acct_id2 == account)).\
                    filter(Transactions.type != 'notposted').\
                        order_by(Transactions.date).all()
                    # filter(Transactions.type != 'transfers').\
                            # include transfers in transaction report
            log.debug(r)
            return r
        elif filter == 'date':
            start_date = '2020-09-01'
            stop_date = '2020-10-01'
            r = s.query(Transactions).\
                    filter(or_(Transactions.acct_id == account, Transactions.acct_id2 == account)).\
                    filter(Transactions.type != 'notposted').\
                    filter(Transactions.date.between(start_date, stop_date)).\
                        order_by(Transactions.date).all()
                    # filter(Transactions.type != 'transfers').\
                            # include transfers in transaction report
            log.debug(r)
            return r
        elif filter == 'category':
            pass
        
class Reconciliation(object):
    """The basic structure of a reconciliation is 

    1) pick account
    2) start date
    3) end date
    4) get transactions for that period for that account

    Args:
        object ([type]): [description]
    """
    @staticmethod
    def start():
        s = Session()
        choice_row = Accounts.just_show_all_accounts()
        selection = int(input('Please select account to reconcile: '))
        account_to_reconcile = 0
        for k, v in choice_row.items():
            if selection == k:
                account_to_reconcile = v

        print('reconciliation account id:', account_to_reconcile)

        date_entry = input('Enter a start date from statement (i.e. 2017/07/21)')
        year, month, day = map(int, date_entry.split('/'))
        strt_dt = date(year, month, day)

        date_entry = input('Enter an end date from statement (i.e. 2017/07/21)')
        year, month, day = map(int, date_entry.split('/'))
        end_dt = date(year, month, day)

        prior_month_end_bal = Decimal(input('Please enter a prior month ending balance: '))
        statement_end_bal = Decimal(input('Please enter statement ending balance: '))

        stuff_check = []
        for stuff in s.query(Transactions).\
            filter(or_(Transactions.acct_id == account_to_reconcile, Transactions.acct_id2 == account_to_reconcile)).\
            filter(Transactions.date >= strt_dt, Transactions.date <= end_dt ).\
            order_by(Transactions.date).all():
            stuff_check.append(stuff)

        start_bal = s.query(Accounts).filter(
                Accounts.id == account_to_reconcile).first()

        starting_balance = Decimal(start_bal.startbal)

        start = prior_month_end_bal
        print('---' * 30)
        for item in stuff_check:
            """if matching account is is acct_id then use amount, else use amount2"""
            if item.acct_id == account_to_reconcile:
                run_bal = start + item.amount
                print(item, run_bal)
                start = run_bal
            elif item.acct_id2 == account_to_reconcile:
                run_bal = start + item.amount2
                print(item, run_bal)
                start = run_bal


        discrepancy = 0        
        acct_end_bal = start
        discrepancy = acct_end_bal - statement_end_bal

        print(f'\nCurrent difference {discrepancy}.')
        
        print(f'\nShowing items from account {account_to_reconcile} from {strt_dt} to {end_dt}.\n')

class Export(object):
    
    @staticmethod
    def to_csv(data, header=None, transfers=None):
        '''
        only works for full year now
        '''
        fig_gen = (str(fig) for fig in data)
        with open('output_here/output.csv', 'w', newline='') as csvfile:
            cw = csv.writer(csvfile)

            if headers:
                cw.writerow(headers)

            cw.writerow(fig_gen)

            if transfers:
                transfer_gen = (str(tsfr) for tsfr in transfers)

                cw.writerow(transfer_gen)

             
if __name__ == "__main__":
    Reports.transaction_report(filter='date', account=1)
    '''
    what kinds of things would we want to do:
    * select by account
    * select by range of dates
    * select by category

    * sort into period by month, year, quarter, day
    * sum by period
    * refine filter

    * search
    '''


    # headers, figures, transfer_in, transfer_out = Reports.full_year_expenses()
    # Export.to_csv(figures, header=headers, transfers=[transfer_in, transfer_out])
