from flask import Flask, render_template, redirect, url_for, request
from flask import current_app as app
from models.models import db, User, Sponsor, Influencer, Campaign, AdRequest

# Home route - displays all users, sponsors, and influencers
@app.route('/')
def home():
    all_users = User.query.all()
    all_sponsors = Sponsor.query.all()
    all_influencers = Influencer.query.all()
    
    return render_template('home.html',
                           users=all_users,
                           sponsors=all_sponsors,
                           influencers=all_influencers)

# Registered users route - displays all registered entities
@app.route('/regsiterredusers')
def registeredusers():
    registered_data = {
        'users': User.query.all(),
        'sponsors': Sponsor.query.all(),
        'influencers': Influencer.query.all()
    }
    
    return render_template('home.html', **registered_data)

# Login route placeholder (currently not implemented)
# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     pass