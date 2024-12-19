from warnings import catch_warnings
from flask import Flask, json, render_template, request, redirect, url_for, session, jsonify, flash
from flask import current_app as app
from datetime import datetime
from flask_sqlalchemy.session import Session
from models.models import db, User, Sponsor, Influencer, Campaign, AdRequest
from functools import wraps

# Authentication decorator for admin routes
def auth_required_admin(func):
    @wraps(func)
    def check_auth(*args, **kwargs):
        if 'loggedin' not in session or session['usertype'] != 'admin':
            flash('You need to login first as Admin')
            return redirect(url_for('loginAdmin'))
        return func(*args, **kwargs)
    return check_auth

# Admin dashboard routes
@app.route('/dashboard', methods=['GET', 'POST'])
@auth_required_admin
def dashboard():
    return render_template('/dashboards/dashboard.html')

@app.route('/dashboard/admin', methods=['GET', 'POST'])
@auth_required_admin
def dashboardAdmin():
    return render_template('/admin/admin.html')

# Admin info route with data aggregation
@app.route('/admin/info', methods=['GET', 'POST'])
def adminInfo():
    sponsors = Sponsor.query.all()
    influencers = Influencer.query.all()
    campaigns = Campaign.query.all()
    adrequests = AdRequest.query.all()

    scount = db.session.query(Sponsor).count()
    icount = db.session.query(Influencer).count()

    data = [scount, icount]
    labels = ["Sponsors", "Influencers"]

    return render_template('/admin/admininfo.html',
                           username=session['username'],
                           sponsors=sponsors,
                           influencers=influencers,
                           campaigns=campaigns,
                           adrequests=adrequests,
                           scount=scount,
                           icount=icount,
                           labels=labels,
                           data=data)

# Admin profile management
@app.route('/admin/profile', methods=['GET', 'POST'])
@auth_required_admin
def adminProfile():
    user_id = session['user_id']
    username = session['username']
    
    if request.method == 'POST':
        password = request.form['password']
        newpassword = request.form['newpassword']
        confirmpassword = request.form['confirmpassword']
        
        user = User.query.filter_by(user_id=user_id).first()
        
        if user and user.password == password:
            if newpassword == confirmpassword:
                user.password = newpassword
                db.session.commit()
                flash("Password changed successfully")
            else:
                flash("Password and Confirm Password do not match.")
        else:
            flash("Current password is incorrect.")
        
    return render_template('admin/adminprofile.html', username=username, user_id=user_id)

# Sponsor management routes
@app.route('/admin/sponsors', methods=['GET', 'POST'])
@auth_required_admin
def managesponsors():
    sponsors = Sponsor.query.all()
    return render_template('/admin/adminsponsors.html', sponsors=sponsors)

@app.route('/admin/sponsors/campaigns/<sponsor_id>', methods=['GET', 'POST'])
@auth_required_admin
def showCampaigns(sponsor_id):
    sponsors = Sponsor.query.all()
    campaigns = Campaign.query.filter_by(sponsor_id=sponsor_id).all()
    return render_template('/admin/sponsors.html', sponsors=sponsors, campaigns=campaigns)

@app.route('/admin/sponsors/flag/<sponsor_id>', methods=['GET', 'POST'])
@auth_required_admin
def flagSponsors(sponsor_id):
    sponsor = Sponsor.query.filter_by(sponsor_id=sponsor_id).first()
    sponsor.status = "Flagged" if sponsor.status == "Unflagged" else "Unflagged"
    db.session.commit()
    return redirect(url_for('adminInfo'))

# Influencer management routes
@app.route('/admin/influencers', methods=['GET', 'POST'])
@auth_required_admin
def manageinfluencers():
    influencers = Influencer.query.all()
    return render_template('/admin/admininfluencers.html', influencers=influencers)

@app.route('/admin/influencers/flag/<influencer_id>', methods=['GET', 'POST'])
@auth_required_admin
def flagIinfluencers(influencer_id):
    influencer = Influencer.query.filter_by(influencer_id=influencer_id).first()
    influencer.status = "Flagged" if influencer.status == "Unflagged" else "Unflagged"
    db.session.commit()
    return redirect(url_for('adminInfo'))

# Campaign and AdRequest management routes
@app.route('/admin/campaigns/flag/<campaign_id>', methods=['GET', 'POST'])
@auth_required_admin
def flagCampaign(campaign_id):
    campaign = Campaign.query.filter_by(campaign_id=campaign_id).first()
    campaign.status = "Flagged" if campaign.status == "Unflagged" else "Unflagged"
    db.session.commit()
    return redirect(url_for('adminInfo'))

