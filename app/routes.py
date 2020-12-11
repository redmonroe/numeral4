from app import app
from app.models import Categories
from flask import render_template


# from flask import Flask, render_template, flash, redirect, url_for
# from flask_sqlalchemy import SQLAlchemy
# from flask_migrate import Migrate
# from numeral4.config import Config
# from forms import LoginForm


# app.config.from_object(Config) #this is really useful to know
# db = SQLAlchemy(app)
# migrate = Migrate(app, db)

@app.route('/')
@app.route('/index')
def index():
    return 'hello world this is numeral4.  I am born.'


@app.route('/categories')
def categories():
    r = Categories.just_show_all_categories_flask()
    items = []
    for item in r: 
        items.append(item)
    return render_template('category_reports.html', items=items)


# @app.route('/')
# @app.route('/index')
# def index():
#     user = {'username': 'Joseph'}
#     posts = [
#         {
#             'author': {'username': 'John'},
#             'body': 'Beautiful day in Portland!'
#         },
#         {
#             'author': {'username': 'Susan'},
#             'body': 'The Avengers movie was so cool!'
#         }
#     ]
#     return render_template('index.html', title='Home', user=user, posts=posts)


# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     form = LoginForm()
#     if form.validate_on_submit():
#         flash('Login requested for user {}, remember_me={}'.format(
#             form.username.data, form.remember_me.data))
#         return redirect(url_for('index'))
#     return render_template('login.html', title='Sign In', form=form)