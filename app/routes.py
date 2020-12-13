from app import app
from app.models import Session, engine, User, Categories, Reports, Accounts, Transactions, Base, and_
from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from app.forms import LoginForm, RegistrationForm, AccountCreationForm, CategoryCreationForm, TransactionCreationForm, PostEngineForm
from werkzeug.urls import url_parse
import pandas as pd


@app.route('/')
@app.route('/index')
@login_required
def index():
    string = 'hello world this is numeral4.  I am born December 10, 2020.'
    return render_template('index.html', title='Sign In', string=string)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        s = Session()
        user = s.query(User).filter_by(username=form.username.data).first()
        print('this is user;;;;;',user)

        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))

        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

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

    accounts = s.query(Accounts).filter_by(Accounts.user_id==user.id).all()
    # accounts = [
    #     {'user': user, 'body': accou},
    #     {'user': user, 'body': 'Test post #2'}
    # ]
    return render_template('user.html', user=user, accounts=accounts)

@app.route('/accounts/<username>/')
@login_required
def accounts(username):
    s = Session()
    user = s.query(User).filter_by(username=username).first()

    r = s.query(Accounts).filter(Accounts.user_id==user.id).all()

    return render_template('view_accounts.html', items=r)

@app.route('/create_account/<username>/', methods=['GET', 'POST'])
@login_required
def create_account(username):
    s = Session()
    user = s.query(User).filter_by(username=username).first()

    r = s.query(Accounts).filter(Accounts.user_id==user.id).all()

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
        return redirect(url_for('create_account')) #post/redirect/get pattern
    return render_template('create_account.html', form=form)

@app.route('/account_register/<username>/<id>', methods=['GET', 'POST'])
def account_register(username, id):
    s = Session()
    
    user = s.query(User).filter_by(username=username).first()

    r = s.query(Transactions).filter(and_(Transactions.user_id==user.id, Transactions.acct_id==id, Transactions.type != 'notposted')).all()

    return render_template('account_register.html', items=r, id=id)

@app.route('/categories/<username>')
@login_required
def categories(username):
    s = Session()
    user = s.query(User).filter_by(username=username).first()

    r = s.query(Categories).filter(Categories.user_id==user.id).all()

    return render_template('view_categories.html', items=r)

@app.route('/create_category/<username>/', methods=['GET', 'POST'])
@login_required
def create_category(username):
    s = Session()
    user = s.query(User).filter_by(username=username).first()

    r = s.query(Categories).filter(Categories.user_id==user.id).all()

    form = CategoryCreationForm()
    if form.validate_on_submit():
        new_cat = Categories()
        new_cat.name = form.name.data
        new_cat.inorex = form.inorex.data
        new_cat.user_id = user.id
        s.add(new_cat)
        s.commit()
        flash('congratulations, you created a new category')
        return redirect(url_for('create_categories')) #post/redirect/get pattern

    return render_template('create_categories.html', form=form)

@app.route('/transactions/<username>')
@login_required
def transactions(username):
    s = Session()
    user = s.query(User).filter_by(username=username).first()

    r = s.query(Transactions).filter(Transactions.user_id==user.id).order_by(Transactions.date).all()

    return render_template('view_transactions.html', items=r)

@app.route('/create_transaction/<username>/', methods=['GET', 'POST'])
@login_required
def create_transaction(username):
    s = Session()
    user = s.query(User).filter_by(username=username).first()

    r = s.query(Transactions).filter(Transactions.user_id==user.id).all()

    form = TransactionCreationForm()
    if form.validate_on_submit():
        new_txn = Transactions()
        new_txn.date = form.date.data
        new_txn.amount = form.amount.data
        new_txn.payee_name = form.payee_name.data
        new_txn.user_id = user.id
        s.add(new_txn)
        s.commit()
        flash('congratulations, you created a new transaction')
        return redirect(url_for('create_transaction')) #post/redirect/get pattern

    return render_template('create_transaction.html', form=form)

@app.route('/unposted/<username>/', methods=['GET', 'POST'])
@login_required
def unposted(username):
    s = Session()
    user = s.query(User).filter_by(username=username).first()

    r = s.query(Transactions).filter(Transactions.user_id==user.id, Transactions.type == 'notposted').order_by(Transactions.date).all()

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

    return render_template('unposted.html', items=r)

@app.route('/post_engine/<username>/<id>', methods=['GET', 'POST'])
@login_required
def post_engine(username, id):
    s = Session()
    user = s.query(User).filter_by(username=username).first()

    r = s.query(Transactions).filter(Transactions.user_id==user.id, Transactions.id == id).first()

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

    filtered_query = s.query(Transactions).filter(and_(Transactions.user_id==user.id, Transactions.acct_id==id, Transactions.type != 'notposted'))


    df = pd.read_sql_query(filtered_query.statement, engine)
    df.to_csv(f'mycsv user {username} account {id}.csv')

    print(df.head(5))

    return render_template('export.html')




