from flask import Flask

app = Flask(__name__)

from app import routes


# import os




# from flask import Flask, render_template
# from .models import Accounts


# def create_app(test_config=None):
#     # create and configure the app
#     app = Flask(__name__, instance_relative_config=True)
#     app.config.from_mapping(
#         SECRET_KEY='dev',
#         DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
#     )

#     if test_config is None:
#         # load the instance config, if it exists, when not testing  
#         app.config.from_pyfile('config.py', silent=True)
#     else:
#         # load the test config if passed in
#         app.config.from_mapping(test_config)

#     # ensure the instance folder exists
#     try:
#         os.makedirs(app.instance_path)
#     except OSError:
#         pass

#     # a simple page that says hello
#     @app.route('/hello')
#     def hello():
#         return 'Hello, World!'
    
#     @app.route('/viewaccounts')
#     def viewaccounts():
#         account_row = Accounts.just_show_all_accounts_flask()
#         for k, v in account_row.items():
#             print(k, v)
#         return render_template('view_accounts.html', title='accounts', user=None, accounts=account_row.items())
        

#     return app