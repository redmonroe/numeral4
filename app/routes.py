from app import app
from decimal import Decimal
from datetime import date
from app.models import MyQuery, sessionmaker, Session, engine, User, Categories, Reports, Accounts, Transactions, Base, and_, or_, extract
from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from app.forms import LoginForm, RegistrationForm, AccountCreationForm, CategoryCreationForm, TransactionCreationForm, PostEngineForm, EditAccountForm, EditCategoryForm, EditTransactionForm, ReportSelectForm
from werkzeug.urls import url_parse
import pandas as pd
from sqlalchemy.exc import ProgrammingError


# TODO:
# anything not categorized should be uncategorized
# create
# delete
# update
# import, posting, adding categories
# reports: annual expenses by month
# export
# reconciliation


@app.route('/')
@app.route('/index')
@login_required
def index():
    string = 'hello world this is numeral4.  I am born December 10, 2020.'
    return render_template('index.html', title='sign in', string=string)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        s = Session()
        user = s.query(User).filter_by(username=form.username.data).first()
        print('this is user;;;;;', user)

        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))

        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='sign in', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    s = Session()
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        s.add(user)
        s.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/user/<username>')
@login_required
def user(username):
    s = Session()
    user = s.query(User).filter_by(username=username).first()

    accounts = s.query(Accounts).filter_by(Accounts.user_id == user.id).all()

    return render_template('user.html', user=user, accounts=accounts)


@app.route('/accounts/<username>/')
@login_required
def accounts(username):
    s = Session()
    user = s.query(User).filter_by(username=username).first()

    r = s.query(Accounts).filter(Accounts.user_id == user.id).all()

    return render_template('view_accounts.html', items=r)


@app.route('/create_account/<username>/', methods=['GET', 'POST'])
@login_required
def create_account(username):
    s = Session()
    user = s.query(User).filter_by(username=username).first()

    r = s.query(Accounts).filter(Accounts.user_id == user.id).all()

    form = AccountCreationForm()
    if form.validate_on_submit():
        new_account = Accounts()
        new_account.acct_name = form.acct_name.data
        new_account.startbal = form.startbal.data
        new_account.type = form.type.data
        new_account.status = form.status.data
        new_account.user_id = user.id
        s.add(new_account)
        s.commit()
        flash('congratulations, you created a new account')
        # post/redirect/get pattern
        return redirect(url_for('accounts', username=username))
    return render_template('create_account.html', form=form)


@app.route('/edit_account/<username>/<id>', methods=['GET', 'POST'])
@login_required
def edit_account(username, id):
    s = Session()
    user = s.query(User).filter_by(username=username).first()

    r = s.query(Accounts).filter(Accounts.user_id == user.id).all()

    account = s.query(Accounts).get(id)

    form = EditAccountForm(obj=account)
    if form.validate_on_submit():
        account.acct_name = form.acct_name.data
        account.startbal = form.startbal.data
        account.type = form.type.data
        account.status = form.status.data
        account.user_id = user.id
        s.commit()
        s.close()
        flash('congratulations, you created a new account')
        # post/redirect/get pattern
        return redirect(url_for('accounts', username=username))
    return render_template('edit_account.html', form=form)


@app.route('/delete_account/<username>', methods=['GET', 'POST'])
@login_required
def delete_account(username):
    s = Session()
    user = s.query(User).filter_by(username=username).first()

    r = s.query(Accounts).filter(Accounts.user_id == user.id).all()

    # flash('congratulations, you created a new account')
    # return redirect(url_for('delete_account', username=username)) #post/redirect/get pattern
    return render_template('delete_account.html', items=r)


@app.route('/deleted/<username>/<id>', methods=['GET', 'POST'])
@login_required
def deleted(username, id):
    s = Session()
    user = s.query(User).filter_by(username=username).first()

    r = s.query(Accounts).get(id)

    s.delete(r)
    s.commit()

    flash('congratulations, you deleted an account')
    # post/redirect/get pattern
    return redirect(url_for('accounts', username=username))


