import os
import json
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    with open('secret.json', 'r') as f:
        secret = json.loads(f.read())
        SECRET_KEY = os.environ.get('SECRET_KEY') or secret['SECRET_KEY']
    
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    with open('email.json', 'r') as f2:
        email = json.loads(f2.read())
        ADMINS = email['ERROR_REPORT_EMAIL']
