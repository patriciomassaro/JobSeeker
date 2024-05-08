import os

from flask import Blueprint, render_template, request, redirect, session as flask_session, send_file, url_for
from flask_login import current_user
from io import BytesIO
import json

from jobseeker.llm import ModelNames
from jobseeker.llm.cv_data_extractor import CVLLMExtractor
from jobseeker.database import DatabaseManager
from jobseeker.database.models import Users


db = DatabaseManager()
LLM_MODEL_NAMES = [(model.name, model.value) for model in ModelNames]
USERS_PATH = 'users'
DASHBOARD_TEMPLATE = os.path.join(USERS_PATH, 'dashboard.html')
users_bp = Blueprint('users', __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ['pdf']

@users_bp.route('/dashboard')
def dashboard():
    if current_user.is_authenticated:
        with db as session:
            user = session.get(Users,current_user.id)
        return render_template(DASHBOARD_TEMPLATE,
                                user=user,
                                model_names=LLM_MODEL_NAMES)
    else:
        return redirect(url_for('auth.login'))

@users_bp.route('/pdf/<int:user_id>')
def serve_pdf(user_id):
    with db as session:
        user = session.get(Users, user_id)
        if user and user.resume:
            pdf_io = BytesIO(user.resume)  # Create a file-like object from bytes
            return send_file(pdf_io, mimetype='application/pdf')
        else:
            return 'PDF not found'

@users_bp.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    if current_user.is_authenticated:
        return redirect(url_for('auth.login'))

    file = request.files.get('pdf_file')  # Use .get() to avoid KeyError if not found
    
    if file and allowed_file(file.filename):
        pdf_data = file.read()
        
        with db as db_session:
            user = db_session.query(Users).filter_by(id=current_user.id).first()
            if user:
                user.resume = pdf_data
                db_session.commit()

        return redirect(url_for('users.dashboard'))
    else:
        return 'Invalid file format or no file provided, please upload a PDF.'
    
@users_bp.route('/parse_pdf', methods=['POST'])
def parse_pdf():
    selected_model_name = request.form['model_name']
    extractor = CVLLMExtractor(model_name=selected_model_name,temperature=0)
    extractor.extract_cv_and_write_to_db(user_id=current_user.id, replace_existing_summary=True)
    return redirect(url_for('users.dashboard'))
    
@users_bp.route('/save_comments', methods=['POST'])
def save_comments():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    
    comments = request.form['comments']
    
    with db as db_session:
        user = db_session.query(Users).filter_by(id=current_user.id).first()
        if user:
            user.additional_info = comments
            db_session.commit()
    return redirect(url_for('users.dashboard'))