@app.route('/account_register/<username>/<id>', methods=['GET', 'POST'], defaults={"page": 1})
@app.route('/account_register/<username>/<id>/<int:page>', methods=['GET'])
@login_required
def account_register(username, id, page):
    s = Session()
    user = s.query(User).filter_by(username=username).first()
    '''current balance
    this need consolidation
    '''
    print(id, username, page)

    results = []
    r = s.query(Transactions).filter(Transactions.acct_id2 ==
                                     id, Transactions.type != 'notposted').all()
    r2 = s.query(Transactions).filter(Transactions.acct_id ==
                                      id, Transactions.type != 'notposted').all()
    for item in r:
        results.append(item)
    for item in r2:
        results.append(item)

    bal_list = []
    starting_balance = s.query(Accounts).filter(Accounts.id == id).first()
    print('ok', starting_balance.startbal)

    for item in results:
        if item.type == 'transfers' and item.acct_id2 == id:
            bal_list.append(item.amount2)
        elif item.type == 'transfers' and item.acct_id == id:
            bal_list.append(item.amount)
        elif item.type == 'transactions':
            bal_list.append(item.amount)

    # print("ballise:", bal_list)
    print('bal_list sum', sum(bal_list))
    curbal = Decimal(starting_balance.startbal) + sum(bal_list)
    print('curbal', curbal)

    '''
    transaction: below
    '''

    r = s.query(Transactions).filter(Transactions.user_id == user.id,
                                     Transactions.type != 'notposted').order_by(Transactions.date).all()

    CustomSession = sessionmaker(
        bind=engine, query_cls=MyQuery, expire_on_commit=False)

    s = CustomSession()
    q = MyQuery(Transactions, s)

    items = q.filter(Transactions.user_id == user.id, Transactions.type != 'notposted').order_by(
        Transactions.date).paginate(page, per_page=10, error_out=False)

    return render_template('account_register.html', startbal=starting_balance, items=items, curbal=curbal, id=id)


@app.route('/categories/<username>')
@login_required
def categories(username):
    s = Session()
    user = s.query(User).filter_by(username=username).first()

    r = s.query(Categories).filter(Categories.user_id == user.id).all()

    return render_template('view_categories.html', items=r)


@app.route('/create_category/<username>/', methods=['GET', 'POST'])
@login_required
def create_category(username):
    s = Session()
    user = s.query(User).filter_by(username=username).first()

    r = s.query(Categories).filter(Categories.user_id == user.id).all()

    form = CategoryCreationForm()
    if form.validate_on_submit():
        new_cat = Categories()
        new_cat.id = None
        new_cat.name = form.name.data
        new_cat.inorex = form.inorex.data
        new_cat.user_id = user.id
        s.add(new_cat)
        s.commit()
        s.close()
        flash('congratulations, you created a new category')
        # post/redirect/get pattern
        return redirect(url_for('categories', username=username))

    return render_template('create_categories.html', form=form)


@app.route('/edit_category/<username>/<id>', methods=['GET', 'POST'])
@login_required
def edit_category(username, id):
    s = Session()
    user = s.query(User).filter_by(username=username).first()

    r = s.query(Categories).filter(Categories.user_id == user.id).all()

    categories = s.query(Categories).get(id)

    form = EditCategoryForm(obj=categories)
    if form.validate_on_submit():

        categories.name = form.name.data
        categories.inorex = form.inorex.data
        categories.user_id = user.id
        s.commit()
        s.close()
        flash('congratulations, you created a new category')
        # post/redirect/get pattern
        return redirect(url_for('categories', username=username))

    return render_template('edit_categories.html', form=form)


@app.route('/delete_category/<username>', methods=['GET', 'POST'])
@login_required
def delete_category(username):

    s = Session()
    user = s.query(User).filter_by(username=username).first()

    r = s.query(Categories).filter(Categories.user_id == user.id).all()

    return render_template('delete_category.html', items=r)


@app.route('/deletedcat/<username>/<id>', methods=['GET', 'POST'])
@login_required
def deletedcat(username, id):
    s = Session()
    user = s.query(User).filter_by(username=username).first()

    r = s.query(Categories).get(id)

    s.delete(r)
    s.commit()
    s.close()

    flash('congratulations, you deleted an account')
    # post/redirect/get pattern
    return redirect(url_for('categories', username=username))


