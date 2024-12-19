from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

from application.config import LocalDevelopmentConfig
from models.models import db, User, Sponsor, Influencer, Campaign, AdRequest

app = None

def isExpired(strdate):
    """Check if a given date string is expired."""
    strdate = strdate.split("-")
    newdate = datetime(int(strdate[0]), int(strdate[1]), int(strdate[2]))
    return datetime.now() > newdate

def createApp():
    """Create and configure the Flask application."""
    app = Flask(__name__, template_folder='templates')
    app.config.from_object(LocalDevelopmentConfig)
    app.app_context().push()
    
    from models.models import db
    db.init_app(app)
    
    createData()
    
    return app

def createData():
    """Create initial data for the application."""
    db.create_all()

    # Check if the admin user exists, if not, create it
    admin = User.query.filter_by(user_id='admin').first()
    if not admin:
        admin = User(
            user_id='admin',
            name='admin',
            password='admin',
            usertype='admin',
            status='ACTIVE'
        )
        db.session.add(admin)
        db.session.commit()

    # Update campaign validity based on end date
    campaigns = Campaign.query.all()
    if campaigns:
        for campaign in campaigns:
            if isExpired(campaign.end_date):
                campaign.validity = "Expired"
            else:
                campaign.validity = "Active"
            db.session.commit()

    # Check if sponsors exist, if not, create them
    sponsor = Sponsor.query.all()
    if not sponsor:
        sponsor1 = Sponsor(
            sponsor_id="sponsor1",
            name="sponsor1",
            password="123",
            industry="Clothing",
            budget=500000,
            status="Unflagged"
        )
        sponsor2 = Sponsor(
            sponsor_id="sponsor2",
            name="sponsor2",
            password="123",
            industry="Food",
            budget=600000,
            status="Unflagged"
        )
        db.session.add(sponsor1)
        db.session.add(sponsor2)
        db.session.commit()

    # Check if influencers exist, if not, create them
    influencers = Influencer.query.all()
    if not influencers:
        influencer1 = Influencer(
            influencer_id="influencer1",
            name="influencer1",
            password="123",
            category="Beauty",
            niche="Cosmetics",
            reach=50000,
            status="Unflagged"
        )
        influencer2 = Influencer(
            influencer_id="influencer2",
            name="influencer2",
            password="123",
            category="Beauty",
            niche="Cosmetics",
            reach=50000,
            status="Unflagged"
        )
        db.session.add(influencer1)
        db.session.commit()
        db.session.add(influencer2)
        db.session.commit()

    return None

app = createApp()

# Import and register blueprints for different parts of the application
from controllers.home import *
from controllers.user import *
from controllers.admin import *
from controllers.sponsor import *
from controllers.influencer import *

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)






    
