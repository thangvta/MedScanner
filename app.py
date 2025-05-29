import os
import logging
from flask import Flask, flash, redirect, render_template, request, session, url_for, g
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from flask_babel import Babel, _, gettext


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1) # needed for url_for to generate with https

# Configure Babel
app.config['BABEL_DEFAULT_LOCALE'] = 'en'
app.config['BABEL_SUPPORTED_LOCALES'] = ['en', 'vi']
app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'translations'

# Define the locale selector function
def get_locale():
    # Try to get the language from the session
    if 'language' in session:
        return session['language']
    
    # Or try to detect it from the request
    return request.accept_languages.best_match(app.config['BABEL_SUPPORTED_LOCALES'])

# Initialize Babel with the locale selector
babel = Babel(app, locale_selector=get_locale)

# Route to set language
@app.route('/set-language/<language>')
def set_language(language):
    # Store the language preference in the session
    if language in app.config['BABEL_SUPPORTED_LOCALES']:
        session['language'] = language
    
    # Redirect back to the referring page or home page
    return redirect(request.referrer or url_for('index'))

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///medscanner.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
# Initialize db with app
db.init_app(app)

# Initialize LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "info"

# Import routes after app is created to avoid circular imports
from routes import *
from models import User

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

with app.app_context():
    # Make sure to import the models here or their tables won't be created
    import models  # noqa: F401

    db.create_all()
    logging.info("Database tables created")
    
    # Create default roles if they don't exist
    from models import Role
    roles = ['patient', 'doctor', 'pharmacist']
    for role_name in roles:
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            role = Role(name=role_name)
            db.session.add(role)
    
    db.session.commit()
    logging.info("Default roles created")