@app.route('/transactions/<username>', methods=['GET'], defaults={"page": 1})
@app.route('/transactions/<username>/<int:page>', methods=['GET'])
@login_required
def transactions(username, page):
    s = Session()
    user = s.query(User).filter_by(username=username).first()
    '''current balance
    this need consolidation
    '''

    try:
        results = []
        r = s.query(Transactions).filter(Transactions.acct_id2 ==
                                         id, Transactions.type != 'notposted').all()
        r2 = s.query(Transactions).filter(Transactions.acct_id ==
                                          id, Transactions.type != 'notposted').all()
        for item in r:
            results.append(item)
        for item in r2:
            results.append(item)

        bal_list = []
        starting_balance = s.query(Accounts).filter(Accounts.id == id).first()

        for item in results:
            if item.type == 'transfers' and item.acct_id2 == id:
                bal_list.append(item.amount2)
            elif item.type == 'transfers' and item.acct_id == id:
                bal_list.append(item.amount)
            elif item.type == 'transactions':
                bal_list.append(item.amount)

        curbal = Decimal(starting_balance.startbal) + sum(bal_list)
        print(curbal)
    except ProgrammingError as e:
        curbal = 0
        print(e, 'You probably do not have any transactions.')
    '''
    transaction: below
    '''

    r = s.query(Transactions).filter(Transactions.user_id == user.id,
                                     Transactions.type != 'notposted').order_by(Transactions.date).all()

    CustomSession = sessionmaker(
        bind=engine, query_cls=MyQuery, expire_on_commit=False)

    s = CustomSession()
    q = MyQuery(Transactions, s)

    items = q.filter(Transactions.user_id == user.id, Transactions.type != 'notposted').order_by(
        Transactions.date).paginate(page, per_page=10, error_out=False)

    return render_template('view_transactions.html', items=items, curbal=curbal)


@app.route('/create_transaction/<username>/', methods=['GET', 'POST'])
@login_required
def create_transaction(username):
    s = Session()
    user = s.query(User).filter_by(username=username).first()

    # r = s.query(Transactions).filter(Transactions.user_id==user.id).all()

    ''' code to create dynamics account list for form'''
    account_choice = s.query(Accounts).filter(
        Accounts.user_id == user.id).all()

    account_list = [(item.id, item.acct_name) for item in account_choice]

    ''' code to create dynamic category list for form'''
    category_choice = s.query(Categories).filter(
        Categories.user_id == user.id).all()

    cat_list = [(item.id, item.name) for item in category_choice]

    '''transaction type list is not dynamic at this time'''

    form = TransactionCreationForm()
    '''form choices passed to form after creation of form'''
    form.acct_id.choices = account_list
    form.cat_id.choices = cat_list
    if form.validate_on_submit():
        new_txn = Transactions()
        new_txn.type = form.type.data
        new_txn.date = form.date.data
        new_txn.amount = form.amount.data
        new_txn.payee_name = form.payee_name.data
        new_txn.acct_id = form.acct_id.data
        new_txn.cat_id = form.cat_id.data
        new_txn.user_id = user.id
        s.add(new_txn)
        s.commit()
        s.close()
        flash('congratulations, you created a new transaction')
        # post/redirect/get pattern
        return redirect(url_for('create_transaction', username=username))

    return render_template('create_transaction.html', form=form)


@app.route('/edit_transaction/<username>/<id>', methods=['GET', 'POST'])
@login_required
def edit_transaction(username, id):
    s = Session()
    user = s.query(User).filter_by(username=username).first()

    # r = s.query(Transactions).filter(Transactions.user_id==user.id).all()

    ''' code to create dynamics account list for form'''
    account_choice = s.query(Accounts).filter(
        Accounts.user_id == user.id).all()

    account_list = [(item.id, item.acct_name) for item in account_choice]

    ''' code to create dynamic category list for form'''
    category_choice = s.query(Categories).filter(
        Categories.user_id == user.id).all()

    cat_list = [(item.id, item.name) for item in category_choice]

    '''transaction type list is not dynamic at this time'''

    transaction = s.query(Transactions).get(id)

    form = EditTransactionForm(obj=transaction)
    '''form choices passed to form after creation of form'''
    form.acct_id.choices = account_list
    form.cat_id.choices = cat_list
    if form.validate_on_submit():

        transaction.type = form.type.data
        transaction.date = form.date.data
        transaction.amount = form.amount.data
        transaction.payee_name = form.payee_name.data
        transaction.acct_id = form.acct_id.data
        transaction.cat_id = form.cat_id.data
        transaction.user_id = user.id

        s.commit()
        s.close()
        flash('congratulations, you created a new transaction')
        # post/redirect/get pattern
        return redirect(url_for('create_transaction', username=username))

    return render_template('create_transaction.html', form=form)


