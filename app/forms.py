from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, DateField, BooleanField, SubmitField, DecimalField, SelectField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from app.models import User, Session

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        s = Session()
        user = s.query(User).filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        s = Session()
        user = s.query(User).filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

class AccountCreationForm(FlaskForm):
    acct_name = StringField('account name', validators=[DataRequired()])
    startbal = DecimalField('starting balance', validators=[DataRequired()])
    type = StringField('asset or liability?', validators=[DataRequired()])
    status = StringField('open or closed?', validators=[DataRequired()])
    submit = SubmitField('create account')

class EditAccountForm(AccountCreationForm):
    submit = SubmitField('submit account changes')

class CategoryCreationForm(FlaskForm):
    name = StringField('category name', validators=[DataRequired()])
    inorex = StringField('income or expense account?', validators=[DataRequired()])
    submit = SubmitField('create category')

class EditCategoryForm(CategoryCreationForm):
    submit = SubmitField('submit category changes')

class TransactionCreationForm(FlaskForm):
    date = DateField('date', validators=[DataRequired()])
    type = SelectField('type? transaction by default', choices=[('transactions', 'transactions'), ('split', 'split'), ('transfer', 'transfer')])
    amount = DecimalField('amount (- for expense)', validators=[DataRequired()])
    payee_name = StringField('payee name')
    acct_id = SelectField('distribution account?', validators=[DataRequired()])
    cat_id = SelectField('category?', validators=[DataRequired()])
    submit = SubmitField('add transaction to register')
    # cat_id = Column(String)
    # cat_id2 = Column(String)
    # acct_id = Column(Integer, ForeignKey('accountlist.id'))
    # amount2 = Column(Numeric)
    # acct_id2 = Column(Integer, ForeignKey('accountlist.id'))
    # user_id = Column(Integer, ForeignKey('user.id'))

class EditTransactionForm(TransactionCreationForm):
    submit = SubmitField('submit changes to transaction')

class PostEngineForm(FlaskForm):
    type = SelectField('post as?', choices=[('regular', 'regular'), ('split', 'split transaction'), ('transfer', 'transfer')])
    submit = SubmitField('press to select')

class ReportSelectForm(FlaskForm):
    report_period = SelectField('report period', choices=[('year', 'year'), ('month', 'month')])
    submit = SubmitField('generate report')