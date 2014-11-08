from flask.ext.wtf import Form
from wtforms import TextField, BooleanField, PasswordField
from wtforms.validators import Required, Email, EqualTo

class LoginForm(Form):
    email = TextField('Email Address', [Email(),
        Required(message='name@domain')])
    password = PasswordField('Password', [Required(message='Enter Password')])
    remember_me = BooleanField('remember_me', default = False)
