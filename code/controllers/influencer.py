from flask import Flask, render_template, request, redirect, url_for, session, flash, json
from flask import current_app as app
from models.models import db, User, Sponsor, Influencer, Campaign, AdRequest, Request
from datetime import datetime
from functools import wraps

# Authentication decorator to ensure user is logged in as an influencer
def auth_required(func):
    @wraps(func)
    def check_auth(*args, **kwargs):
        if not session.get('loggedin') or session['usertype'] != 'influencer':
            flash('You need to login first')
            return redirect(url_for('loginInfluencer'))
        return func(*args, **kwargs)
    return check_auth

# Helper function to calculate campaign progress
def calculate_progress(start_date, end_date):
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    current = datetime.now()

    if current < start:
        return 0
    elif current > end:
        return 100
    else:
        total_duration = (end - start).days
        elapsed_duration = (current - start).days
        return int((elapsed_duration / total_duration) * 100)

# Route to get campaign progress for influencers
@app.route('/influencer/campaignprogress')
@auth_required
def influencerCampaignsProgress():
    campaigns = Campaign.query.filter_by(visibility="Public", status="Unflagged").all()
    return [
        {
            "campaign_id": campaign.campaign_id,
            "name": campaign.name,
            "progress": calculate_progress(campaign.start_date, campaign.end_date)
        }
        for campaign in campaigns
    ]

# Influencer dashboard route
@app.route('/dashboard/influencer', methods=['GET', 'POST'])
@auth_required
def dashboardInfluencer():
    influencer_id = session['user_id']
    progress_data = influencerCampaignsProgress()
    private_ad_requests = AdRequest.query.join(Campaign).filter(
        AdRequest.influencer_id == influencer_id,
        Campaign.visibility == 'Private'
    ).all()
    requests = Request.query.filter_by(influencer_id=influencer_id).all()
    return render_template('influencer/influencermain.html',
                           progressdata=progress_data,
                           adrequests=private_ad_requests,
                           requests=requests)

# Route for influencer main page
@app.route('/influencer/main', methods=['GET', 'POST'])
def influencerMain():
    public_campaigns = Campaign.query.filter_by(visibility='Public').all()
    return render_template('influencer/influencermain.html', campaigns=public_campaigns)

# Route for influencer profile and password change
@app.route('/influencer/profile', methods=['GET', 'POST'])
@auth_required
def influencerProfile():
    user_id = session['user_id']
    username = session['username']

    if request.method == 'POST':
        password = request.form['password']
        new_password = request.form['newpassword']
        confirm_password = request.form['confirmpassword']
        
        user = Influencer.query.get(user_id)
        if not user:
            flash("User does not exist.")
        elif user.password != password:
            flash("Current password is incorrect.")
        elif new_password != confirm_password:
            flash("New password and confirmation do not match.")
        else:
            user.password = new_password
            db.session.commit()
            flash("Password changed successfully")

    return render_template('influencer/influencerprofile.html', username=username, user_id=user_id)

# Helper function for campaign search
def search_campaigns(subtype, query):
    filters = {
        "By Name": Campaign.name.like(f'%{query}%'),
        "By Description": Campaign.description.like(f'%{query}%'),
        "By Visibility": Campaign.visibility.like(f'%{query}%'),
        "By Goals": Campaign.goals.like(f'%{query}%'),
        "By Start Date": Campaign.start_date == query,
        "By End Date": Campaign.end_date == query
    }
    return Campaign.query.filter(filters.get(subtype)).all()

# Helper function for ad request search
def search_ad_requests(subtype, query):
    filters = {
        "By Message": AdRequest.message.like(f'%{query}%'),
        "By Requirements": AdRequest.requirements.like(f'%{query}%'),
        "By Status": AdRequest.status.like(f'%{query}%')
    }
    return AdRequest.query.filter(filters.get(subtype)).all()

# Route for influencer search functionality
@app.route('/influencer/search', methods=['GET', 'POST'])
def influencerSearch():
    if request.method == 'POST':
        search_type = request.form['searchtype']
        subtype = request.form['subtype']
        query = request.form['search']

        if search_type == "Campaign":
            results = search_campaigns(subtype, query)
            return render_template('/influencer/influencersearch.html', campaigns=results)
        elif search_type == "AdRequest":
            results = search_ad_requests(subtype, query)
            return render_template('/influencer/influencersearch.html', adrequests=results)

        if not results:
            flash("No Data Found")

    return render_template('/influencer/influencersearch.html', username=session['user_id'])

# Route for influencer statistics
@app.route('/influencer/stats', methods=['GET', 'POST'])
def influencerStats():
    progress_data = influencerCampaignsProgress()
    return render_template('/influencer/influencerstats.html',
                           username=session['user_id'],
                           progressdata=progress_data)

# Route for viewing a specific campaign
@app.route('/influencer/view/campaign/<int:campaign_id>', methods=['GET', 'POST'])
def influencerViewCampaigns(campaign_id):
    campaign = Campaign.query.filter_by(campaign_id=campaign_id, visibility="Public").first()
    requests = Request.query.filter_by(influencer_id=session['user_id']).all()
    return render_template('/influencer/influencerview.html', campaign=campaign, requests=requests)

# Route for responding to an ad request
@app.route('/influencer/adrequest/response/<adrequest_id>', methods=['GET', 'POST'])
def influencerResponse(adrequest_id):
    if request.method == 'POST':
        response = request.form['response']
        influencer_id = session['user_id']

        request_data = Request.query.filter_by(adrequest_id=adrequest_id, influencer_id=influencer_id).first()
        if request_data:
            request_data.response = response
        else:
            new_request = Request(adrequest_id=adrequest_id, influencer_id=influencer_id, response=response)
            db.session.add(new_request)

        db.session.commit()
        flash("Response Updated.")
        return redirect(url_for('dashboardInfluencer'))

# Route for accepting an ad request
@app.route('/influencer/adrequests/accept/<int:adrequest_id>', methods=['GET', 'POST'])
def influencerAccept(adrequest_id):
    adrequest = AdRequest.query.get(adrequest_id)
    if adrequest and adrequest.status == "Pending" and not adrequest.response and adrequest.influencer_id:
        adrequest.status = "Acepted"
        db.session.commit()
    else:
        flash("Now only Sponsor can Accept/Reject")
    return redirect(url_for('dashboardInfluencer'))

# Route for rejecting an ad request
@app.route('/influencer/adrequests/reject/<int:adrequest_id>', methods=['GET', 'POST'])
def influencerReject(adrequest_id):
    adrequest = AdRequest.query.get(adrequest_id)
    if adrequest and adrequest.status == "Pending" and not adrequest.response and adrequest.influencer_id:
        adrequest.status = "Rejected"
        db.session.commit()
    else:
        flash("Now only Sponsor can Accept/Reject")
    return redirect(url_for('dashboardInfluencer'))