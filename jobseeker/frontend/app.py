import os

from flask import Flask, render_template
from flask_login import current_user
from flask_login import LoginManager

from jobseeker.database import DatabaseManager
from jobseeker.database.models import  Users
from jobseeker.frontend.blueprints.auth import auth_bp
from jobseeker.frontend.blueprints.users import users_bp
from jobseeker.frontend.blueprints.job_search import job_search_bp
from jobseeker.frontend.blueprints.job_scrape import job_scrape_bp
from jobseeker.frontend.blueprints.cover_letter_feedback import cover_letter_feedback_bp
from jobseeker.frontend.blueprints.companies import companies_bp
from jobseeker.frontend.blueprints.cv_feedback import cv_feedback_bp

ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = DatabaseManager().url

@login_manager.user_loader
def load_user(user_id):
    with db as session:
        return session.query(Users).get(user_id)

# Register the blueprint
app.register_blueprint(auth_bp,url_prefix='/auth')
app.register_blueprint(users_bp,url_prefix='/users')
app.register_blueprint(job_search_bp,url_prefix='/job_search')
app.register_blueprint(job_scrape_bp,url_prefix='/job_scrape')
app.register_blueprint(cover_letter_feedback_bp,url_prefix='/cover_letter_feedback')
app.register_blueprint(companies_bp,url_prefix='/companies')
app.register_blueprint(cv_feedback_bp, url_prefix='/cv_feedback')



db = DatabaseManager()

@app.route('/')
def home():
    return render_template('base.html',user=current_user)

if __name__ == '__main__':
    app.run(debug=True,port=5001) 

