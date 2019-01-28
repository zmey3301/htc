#!/usr/bin/env python3
from sys import argv
from app import db
if len(argv) > 1 and argv[1].lower() == "clear":
    db.drop_all()
db.create_all()
