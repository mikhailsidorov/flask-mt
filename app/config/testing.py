import os

from config.base import BaseConfig


class Config(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL_TESTING')
    ELASTICSEARCH_URL = None
