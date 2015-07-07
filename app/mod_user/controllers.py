from flask import Blueprint, request, render_template, \
                  flash, g, session, redirect, url_for, jsonify, \
		  current_app
from flask.ext.login import login_user, logout_user,\
			    current_user, login_required,\
			    encode_cookie
import app
from app import db, lm
from config import baseurl
from app.mod_user.models import User
from rauth import OAuth1Service, OAuth2Service

# Define the blueprint: 'auth', set its url prefix: app.url/auth
mod_user = Blueprint('user', __name__)

class OAuthSignIn(object):
    providers = None

    def __init__(self, provider_name):
        self.provider_name = provider_name
        credentials = current_app.config['OAUTH_CREDENTIALS'][provider_name]
        self.consumer_id = credentials['id']
        self.consumer_secret = credentials['secret']

    def authorize(self):
        pass

    def callback(self):
        pass

    def get_callback_url(self):
        return url_for('user.oauth_callback', provider=self.provider_name,
                       _external=True)

    @classmethod
    def get_provider(self, provider_name):
        if self.providers is None:
            self.providers = {}
            for provider_class in self.__subclasses__():
                provider = provider_class()
                self.providers[provider.provider_name] = provider
        return self.providers[provider_name]

class GithubSignIn(OAuthSignIn):
    def __init__(self):
        super(GithubSignIn, self).__init__('github')
        self.service = OAuth2Service(
            name='github',
            client_id=self.consumer_id,
            client_secret=self.consumer_secret,
            authorize_url='https://github.com/login/oauth/authorize',
            access_token_url='https://github.com/login/oauth/access_token',
            base_url='https://api.github.com'
        )

    def authorize(self):
        return redirect(self.service.get_authorize_url(
            scope='user:email',
            response_type='code',
            #redirect_uri=self.get_callback_url())  #TODO: This needs to be dynamic, missing '/pysalrest/' right now.
	    redirect_uri='https://webpool.csf.asu.edu/pysalrest/user/callback/github')
        )

    def callback(self):
        if 'code' not in request.args:
            return None, None, None
        oauth_session = self.service.get_auth_session(
            data={'code': request.args['code'],
                  #'redirect_uri': self.get_callback_url()}  #TODO: Also needs to be dynamic
		  'redirect_uri': 'https://webpool.csf.asu.edu/pysalrest/user/callback/github'}
        )
        user = oauth_session.get('user').json()
	return (
            'github$' + str(user['id']),
	    user['login'],
	    None
        )

class TwitterSignIn(OAuthSignIn):
    def __init__(self):
        super(TwitterSignIn, self).__init__('twitter')
        self.service = OAuth1Service(
            name='twitter',
            consumer_key=self.consumer_id,
            consumer_secret=self.consumer_secret,
            request_token_url='https://api.twitter.com/oauth/request_token',
            authorize_url='https://api.twitter.com/oauth/authorize',
            access_token_url='https://api.twitter.com/oauth/access_token',
            base_url='https://api.twitter.com/1.1/'
        )

    def authorize(self):
        request_token = self.service.get_request_token(
            params={'user.oauth_callback': self.get_callback_url()}
        )
        session['request_token'] = request_token
        return redirect(self.service.get_authorize_url(request_token[0]))

    def callback(self):
        request_token = session.pop('request_token')
        if 'oauth_verifier' not in request.args:
            return None, None, None
        oauth_session = self.service.get_auth_session(
            request_token[0],
            request_token[1],
            data={'oauth_verifier': request.args['oauth_verifier']}
        )
        me = oauth_session.get('account/verify_credentials.json').json()
        social_id = 'twitter$' + str(me.get('id'))
        username = me.get('screen_name')
        return social_id, username, None   # Twitter does not provide email

@mod_user.route('/', methods=['GET'])
def user_index():
    response = {'status':'success', 'links':[]}
    response['links'] = [{'name':'login', 'href':baseurl + 'user/login/'},
			 {'name':'session', 'href':baseurl + '/user/session/'},
              		 {'name':'logout', 'href':baseurl + '/user/logout/'}]
    return jsonify(response)

@mod_user.route('/login/', methods=['GET'])
def login():
    response = {'status':'success', 'links':[]}
    response['links'] =  [{'name':'twitter', 'href': baseurl + '/user/login/twitter/'},
                          {'name':'github', 'href':baseurl + '/user/login/github/'}]
    return jsonify(response)

@mod_user.route('/login/<provider>/', methods=['GET'])
def login_provider(provider):
    if provider == 'twitter':
	return render_template('twitter.html')
    elif provider == 'github':
	return render_template('github.html')

@mod_user.route('/session/', methods=['GET'])
@login_required
def session():
    print encode_cookie(unicode(current_user.id))
    print dir(current_user)
    response = {'status':'success', 'session_cookie':''}
    sessionid = request.cookies['session']
    response['session_cookie'] = sessionid
    return jsonify(response)

@mod_user.route('/logout/')
def logout():
    logout_user()
    return redirect(url_for('user.user_index'))

@mod_user.route('/authorize/<provider>', methods=['GET'])
def oauth_authorize(provider):
    if not current_user.is_anonymous():
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize()

@mod_user.route('/callback/<provider>')
def oauth_callback(provider):
    if not current_user.is_anonymous():
        return redirect(url_for('user.index'))
    oauth = OAuthSignIn.get_provider(provider)
    social_id, username, email = oauth.callback()
    if social_id is None:
        flash('Authentication failed.')
        return redirect(url_for('user.index'))
    user = User.query.filter_by(social_id=social_id).first()
    if not user:
        user = User(social_id=social_id, nickname=username, email=email)
        db.session.add(user)
        db.session.commit()
    login_user(user, True)
    return redirect(url_for('api_root'))
