
import os
from io import BytesIO
import random

from flask import Blueprint, render_template, request, redirect, session as flask_session, flash, url_for, send_file, abort
from flask_login import current_user
from jobseeker.database import DatabaseManager
from jobseeker.database.models import JobPosting, UserJobComparison
from jobseeker.llm import ModelNames
from jobseeker.llm.job_description_extractor import JobDescriptionLLMExtractor
from jobseeker.llm.requirements_qualification_comparator import RequirementsQualificationsComparator
from jobseeker.llm.cv_builder import CVBuilder
from jobseeker.llm.cover_letter_builder import CoverLetterBuilder
from sqlalchemy.orm import joinedload



db=DatabaseManager()
job_search_bp = Blueprint('job_search', __name__)
JOB_SEARCH_PATH= 'job_search'
JOB_SEARCH_HTML = os.path.join(JOB_SEARCH_PATH, 'postings.html')
LLM_MODEL_NAMES = [(model.name, model.value) for model in ModelNames]

@job_search_bp.route('/', methods=['GET'])
def index():
    if not current_user.is_authenticated:
        return redirect('/auth/login')
    title_filter = request.args.get('title', '')
    company_filter = request.args.get('company', '')
    job_ids = request.args.get('job_ids', '')
    with db as session:
        query = session.query(JobPosting).options(
            joinedload(JobPosting.institution),
            joinedload(JobPosting.user_job_comparisons)
        )
        if title_filter:
                query = query.filter(JobPosting.title.ilike(f'%{title_filter}%'))
        if company_filter:
            query = query.filter(JobPosting.company.ilike(f'%{company_filter}%'))
        if job_ids:
            ids_list = [int(id.strip()) for id in job_ids.split(',')]
            query = query.filter(JobPosting.id.in_(ids_list))
        postings = query.all()
        if len(postings)!=0:
            postings= random.sample(postings,k=min(len(postings),30))
    return render_template(JOB_SEARCH_HTML, postings=postings,user=current_user,model_names=LLM_MODEL_NAMES)


@job_search_bp.route('/parse-job/<int:job_id>', methods=['POST'])
def parse_job(job_id):
    try:
        #get the model name from the form
        model_name = request.form['model_name']
        job_posting_parser = JobDescriptionLLMExtractor(model_name=model_name)
        # Assuming you have a function that takes a list of job IDs to update.
        job_posting_parser.update_job_postings(job_ids=[job_id],replace_existing=True)
        flash('Job description parsed successfully.', 'success')
    except Exception as e:
        # You should log this exception and handle it appropriately in production.
        flash(f'An error occurred: {e}', 'error')
    
    return redirect(url_for('job_search.index'))


@job_search_bp.route('/compare-job-user/<int:job_id>', methods=['POST'])
def compare_job_user(job_id):
    try:
        model_name = request.form['model_name']
        comparator = RequirementsQualificationsComparator(model_name=model_name,
                                                          user_id=current_user.id,
                                                          temperature=0.5)
        comparator.compare_job_postings_with_user(job_ids=[job_id], replace_previous_comparison_flag=True)
        flash('Job description compared to user CV successfully.', 'success')
    except Exception as e:
        flash(f'An error occurred: {e}', 'error')
    
    return redirect(url_for('job_search.index'))

@job_search_bp.route('/generate_cv/<int:job_id>', methods=['POST'])
def generate_cv(job_id):
    try:
        use_llm = bool(int(request.form['use_llm']))
        model_name = request.form['model_name']
        builder = CVBuilder(model_name=model_name, user_id=current_user.id, temperature=0.9)
        builder.build(job_ids=[job_id], use_llm=use_llm)
        flash('Generated CV successfully.', 'success')
    except Exception as e:  
        print(e)
        flash(f'An error occurred: {e}', 'error')
    return redirect(url_for('job_search.index'))

@job_search_bp.route('/generate-cover-letter/<int:job_id>', methods=['POST'])
def generate_cover_letter(job_id:int):
    try:
        use_llm = bool(int(request.form['use_llm']))
        model_name = request.form['model_name']
        builder = CoverLetterBuilder(model_name=model_name, user_id=current_user.id, temperature=0.5)
        builder.build(job_ids=[job_id], use_llm=use_llm)
        flash('Generated cover letter successfully.', 'success')
    except Exception as e:
        flash(f'An error occurred: {e}', 'error')
    return redirect(url_for('job_search.index'))

@job_search_bp.route('/download-cover_letter/<int:user_id>/<int:job_id>')
def download_cover_letter(job_id, user_id):
    with db as session:
        comparison = session.query(UserJobComparison).filter_by(
            job_posting_id=job_id, user_id=user_id
        ).first()
        job_columns = [
                    getattr(JobPosting, attr) for attr in JobPosting.__table__.columns.keys()
                    if attr in ["title","company"] 
                ]
        job = session.query(*job_columns).filter(JobPosting.id == job_id).first()
        job = job._asdict()
        job["company"] = job["company"].replace(" ","").replace(",","").replace("/","").replace(".","")
        job["title"] = job["title"].replace(" ","").replace(",","").replace("/","").replace(".","")
        file_name=job["company"]+ "_" + job["title"]
        
        if comparison and comparison.cover_letter_pdf:
            # Convert bytes to a file-like object
            pdf_bio = BytesIO(comparison.cover_letter_pdf)
            pdf_bio.seek(0)
            # Send file
            return send_file(pdf_bio, mimetype='application/pdf', as_attachment=True, download_name=f'{file_name}_cover_letter.pdf')
        else:
            # If no PDF is found, return a 404 error
            abort(404, description="PDF not found.")

@job_search_bp.route('/download-cv/<int:user_id>/<int:job_id>')
def download_cv(job_id, user_id):
    with db as session:
        comparison = session.query(UserJobComparison).filter_by(
            job_posting_id=job_id, user_id=user_id
        ).first()
        job_columns = [
                    getattr(JobPosting, attr) for attr in JobPosting.__table__.columns.keys()
                    if attr in ["title","company"] 
                ]
        job = session.query(*job_columns).filter(JobPosting.id == job_id).first()
        job = job._asdict()
        job["company"] = job["company"].replace(" ","").replace(",","").replace("/","").replace(".","")
        job["title"] = job["title"].replace(" ","").replace(",","").replace("/","").replace(".","")
        file_name=job["company"]+ "_" + job["title"]
        
        if comparison and comparison.cv_pdf:
            # Convert bytes to a file-like object
            pdf_bio = BytesIO(comparison.cv_pdf)
            pdf_bio.seek(0)  # Go to the beginning of the file-like object
            # Send file
            return send_file(pdf_bio, mimetype='application/pdf', as_attachment=True, download_name=f'{file_name}_CV.pdf')
        else:
            # If no PDF is found, return a 404 error
            abort(404, description="PDF not found.")