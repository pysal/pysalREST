from flask import Blueprint, request, render_template, \
                  flash, g, session, redirect, url_for, jsonify
from app import db, auth
import app

from flask_cors import cross_origin

from app.mod_user.models import User, ROLE_ADMIN, ROLE_USER

# Define the blueprint: 'auth', set its url prefix: app.url/auth
mod_user = Blueprint('auth', __name__, template_folder='templates/user')

@mod_user.route('/token/', methods=['GET'])
@auth.login_required
def get_auth_token():
    """
    Authentication can be via a username password combination
    curl -k -L -i -u  jay@jay.com:jay https://webpool.csf.asu.edu/pysalrest/user/token/
    
    or, more securely, via a token.  This is the function to get said token so that
     username:password are not constantly passed

    curl -k -L -i -u  big_long_token:unused https://webpool.csf.asu.edu/pysalrest/user/token/
    """
    token = g.user.generate_auth_token()
    uid = g.user.id
    return jsonify({'token':token.decode('ascii'), 'uid':uid})

@mod_user.route('/register/', methods=['POST'])
def register():
    """
    Register a new user with the backend
    
    Example:
    --------
    curl -k -L -XPOST -i -H "Content-Type:application/x-www-form-urlencoded" -d "email=jay@jay.com&password=jay" https:/webpool.csf.asu.edu/pysalrest/user/register/
    
    """
    print request.form
    print type(request.form)
    email = request.form.get('email')
    password = request.form.get('password')
    name = email.split('@')[0]
    user = User(name=name, email=email)
    user.hashpwd(password)
    db.session.add(user)
    db.session.commit()

    token = user.generate_auth_token()
    uid = user.id    

    return jsonify({'username':user.name, 'token':token.decode('ascii'), 'uid':uid})