@app.route('/delete_transaction/<username>', methods=['GET', 'POST'])
@login_required
def delete_transaction(username):

    s = Session()
    user = s.query(User).filter_by(username=username).first()

    r = s.query(Transactions).filter(Transactions.user_id == user.id).all()

    return render_template('delete_transaction.html', items=r)


@app.route('/deletedtrxn/<username>/<id>', methods=['GET', 'POST'])
@login_required
def deletedtrxn(username, id):
    s = Session()
    user = s.query(User).filter_by(username=username).first()

    r = s.query(Transactions).get(id)

    s.delete(r)
    s.commit()
    s.close()

    flash('congratulations, you deleted a transaction!')
    return redirect(url_for('transactions', username=username))


@app.route('/unposted/<username>/', methods=['GET'], defaults={"page": 1})
@app.route('/unposted/<username>/<int:page>', methods=['GET'])
@login_required
def unposted(username, page):
    s = Session()
    user = s.query(User).filter_by(username=username).first()

    r = s.query(Transactions).filter(Transactions.user_id == user.id,
                                     Transactions.type == 'notposted').order_by(Transactions.date).all()

    '''
    pagination test goes here
    '''
    CustomSession = sessionmaker(
        bind=engine, query_cls=MyQuery, expire_on_commit=False)
    '''
    CustomSession should still have filter, order_by, etc
    '''
    s = CustomSession()
    q = MyQuery(Transactions, s)

    items = q.filter(Transactions.user_id == user.id, Transactions.type == 'notposted').order_by(
        Transactions.date).paginate(page, per_page=10, error_out=False)

    for page in items.iter_pages():
        print(page)

    # form = TransactionCreationForm()
    # if form.validate_on_submit():
    #     new_txn = Transactions()
    #     new_txn.date = form.date.data
    #     new_txn.amount = form.amount.data
    #     new_txn.payee_name = form.payee_name.data
    #     new_txn.user_id = user.id
    #     s.add(new_txn)
    #     s.commit()
    #     flash('congratulations, you created a new transaction')
        # return render_template('xxxx') #post/redirect/get pattern

    return render_template('unposted.html', items=items)


@app.route('/post_engine/<username>/<id>', methods=['GET', 'POST'])
@login_required
def post_engine(username, id):
    s = Session()
    user = s.query(User).filter_by(username=username).first()

    r = s.query(Transactions).filter(Transactions.user_id ==
                                     user.id, Transactions.id == id).first()

    form = PostEngineForm()
    if form.validate_on_submit():
        choice = form.type.data
        print(choice)
    #     new_txn.date = form.date.data
    #     new_txn.amount = form.amount.data
    #     new_txn.payee_name = form.payee_name.data
    #     new_txn.user_id = user.id
    #     s.add(new_txn)
    #     s.commit()
    #     flash('congratulations, you created a new transaction')
        # return render_template('xxxx') #post/redirect/get pattern

    return render_template('post_engine.html', items=r, form=form)


@app.route('/export_csv/<username>/<id>', methods=['GET', 'POST'])
@login_required
def export_csv(username, id):
    s = Session()

    user = s.query(User).filter_by(username=username).first()

    filtered_query = s.query(Transactions).filter(and_(
        Transactions.user_id == user.id, Transactions.acct_id == id, Transactions.type != 'notposted'))

    df = pd.read_sql_query(filtered_query.statement, engine)
    df.to_csv(f'mycsv user {username} account {id}.csv')

    print(df.head(5))

    return render_template('export.html')


@app.route('/reports/<username>/', methods=['GET', 'POST'])
@login_required
def reports(username):
    form = ReportSelectForm()
    if form.validate_on_submit():
        report_period = form.report_period.data
        report_template = form.report_template.data
        total = form.total_by_cat.data

        output_list_of_tuples = Reports.report_query(username=username, report_template=report_template, report_period=report_period, total=total) 

        flash('lily-livered sumbitch')

        return render_template('reports_summary.html', username=username, form=form, transactions=output_list_of_tuples, report_period=report_period)

    return render_template('reports_summary.html', username=username, form=form)

