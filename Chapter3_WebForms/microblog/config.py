import os
import json

class Config(object):
    with open('secret.json', 'r') as f:
        secret = json.loads(f.read())
        SECRET_KEY = os.environ.get('SECRET_KEY') or secret['SECRET_KEY']
