from flask import Blueprint, request, render_template, \
                  flash, g, session, redirect, url_for
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import db, lm, oid
import app

from app.mod_user.forms import LoginForm
from app.mod_user.models import User, ROLE_ADMIN, ROLE_USER

# Define the blueprint: 'auth', set its url prefix: app.url/auth
mod_user = Blueprint('auth', __name__)

@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

@mod_user.route('/', methods=['GET'])
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
@oid.loginhandler
def signin():
    """
    Sign a user in a start a session
    """

    #If the user is already logged in
    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('mod_api.get_api'))

    form = LoginForm()
    if form.validate_on_submit():
        session['remember_me'] = form.remember_me.data
        return oid.try_login(form.openid.data, ask_for = ["name", "email"])

    return render_template("user/signin.html", form=form)

@oid.after_login
def after_login(resp):
    if resp.email is None or resp.email == "":
        flash('Invalid login. Please try again.')
        return redirect(url_for('mod_user.signin'))
    user = User.query.filter_by(email = resp.email).first()
    if user is None:
        nickname = resp.nickname
        if nickname is None or nickname == "":
            nickname = resp.email.split('@')[0]
        user = User(nickname = nickname, email = resp.email, role = ROLE_USER)
        db.session.add(user)
        db.session.commit()
    remember_me = False
    if 'remember_me' in session:
        remember_me = session['remember_me']
        session.pop('remember_me', None)
    login_user(user, remember = remember_me)
    return redirect(request.args.get('next') or url_for('mod_api.get_api'))

#This fires before any view
@mod_user.before_request
def before_request():
    g.user = current_user
