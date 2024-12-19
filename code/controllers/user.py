from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask import current_app as app
from models.models import db, User, Sponsor, Influencer, Campaign, AdRequest
from functools import wraps

# Authentication decorator
def auth_required(func):
    @wraps(func)
    def check_auth(*args, **kwargs):
        if not session.get('loggedin'):
            flash('You need to login first')
            return redirect(url_for('loginAdmin'))
        return func(*args, **kwargs)
    return check_auth

# Helper function to set session variables after successful login
def logInUser(user, usertype):
    if usertype == 'admin':
        session.update({
            "loggedin": True,
            "usertype": usertype,
            "user_id": getattr(user, f"user_id"),
            "username": user.name
    })
    else:
        session.update({
            "loggedin": True,
            "usertype": usertype,
            "user_id": getattr(user, f"{usertype}_id"),
            "username": user.name
    })  

# Logout route
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('loginAdmin'))

# Admin login route
@app.route('/login/admin', methods=['GET', 'POST'])
def loginAdmin():
    if request.method == 'POST':
        return handle_login(User, 'user_id', 'admin', 'dashboardAdmin')
    return render_template('loginadmin.html')

# Sponsor login route
@app.route('/login/sponsor', methods=['GET', 'POST'])
def loginSponsor():
    if request.method == 'POST':
        return handle_login(Sponsor, 'sponsor_id', 'sponsor', 'dashboardSponsor')
    return render_template('loginsponsor.html')

# Influencer login route
@app.route('/login/influencer', methods=['GET', 'POST'])
def loginInfluencer():
    if request.method == 'POST':
        return handle_login(Influencer, 'influencer_id', 'influencer', 'dashboardInfluencer')
    return render_template('logininfluencer.html')

# Helper function to handle login process
def handle_login(model, id_field, usertype, dashboard):
    user_id = request.form[id_field]
    password = request.form['password']
    
    if not user_id or not password:
        flash(f"{usertype.capitalize()} Id and Password cannot be blank.")
        return render_template(f'login{usertype}.html')
    
    user = model.query.filter_by(**{id_field: user_id}).first()
    
    if user and user.password == password:
        logInUser(user, usertype)
        return redirect(url_for(dashboard))
    elif user:
        flash("Invalid Password")
    else:
        flash("User id not Registered")
        return render_template(f'register{usertype}.html')
    
    return render_template(f'login{usertype}.html')

# Route to get all users
@app.route('/users')
def getusers():
    users = User.query.all()
    return render_template('users.html', users=users)

# Sponsor registration route
@app.route('/register/sponsor', methods=['GET', 'POST'])
def registerSponsor():
    if request.method == 'POST':
        return handle_registration(Sponsor, 'sponsor_id', 'dashboardSponsor')
    return render_template('registersponsor.html')

# Influencer registration route
@app.route('/register/influencer', methods=['GET', 'POST'])
def registerInfluencer():
    if request.method == 'POST':
        return handle_registration(Influencer, 'influencer_id', 'dashboardInfluencer')
    return render_template('registerinfluencer.html')

# Helper function to handle registration process
def handle_registration(model, id_field, dashboard):
    form_data = request.form.to_dict()
    
    if any(value == "" for value in form_data.values()):
        flash("All columns are required to be filled.")
        return render_template(f'register{model.__name__.lower()}.html')
    
    if model.query.filter_by(**{id_field: form_data[id_field]}).first():
        flash(f"{model.__name__} id already registered. Please use a different Id")
        return render_template(f'register{model.__name__.lower()}.html')
    
    new_user = model(**form_data, status='Unflagged')
    new_user.name = new_user.name.upper()
    if hasattr(new_user, 'industry'):
        new_user.industry = new_user.industry.upper()
    if hasattr(new_user, 'category'):
        new_user.category = new_user.category.upper()
    if hasattr(new_user, 'niche'):
        new_user.niche = new_user.niche.upper()
    
    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for(dashboard))