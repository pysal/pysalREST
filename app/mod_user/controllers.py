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
    return redirect(url_for('user'))

@mod_user.route('/', methods=['GET'])
def user_home():
    """
    User landing page.  A GET request here hands the browser
    a CSRF token.
    """
    print "getting"
    form = LoginForm(request.form)
    return render_template("user/signin.html", form=form)

@mod_user.route('/', methods=['POST'])
def login():
    """
    Sign a user in a start a session
    """
    form = LoginForm(request.form)
    if not form.validate_on_submit():
        flash('Error logging in')
    else:
        if request.form['submit'] == 'login':
            try:
                user = User.query.filter_by(email = form.email.data).first()
                if user == None:
                    flash('User not found, please register')
                    return render_template("user/signin.html", form=form)
            except:
                return render_template("user/signin.html", form=form)
            #These should be hashed, etc.  This is development only.

            if user.password == form.password.data:
                if 'remember' in request.form.keys():
                    if login_user(user, remember=request.form['remember']):
                        flash('Successfully logged in.')
                        return redirect(url_for('mod_api.get_api'))
                else:
                    if login_user(user):
                        flash('Successfully logged in.')
                        return redirect(url_for('mod_api.get_api'))

            else:
                return "Incorrect password"
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



#Checker to see if the user is already logged in
@mod_user.before_request
def before_request():
    g.user = current_user

