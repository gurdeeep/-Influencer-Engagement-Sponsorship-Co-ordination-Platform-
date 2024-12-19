import os

basedir = os.path.abspath(os.path.dirname(__file__))


class config:
  SQLITE_DB_DIR = None
  SQLALCHEMY_DATABASE_URI = None
  SQLALCHEMY_TRACK_MODIFICATIONS = False
  DEBUG = False
  SECRET_KEY=None


class LocalDevelopmentConfig(config):
  DEBUG = True
  SECRET_KEY="myflasksecret"
  SQL_DB_DIR = os.path.join(basedir, '../database')
  SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(
      SQL_DB_DIR, 'iescpDB.sqlite3')
