import os

import pymysql
from flask import g


def get_db():
    if 'db' not in g:
        g.db = pymysql.connect(
            host=os.environ.get('DB_HOST', 'gachon.arang.kr'),
            port=int(os.environ.get('DB_PORT', 3306)),
            user=os.environ.get('DB_USER', 'root'),
            password=os.environ.get('DB_PASS', 'rkcjs123!'),
            database=os.environ.get('DB_NAME', 'security_lab'),
            cursorclass=pymysql.cursors.DictCursor,
            charset='utf8mb4',
        )
    return g.db


def close_db(exception=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()
