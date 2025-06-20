from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
import os

# Import config
from .config import config_by_name

# Initialize extensions globally but without an app
db = SQLAlchemy() # No metadata here, models.py will handle it.
csrf = CSRFProtect()
login_manager = LoginManager()
login_manager.login_view = 'main.login' # Assuming routes will be in a 'main' blueprint or similar
login_manager.login_message_category = "info"


def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'default')

    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    # Initialize extensions with the app
    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)

    # User loader for Flask-Login
    # Moved from app.py, need User model
    # from .models import User # This will cause circular import if models imports db from here.
    # This is a classic Flask structure problem.
    # User loader needs to be defined after User model and login_manager are available.
    # It's often done within the blueprint or after models are fully defined.

    # Import and register Blueprints here
    # For example:
    # from .main_routes import main as main_blueprint
    # app.register_blueprint(main_blueprint)

    # from .auth_routes import auth as auth_blueprint
    # app.register_blueprint(auth_blueprint, url_prefix='/auth')

    # For now, since routes are in app.py, this is more complex.
    # The routes in app.py expect a global `app` object.
    # The simplest way to adapt without full blueprint refactor:
    # Make app.py define routes on a blueprint, then register that blueprint here.
    # Or, ensure app.py's routes are imported *after* app is created and extensions initialized.

    # User loader for Flask-Login
    # Needs to be defined after User model is available and login_manager is initialized.
    from .models import User  # Import User model
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Import and register Blueprints here
    from .routes import main as main_blueprint # Import the blueprint from routes.py
    app.register_blueprint(main_blueprint)
    # If you have other blueprints, register them too:
    # from .auth_routes import auth as auth_blueprint
    # app.register_blueprint(auth_blueprint, url_prefix='/auth')


    # CLI command to create database tables
    from .models import init_db as init_db_func
    @app.cli.command("init-db")
    def init_db_command_wrapper():
        with app.app_context(): # Ensure commands run within app context
            init_db_func(app)
        print("Database initialized and tables created.")

    return app
