from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager


app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('APP_CONFIG_FILE', silent=True)
app.config['SECRET_KEY'] = 'the-key-that-is-secret'

try:
    MAPBOX_ACCESS_KEY = app.config['MAPBOX_ACCESS_KEY']
except KeyError:
    MAPBOX_ACCESS_KEY = ""

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login = LoginManager(app)
login.login_view = 'login'

from routes import *

if __name__ == '__main__':
    app.run()
