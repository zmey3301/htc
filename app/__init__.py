#!/usr/bin/env python3
from flask import Flask
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from json import loads
application = Flask(__name__)
application.config.from_object("flask-config")
Bootstrap(application)
db = SQLAlchemy(application)
with open("app.json", "r") as config_file:
    config = loads(config_file.read())
from app import views
