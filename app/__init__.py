from flask import Flask
# from jinja2 import Environment
# from hamlish_jinja import HamlishExtension, HamlishTagExtension
# from flask_sqlalchemy import SQLAlchemy
# # from flask.ext.heroku import Heroku
# from flask_login import LoginManager
# from flask_bcrypt import Bcrypt
from celery import Celery


app = Flask(__name__)
app.config.from_object('config')
app.secret_key = 'abc'

app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

# heroku = Heroku(app)
# bcrypt = Bcrypt(app)
# db = SQLAlchemy(app)

# env = Environment(extensions=[HamlishExtension])
# env.hamlish_file_extensions=('.haml', '.html.haml')
# env.hamlish_enable_div_shortcut=True
# app.jinja_env.add_extension(HamlishTagExtension)
# app.jinja_env.add_extension(HamlishExtension)
#
# login_manager = LoginManager()
# login_manager.init_app(app)
# login_manager.login_view = "login"

from app import views



