from datetime import datetime, timezone

from flask import current_app as app

# from application.database import db
from werkzeug.security import generate_password_hash, check_password_hash

from sqlalchemy.ext.declarative import declarative_base
from flask_sqlalchemy import SQLAlchemy

engine = None
Base = declarative_base()
db = SQLAlchemy()


class User(db.Model):
  __tablename__ = 'users'  # For Admin
  id = db.Column(db.Integer, autoincrement=True, primary_key=True)
  user_id = db.Column(db.String(200), unique=True)
  name = db.Column(db.String(50), nullable=False)
  password = db.Column(db.String(500))
  usertype = db.Column(db.String(50))
  status = db.Column(db.String(50))
  timestamp = db.Column(db.DateTime, default=datetime.now(timezone.utc))

  def hashPassword(self, password):
    return generate_password_hash(password)

  def checkPassword(self, password):
    return check_password_hash(self.password, password)


class Sponsor(db.Model):
  __tablename__ = 'sponsors'
  id = db.Column(db.Integer, autoincrement=True, primary_key=True)
  sponsor_id = db.Column(db.String(200), unique=True)
  password = db.Column(db.String(200))
  name = db.Column(db.String(200), nullable=False)
  industry = db.Column(db.String(200), nullable=False)
  budget = db.Column(db.Double, nullable=False)
  status = db.Column(db.String(200), nullable=False)
  timestamp = db.Column(db.DateTime, default=datetime.now(timezone.utc))
  #for One-To_many relationship with campaigns
  campaigns = db.relationship('Campaign', backref='sponsors', lazy=True)


class Influencer(db.Model):
  __tablename__ = 'influencers'
  id = db.Column(db.Integer, autoincrement=True, primary_key=True)
  influencer_id = db.Column(db.String(200), unique=True)
  password = db.Column(db.String(200))
  name = db.Column(db.String(200), nullable=False)
  category = db.Column(db.String(200), nullable=False)
  niche = db.Column(db.String(200), nullable=False)
  reach = db.Column(db.String(200), nullable=False)
  status = db.Column(db.String(200), nullable=False)
  timestamp = db.Column(db.DateTime, default=datetime.now(timezone.utc))
  requests = db.relationship('Request', backref='influencers', lazy=True)


class Campaign(db.Model):
  __tablename__ = 'campaigns'
  campaign_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
  name = db.Column(db.String(200), nullable=False, unique=True)
  description = db.Column(db.String(500), nullable=False)
  start_date = db.Column(db.String(100), nullable=False)
  end_date = db.Column(db.String(100), nullable=False)
  budget = db.Column(db.Double, nullable=False)
  visibility = db.Column(db.String(100), nullable=False)
  goals = db.Column(db.String(500), nullable=False)
  timestamp = db.Column(db.DateTime, default=datetime.now(timezone.utc))
  status = db.Column(db.String(200), nullable=False) # Flagged or Unflagged
  validity = db.Column(db.String(200), nullable=False) #Active or Expired
  sponsor_id = db.Column(db.String(200), db.ForeignKey('sponsors.sponsor_id'))
  adrequests = db.relationship('AdRequest', backref='campaigns', lazy=True)
  add_campaign = db.relationship('AdRequest', cascade='all, delete-orphan', lazy=True)


class AdRequest(db.Model):
  __tablename__ = 'adrequests'
  adrequest_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
  campaign_id = db.Column(db.Integer,
                          db.ForeignKey('campaigns.campaign_id'),
                          nullable=False)
  influencer_id = db.Column(db.Integer,
                            db.ForeignKey('influencers.influencer_id'))

  message = db.Column(db.String(500), nullable=False)
  requirements = db.Column(db.String(500), nullable=False)
  payment_amount = db.Column(db.Double, nullable=False)
  status = db.Column(db.String(100), nullable=False)  #Pending/Acepted/Rejected
  present_status = db.Column(db.String(100),
                             nullable=False)  # Flagged or Unflagged
  # Influencer response
  requests = db.relationship('Request', backref='adrequests', lazy=True)
  timestamp = db.Column(db.DateTime, default=datetime.now(timezone.utc))


class Request(db.Model):
  __tablename__ = 'requests'
  id = db.Column(db.Integer, autoincrement=True, primary_key=True)
  adrequest_id = db.Column(db.Integer,
                           db.ForeignKey('adrequests.adrequest_id'))

  influencer_id = db.Column(db.Integer,
                            db.ForeignKey('influencers.influencer_id'))
  response = db.Column(db.String(500))  # Influencer response
  timestamp = db.Column(db.DateTime, default=datetime.now(timezone.utc))
