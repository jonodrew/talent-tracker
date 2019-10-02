import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ADMINS = ["your-email@example.com"]
    LANGUAGES = ["en", "es"]


class TestConfig(Config):
    SECRET_KEY = "secret-testing-key"
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///testing-database"
