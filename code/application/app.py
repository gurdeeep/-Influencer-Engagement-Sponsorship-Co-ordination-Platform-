from flask import Flask,render_template,redirect,url_for,request
from flask_sqlalchemy import SQLAlchemy

from flask_login import LoginManager,UserMixin, login_manager,login_user,login_required,logout_user,current_user

from flask_migrate  import Migrate


from application.config import LocalDevelopmentConfig
from application.database import db
from models.models import *


app=None
migrate=Migrate()

def createApp():
  app=Flask(__name__,template_folder='templates')
  app.config.from_object(LocalDevelopmentConfig)
  app.app_context().push()
  # db=SQLAlchemy()
  db.init_app(app)
  migrate.init_app(app,db)
  return app


app=createApp()

from controllers.home import *
from controllers.user import *


if __name__=='__main__':
  app.run(host='0.0.0.0', port=8080)