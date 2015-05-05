from app import db
from flask.ext.login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = 'oauth2users'
    id = db.Column(db.Integer, primary_key=True)
    social_id = db.Column(db.String(64), nullable=False, unique=True)
    nickname = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(64), nullable=True)


