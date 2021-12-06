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
