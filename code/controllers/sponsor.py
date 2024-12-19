from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash
from models.models import db, User, Sponsor, Influencer, Campaign, AdRequest, Request
from functools import wraps
from flask import current_app as app
from flask_restful import Resource, Api, marshal_with, fields
import sqlalchemy
from sqlalchemy import func
from sqlalchemy import or_
import json

# Authentication decorator
def auth_required(func):
    @wraps(func)
    def check_auth(*args, **kwargs):
        if not session.get('loggedin') or session['usertype'] != 'sponsor':
            flash('You need to login first')
            return redirect(url_for('loginSponsor'))
        return func(*args, **kwargs)
    return check_auth

# Utility function to calculate campaign progress
def calculate_campaign_progress(start_date, end_date):
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    current = datetime.now()
    
    if current < start:
        return 0
    elif current > end:
        return 100
    else:
        total_days = (end - start).days
        elapsed_days = (current - start).days
        return int((elapsed_days / total_days) * 100)

# Route for sponsor's campaign progress
@app.route('/sponsor/stats/campaignprogress')
@auth_required
def sponsorCampaignsProgress():
    campaigns = Campaign.query.all()
    return [{"name": c.name, "progress": calculate_campaign_progress(c.start_date, c.end_date)} for c in campaigns]

# Sponsor dashboard route
@app.route('/dashboard/sponsor', methods=['GET', 'POST'])
@auth_required
def dashboardSponsor():
    sponsor_id = session['user_id']
    campaigns = Campaign.query.filter_by(sponsor_id=sponsor_id).all()
    return render_template('/sponsor/sponsormain.html', campaigns=campaigns)

# Sponsor profile route
@app.route('/sponsor/profile', methods=['GET', 'POST'])
@auth_required
def sponsorProfile():
    if request.method == 'POST':
        return handle_password_change()
    return render_template('sponsor/sponsorprofile.html', username=session['username'], user_id=session['user_id'])

# Helper function for password change
def handle_password_change():
    user = Sponsor.query.filter_by(sponsor_id=session['user_id']).first()
    if not user:
        flash("User does not exist.")
        return render_template('sponsor/sponsorprofile.html', username=session['username'], user_id=session['user_id'])
    
    if user.password != request.form['password']:
        flash("Password does not match.")
        return render_template('sponsor/sponsorprofile.html', username=session['username'], user_id=session['user_id'])
    
    if request.form['newpassword'] != request.form['confirmpassword']:
        flash("Password and Confirm Password does not match.")
        return render_template('sponsor/sponsorprofile.html', username=session['username'], user_id=session['user_id'])
    
    user.password = request.form['newpassword']
    db.session.commit()
    flash("Password changed successfully")
    return render_template('sponsor/sponsorprofile.html', username=session['username'])

# Route for managing campaigns
@app.route('/sponsor/campaigns', methods=['GET', 'POST'])
@auth_required
def manageCampaigns():
    sponsor_id = session['user_id']
    campaigns = Campaign.query.filter_by(sponsor_id=sponsor_id).all()
    return render_template('/sponsor/campaigns.html', campaigns=campaigns)

# Route for viewing specific campaign
@app.route('/sponsor/campaigns/view/<int:campaign_id>', methods=['GET', 'POST'])
@auth_required
def viewCampaigns(campaign_id):
    sponsor_id = session['user_id']
    campaigns = Campaign.query.filter_by(sponsor_id=sponsor_id, campaign_id=campaign_id).all()
    return render_template('/sponsor/campaigns.html', campaigns=campaigns)

# Route for creating new campaign
@app.route('/sponsor/campaigns/create', methods=['GET', 'POST'])
@auth_required
def createCampaigns():
    if request.method == 'POST':
        new_campaign = create_campaign_from_form()
        db.session.add(new_campaign)
        db.session.commit()
        return redirect(url_for('dashboardSponsor'))
    return render_template('/sponsor/campaigncreate.html')

# Helper function to create campaign from form data
def create_campaign_from_form():
    return Campaign(
        name=request.form['name'].upper(),
        description=request.form['description'].title(),
        start_date=request.form['start_date'],
        end_date=request.form['end_date'],
        budget=request.form['budget'],
        visibility=request.form['campaigntype'],
        goals=request.form['goals'].capitalize(),
        status="Unflagged",
        validity="Active",
        sponsor_id=session['user_id']
    )

