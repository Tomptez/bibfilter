from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_marshmallow import Marshmallow
from flask_basicauth import BasicAuth
from dotenv import load_dotenv
import os
import atexit
import logging
from logging.handlers import SMTPHandler

load_dotenv()

def get_env_variable(name):
    try:
        return os.environ[name]
    except KeyError:
        message = "Expected environment variable '{}' not set.".format(name)
        raise Exception(message)

#init app
app = Flask(__name__)

# the URI for the Databse depend on your setup and 
# should be setup as an environment variable DATABASE_URL (for example in your .env file)
#
# Examples
# DATABASE_URL = "postgresql://postgres:mypassword@localhost/bibfilter"
# DATABASE_URL = "sqlite:///new.db"
uri = get_env_variable("DATABASE_URL")

# If using heroku, POSTGRES_DATABASE_SCHEME=postgresql should be used, but just in case DATABASE_URL returns postgres:// insead of postgresql://
# https://help.heroku.com/ZKNTJQSK/why-is-sqlalchemy-1-4-x-not-connecting-to-heroku-postgres
if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)
    
app.config['SQLALCHEMY_DATABASE_URI'] = uri 

# Set Up Username and Password for Basic Auth as environment variables APP_USERNAME annd APP_PASSWORD
app.config['BASIC_AUTH_USERNAME'] = get_env_variable("APP_USERNAME")
app.config['BASIC_AUTH_PASSWORD'] = get_env_variable("APP_PASSWORD")

# silence the deprecation warning
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False 

## Optionally SQLALCHEMY logging
if os.environ.get("SQL_DEBUG") == "Yes":
    app.config['SQLALCHEMY_ECHO'] = True

# Don't sort json elements alphabetically 
app.config['JSON_SORT_KEYS'] = False


# Init Cors (needed to communicate properly on local server)
CORS(app)
# Init db
db = SQLAlchemy(app)
# Init Marshmallow
ma = Marshmallow(app)
# Init BasicAuth
basic_auth = BasicAuth(app)

# sending an email notification once it fails
if not app.debug:
    app.logger.setLevel(logging.WARNING)

    mail_handler = SMTPHandler(
        mailhost=("smtp.gmail.com", 587),
        fromaddr="socialpolicyprefs@gmail.com",
        toaddrs=["socialpolicyprefs@gmail.com"],  
        subject="Flask application error"
    )
    mail_handler.setLevel(logging.ERROR)
    app.logger.addHandler(mail_handler)

def cleanup():
    app.logger.warning("Bibfilter is shutting down.")

# Register the cleanup function
atexit.register(cleanup)

from bibfilter import routes