@app.route('/admin/adrequests/flag/<id>', methods=['GET', 'POST'])
@auth_required_admin
def flagAdrequests(id):
    adrequest = AdRequest.query.filter_by(adrequest_id=id).first()
    adrequest.present_status = "Flagged" if adrequest.present_status == "Unflagged" else "Unflagged"
    db.session.commit()
    return redirect(url_for('adminInfo'))

# Search functionality
@app.route('/admin/search')
@auth_required_admin
def adminSearch():
    return render_template('/admin/adminsearch.html')

@app.route('/admin/sponsors/search', methods=['GET', 'POST'])
@auth_required_admin
def adminSponsorSearch():
    return render_template('/admin/adminsposnors.html')

@app.route('/admin/influencers/search', methods=['GET', 'POST'])
@auth_required_admin
def adminInfluencerSearch():
    return render_template('/admin/admininfluencers.html')

@app.route('/admin/search/all', methods=['GET', 'POST'])
@auth_required_admin
def adminSearchAll():
    if request.method == 'POST':
        searchtype = request.form['searchtype']
        subtype = request.form['subtype']
        search = request.form['search']

        search_functions = {
            "Sponsor": searchSponsors,
            "Influencer": searchInfluencers,
            "Campaign": searchCampaigns,
            "AdRequest": searchAdrequests
        }

        results = search_functions.get(searchtype, lambda x, y: None)(subtype, search)

        if results:
            return render_template('admin/adminsearch.html', **{searchtype.lower() + 's': results})
        else:
            flash("No Data Found")
            return render_template('/admin/adminsearch.html')

    return "Some error occurred"

# Search helper functions
def searchSponsors(subtype, search):
    if subtype == "By Name":
        return Sponsor.query.filter(Sponsor.name.like(f'%{search}%')).all()
    elif subtype == "By Industry":
        return Sponsor.query.filter(Sponsor.industry.like(f'%{search}%')).all()

def searchInfluencers(subtype, search):
    if subtype == "By Name":
        return Influencer.query.filter(Influencer.name.like(f'%{search}%')).all()
    elif subtype == "By Category":
        return Influencer.query.filter(Influencer.category.like(f'%{search}%')).all()
    elif subtype == "By Niche":
        return Influencer.query.filter(Influencer.niche.name.like(f'%{search}%')).all()

def searchCampaigns(subtype, search):
    filters = {
        "By Name": Campaign.name,
        "By Description": Campaign.description,
        "By Visibility": Campaign.visibility,
        "By Goals": Campaign.goals,
        "By Start Date": Campaign.start_date,
        "By End Date": Campaign.end_date
    }
    return Campaign.query.filter(filters[subtype].like(f'%{search}%')).all()

def searchAdrequests(subtype, search):
    filters = {
        "By Message": AdRequest.message,
        "By Requirements": AdRequest.requirements,
        "By Status": AdRequest.status
    }
    return AdRequest.query.filter(filters[subtype].like(f'%{search}%')).all()

# Admin statistics routes
@app.route('/admin/stats')
@auth_required_admin
def adminStats():
    activeSponsors = db.session.query(Sponsor).count()
    activeInfluencers = db.session.query(Influencer).count()
    activeCampaigns = db.session.query(Campaign).count()
    activeAdrequests = db.session.query(AdRequest).count()

    data = campaignsProgress()

    return render_template('/admin/adminstats.html',
                           username=session['username'],
                           activeSponsors=activeSponsors,
                           activeInfluencers=activeInfluencers,
                           activeCampaigns=activeCampaigns,
                           activeAdrequests=activeAdrequests,
                           progressdata=data)

@app.route('/userschartdata', methods=['GET', 'POST'])
@auth_required_admin
def userschartdata():
    scount = db.session.query(Sponsor).count()
    icount = db.session.query(Influencer).count()
    return [
        {'users': 'Sponsors', 'values': scount},
        {'users': 'Influencers', 'values': icount}
    ]

@app.route('/campaignschartdata', methods=['GET', 'POST'])
@auth_required_admin
def campaignschartdata():
    return userschartdata()

@app.route('/admin/stats/campaignprogress')
@auth_required_admin
def campaignsProgress():
    campaigns = Campaign.query.all()
    return [{"name": campaign.name, "progress": getProgress(campaign.start_date, campaign.end_date)} for campaign in campaigns]

def getProgress(startdate, enddate):
    start = datetime.strptime(startdate, '%Y-%m-%d')
    end = datetime.strptime(enddate, '%Y-%m-%d')
    current = datetime.now()

    if current < start:
        return 0
    elif current > end:
        return 100
    else:
        duration = (end - start).days
        elapsed = (current - start).days
        return int((elapsed / duration) * 100)