# Route for modifying existing campaign
@app.route('/sponsor/campaigns/modify/<campaign_id>', methods=['GET', 'POST'])
def modifyCampaign(campaign_id):
    campaign = Campaign.query.filter_by(campaign_id=campaign_id).first()
    if request.method == 'POST':
        update_campaign_from_form(campaign)
        db.session.commit()
        return redirect(url_for('manageCampaigns'))
    return render_template('/sponsor/campaignmodify.html', campaigns=campaign)


@app.route('/delete_campaign/<int:campaign_id>', methods=['POST'])
@auth_required
def delete_campaign(campaign_id):
    print(campaign_id)
    campaign = Campaign.query.get_or_404(campaign_id)
    print(campaign)

    if campaign.sponsor_id != session['user_id']:
        flash('You do not have permission to delete this campaign.', 'error')
        return redirect(url_for('dashboardSponsor'))

    try:
        AdRequest.query.filter_by(campaign_id=campaign_id).delete()
        db.session.delete(campaign)
        db.session.commit()
        flash('Campaign and related ad requests deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'There was an error deleting the campaign: {str(e)}', 'error')

    return redirect(url_for('manageCampaigns'))



# Helper function to update campaign from form data
def update_campaign_from_form(campaign):
    campaign.name = request.form['name'].upper()
    campaign.description = request.form['description'].capitalize()
    campaign.start_date = request.form['start_date']
    campaign.end_date = request.form['end_date']
    campaign.budget = request.form['budget']
    campaign.visibility = request.form['campaigntype']
    campaign.goals = request.form['goals'].capitalize()
    campaign.status = "Unflagged"
    campaign.validity = "Active"

# Routes for ad requests
@app.route('/sponsor/adrequests/view/<int:campaign_id>', methods=['GET', 'POST'])
@auth_required
def viewAdrequests(campaign_id):
    campaigns = Campaign.query.filter_by(campaign_id=campaign_id).first()
    return render_template('/sponsor/adrequestsview.html', campaigns=campaigns)

@app.route('/sponsor/adrequests/create')
def newAdrequest():
    return redirect(url_for('manageCampaigns'))

@app.route('/sponsor/adrequests/create/<int:campaign_id>', methods=['GET', 'POST'])
def createAdrequest(campaign_id):
    if request.method == 'POST':
        new_adrequest = create_adrequest_from_form(campaign_id)
        db.session.add(new_adrequest)
        db.session.commit()
        return redirect(url_for('dashboardSponsor'))
    campaign = Campaign.query.filter_by(campaign_id=campaign_id).first()
    return render_template('/sponsor/adrequestscreate.html', campaign=campaign)

# Helper function to create ad request from form data
def create_adrequest_from_form(campaign_id):
    return AdRequest(
        message=request.form['message'].capitalize(),
        requirements=request.form['requirements'].capitalize(),
        payment_amount=request.form['payment_amount'],
        status="Pending",
        campaign_id=campaign_id,
        present_status="Unflagged"
    )

# Route for modifying ad request
@app.route('/sponsor/adrequests/modify/<int:adrequest_id>', methods=['GET', 'POST'])
def modifyAdrequest(adrequest_id):
    adrequest = AdRequest.query.filter_by(adrequest_id=adrequest_id).first()
    if request.method == 'POST':
        update_adrequest_from_form(adrequest)
        db.session.commit()
        return redirect(url_for('dashboardSponsor'))
    campaign = Campaign.query.filter_by(campaign_id=adrequest.campaign_id).first()
    return render_template('/sponsor/adrequestsmodify.html', campaign=campaign, adrequest=adrequest)

# Helper function to update ad request from form data
def update_adrequest_from_form(adrequest):
    adrequest.message = request.form['message'].capitalize()
    adrequest.requirements = request.form['requirements'].capitalize()
    adrequest.payment_amount = request.form['payment_amount']
    adrequest.influencer_id = request.form['influencer_id']

# Routes for handling requests
@app.route('/sponsor/requests/view/<int:adrequest_id>', methods=['GET', 'POST'])
@auth_required
def viewRequests(adrequest_id):
    adrequests = AdRequest.query.filter_by(adrequest_id=adrequest_id).first()
    return render_template('/sponsor/sponsorrequests.html', adrequests=adrequests)

@app.route('/sponsor/adrequests/send/<adrequest_id>', methods=['GET', 'POST'])
def sendRequest(adrequest_id):
    if request.method == 'POST':
        adrequest = AdRequest.query.filter_by(adrequest_id=adrequest_id).first()
        adrequest.influencer_id = request.form['influencer_id']
        db.session.commit()
        return redirect(url_for('dashboardSponsor'))
    influencers = Influencer.query.all()
    adrequest = AdRequest.query.filter_by(adrequest_id=adrequest_id).first()
    return render_template('/sponsor/adrequestssend.html', adrequest=adrequest, influencers=influencers)

@app.route('/sponsor/adrequests/accept/<id>')
def acceptRequest(id):
    request = Request.query.filter_by(id=id).first()
    if request:
        adrequest = AdRequest.query.filter_by(adrequest_id=request.adrequest_id).first()
        adrequest.influencer_id = request.influencer_id
        adrequest.status = "Accepted"
        db.session.commit()
        return redirect(url_for('dashboardSponsor'))
    flash("Action failed. Please try again.")
    return redirect(url_for('dashboardSponsor'))

@app.route('/sponsor/adrequests/reject/<adrequest_id>')
def rejectRequest(adrequest_id):
    adrequest = AdRequest.query.filter_by(adrequest_id=adrequest_id).first()
    if adrequest.influencer_id is not None:
        adrequest.status = "Rejected"
        db.session.commit()
        return redirect(url_for('dashboardSponsor'))
    flash("Action failed. Please try again.")
    return redirect(url_for('dashboardSponsor'))

# Search functionality
@app.route('/sponsor/search', methods=['GET', 'POST'])
def sponsorSearch():
    if request.method == 'POST':
        search_type = request.form['searchtype']
        subtype = request.form['subtype']
        search = request.form['search']
        results = perform_search(search_type, subtype, search)
        return render_template('/sponsor/sponsorsearch.html', **results)
    return render_template('/sponsor/sponsorsearch.html')

# Helper function to perform search
def perform_search(search_type, subtype, search):
    if search_type == "Influencer":
        influencers = findInfluencers(subtype, search)
        return {'influencers': influencers}
    elif search_type == "Campaign":
        campaigns = findCampaigns(subtype, search)
        return {'campaigns': campaigns}
    elif search_type == "AdRequest":
        adrequests = findAdrequests(subtype, search)
        return {'adrequests': adrequests}
    return {}

# Route for sponsor statistics
@app.route('/sponsor/stats')
def sponsorStats():
    username = session['user_id']
    campaigns = Campaign.query.all()
    adrequests = AdRequest.query.all()
    account = Campaign.query.filter_by(status='Unflagged').count()
    aadcount = AdRequest.query.filter_by(present_status='Unflagged').count()
    data = sponsorCampaignsProgress()
    return render_template('/sponsor/sponsorstats.html', username=username, campaigns=campaigns,
                           adrequests=adrequests, account=account, aadcount=aadcount, progressdata=data)

# Search functions
def findInfluencers(subtype, value):
    if subtype == "By Name":
        return Influencer.query.filter(Influencer.name.like(f'%{value}%')).all()
    elif subtype == "By Category":
        return Influencer.query.filter(Influencer.category.like(f'%{value}%')).all()
    elif subtype == "By Niche":
        return Influencer.query.filter(Influencer.niche.name.like(f'%{value}%')).all()
    return []

def findCampaigns(subtype, search):
    if subtype == "By Name":
        return Campaign.query.filter(Campaign.name.like(f'%{search}%')).all()
    elif subtype == "By Description":
        return Campaign.query.filter(Campaign.description.like(f'%{search}%')).all()
    elif subtype == "By Visibility":
        return Campaign.query.filter(Campaign.visibility.like(f'%{search}%')).all()
    elif subtype == "By Goals":
        return Campaign.query.filter(Campaign.goals.like(f'%{search}%')).all()
    elif subtype == "By Start Date":
        return Campaign.query.filter(Campaign.start_date == search).all()
    elif subtype == "By End Date":
        return Campaign.query.filter(Campaign.end_date == search).all()
    return []

def findAdrequests(subtype, search):
    if subtype == "By Message":
        return AdRequest.query.filter(AdRequest.message.like(f'%{search}%')).all()
    elif subtype == "By Requirements":
        return AdRequest.query.filter(AdRequest.requirements.like(f'%{search}%')).all()
    elif subtype == "By Status":
        return AdRequest.query.filter(AdRequest.status.like(f'%{search}%')).all()
    return []

# API endpoint for influencer search
influencer_data = {
    'influencer_id': fields.String,
    'name': fields.String,
    'category': fields.String,
    'niche': fields.String
}

@app.route('/sponsor/search/influencer')
@marshal_with(influencer_data)
def searchInfluencer():
    subtype = request.args.get('searchtype')
    value = request.args.get('search')
    return findInfluencers(subtype, value)