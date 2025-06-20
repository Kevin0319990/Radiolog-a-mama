# Application configuration settings

import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a_very_hard_to_guess_secret_string'
    # For Flask-SQLAlchemy
    # For SQLite:
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'inventory.db')
    # Example for PostgreSQL:
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
    # 'postgresql://user:password@host:port/dbname'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # CSRF Protection
    WTF_CSRF_ENABLED = True
    # SECRET_KEY is already defined, which is used by Flask-WTF for CSRF

    # Application specific settings
    LOW_STOCK_THRESHOLD = 10 # Products with quantity below this are considered low stock

    # Add other configurations as needed
    # For example, mail server settings for password reset emails
    # MAIL_SERVER = os.environ.get('MAIL_SERVER')
    # MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    # MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    # MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    # MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    # ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL')

# You can create different config classes for different environments
# class DevelopmentConfig(Config):
#     DEBUG = True
#
# class TestingConfig(Config):
#     TESTING = True
#     SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:' # Use in-memory SQLite for tests
#
# class ProductionConfig(Config):
#     DEBUG = False
    # Ensure sensitive data like SECRET_KEY and DATABASE_URL are set via environment variables
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') # Must be set in production
    # SECRET_KEY = os.environ.get('SECRET_KEY') # Must be set in production

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:' # Use in-memory SQLite for tests
    WTF_CSRF_ENABLED = False # Disable CSRF for easier form testing in unit tests
    LOGIN_DISABLED = False # Make sure login is not disabled unless specifically needed for a test
    SERVER_NAME = 'localhost.localdomain' # Re-adding this. Essential for url_for in tests.

class ProductionConfig(Config):
    DEBUG = False
    # Ensure sensitive data like SECRET_KEY and DATABASE_URL are set via environment variables
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') # Must be set in production
    # SECRET_KEY = os.environ.get('SECRET_KEY') # Must be set in production

config_by_name = dict(
    dev=DevelopmentConfig,
    test=TestingConfig,
    prod=ProductionConfig,
    default=DevelopmentConfig
)

# For simplicity, we'll just use the base Config for now.
# The app can be updated to use different configs later if needed.
# from flask import current_app
# current_app.config.from_object(config_by_name[os.getenv('FLASK_ENV') or 'default'])
