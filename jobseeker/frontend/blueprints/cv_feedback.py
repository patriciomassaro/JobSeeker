import os
from flask import Blueprint, render_template,url_for,redirect,request
from flask_login import login_required, current_user
from jobseeker.database import DatabaseManager
import random
from jobseeker.database.models import WorkExperienceParagraphs,UserJobComparison,JobPosting,WorkExperienceParagraphsExamples

db=DatabaseManager()

cv_feedback_bp = Blueprint('cv_feedback', __name__)

CV_FEEDBACK_PATH = 'cv_feedback'
CV_FEEDBACK_HTML = os.path.join(CV_FEEDBACK_PATH, 'index.html')
CV_EDIT_PARAGRAPH_HTML = os.path.join(CV_FEEDBACK_PATH, 'edit_work_experience.html')


@cv_feedback_bp.route('/', methods=['GET'])
@login_required
def index():
    title_filter = request.args.get('title', '')
    company_filter = request.args.get('company', '')
    with db as session:
        # Select the columns explicitly to avoid unpacking issues
        query = session.query(
            WorkExperienceParagraphs.id,
            WorkExperienceParagraphs.start_year.label('start_year'),
            WorkExperienceParagraphs.end_year.label('end_year'),
            WorkExperienceParagraphs.title.label('work_experience_title'),
            WorkExperienceParagraphs.company.label('work_experience_company'),
            WorkExperienceParagraphs.accomplishments.label('work_experience_accomplishments'),
            JobPosting.title.label('job_title'),
            JobPosting.company.label('job_company'),
        ).join(
            UserJobComparison, WorkExperienceParagraphs.comparison_id == UserJobComparison.id
        ).join(
            JobPosting, UserJobComparison.job_posting_id == JobPosting.id
        ).filter(
            UserJobComparison.user_id == current_user.id
        )
        if title_filter:
            query = query.filter(JobPosting.title.ilike(f'%{title_filter}%'))
        if company_filter:
            query = query.filter(JobPosting.company.ilike(f'%{company_filter}%'))
        work_experiences = query.all()
        work_experiences = random.sample(work_experiences,k=min(len(work_experiences),30))
    return render_template(CV_FEEDBACK_HTML, work_experiences=work_experiences,user=current_user, title_filter=title_filter, company_filter=company_filter)


@cv_feedback_bp.route('/edit_work_experience/<int:work_experience_id>/', methods=['GET', 'POST'])
@login_required
def edit_work_experience(work_experience_id):
    with db as session:
        work_experience = session.query(WorkExperienceParagraphs).filter_by(id=work_experience_id).first()
        comparison = session.query(
            UserJobComparison.comparison,
            JobPosting.job_posting_summary,
        ).join(
            JobPosting, UserJobComparison.job_posting_id == JobPosting.id
        ).filter(
            (UserJobComparison.id == work_experience.comparison_id) & (UserJobComparison.user_id == current_user.id)
        ).first()

        if request.method == 'POST':
            original_accomplishments = work_experience.accomplishments
            origianl_title = work_experience.title

            accomplishments = request.form.getlist('accomplishments')
            title = request.form.get('title')

            work_experience.title = title
            work_experience.accomplishments = accomplishments

            # create the example instance and add it to the database
            example = WorkExperienceParagraphsExamples(
                comparison_id=work_experience.comparison_id,
                original_title=origianl_title,
                original_accomplishments=original_accomplishments,
                edited_title=title,
                edited_accomplishments=accomplishments
            )
            session.add(example)
            
            session.commit()
            return redirect(url_for('cv_feedback.index'))
    return render_template(CV_EDIT_PARAGRAPH_HTML, work_experience=work_experience, comparison=comparison,user=current_user)