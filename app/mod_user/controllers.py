from flask import Blueprint, request, render_template, \
                  flash, g, session, redirect, url_for
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import db, lm
import app

from app.mod_user.forms import LoginForm
from app.mod_user.models import User, ROLE_ADMIN, ROLE_USER

# Define the blueprint: 'auth', set its url prefix: app.url/auth
mod_user = Blueprint('auth', __name__)

@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

@lm.unauthorized_handler
def unauthorized():
    """
    @login_required calls this when a user is unauthorized
    """
    return redirect(url_for('signin'))

@mod_user.route('/', methods=['GET'])
@login_required
def user_home():
    """
    User landing page
    """
    return '''
    #If the user is signed in, give them some information
    #Else redirect to the signin page
    '''
    pass

@mod_user.route('/signin/', methods=['GET', 'POST'])
def signin():
    """
    Sign a user in a start a session
    """
    form = LoginForm(request.form)
    if form.validate_on_submit():
        if request.form['submit'] == 'login':
            try:
                user = User.query.filter_by(email = form.email.data).first()
            except:
                return render_template("user/signin.html", form=form)
            #These should be hashed, etc.  This is development only.
            if user.password == form.password.data:
                if login_user(user, remember=request.form['remember']):
                    flash('Successfully logged in.')
                    return redirect(url_for('mod_api.get_api'))
        elif request.form['submit'] == 'register':
            user = User.query.filter_by(email = form.email.data).first()
            if user != None:
                flash('A user with this email already exists')
            else:
                email = form.email.data
                try:
                    name = email.split('@')[0]
                except:
                    flash('Invalid email')
                    return render_templace("user/signin.html", form=form)
                password = form.password.data
                newuser = User(name=name, email=email, password=password)
                db.session.add(newuser)
                db.session.commit()
                render_template('user/signin.html', form=form)
    return render_template("user/signin.html", form=form)

#Checker to see if the user is already logged in
@mod_user.before_request
def before_request():
    g.user = current_user

