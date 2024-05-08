import time
import os
from io import BytesIO

from flask import Blueprint, render_template, request, redirect, session as flask_session, flash, url_for, send_file, abort,jsonify, Response, stream_with_context
from flask_login import current_user
from jobseeker.database import DatabaseManager
from jobseeker.scraper.orchestrator import MainOrchestrator
from jobseeker.scraper.query_builder.filters import FilterRemoteModality, FilterSalaryRange, FilterTime,FilterExperienceLevel
from sqlalchemy.orm import joinedload
from jobseeker.logger import Logger


db=DatabaseManager()
job_scrape_bp = Blueprint('job_scrape', __name__)
# PROJECT ROOT
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
JOB_SCRAPE_PATH= 'job_scrape'
JOB_SCRAPE_HTML = os.path.join(JOB_SCRAPE_PATH, 'scrape.html')

base_url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"

def form_value(value):
    """Convert form values from 'None' string to None type."""
    return None if value == 'None' or value == '' else int(value)

@job_scrape_bp.route('/run', methods=['POST'])
def run():
    log_filename = request.form['logFilename']

    keywords = request.form['keywords']
    location = request.form['location']
    salary_range = FilterSalaryRange(form_value(request.form['salary_range']))
    time_filter = FilterTime(form_value(request.form['time_filter']))
    experience_level = FilterExperienceLevel(form_value(request.form['experience_level']))
    remote_modality = FilterRemoteModality(form_value(request.form['remote_modality']))
    company_id =form_value(request.form['company_id'])

    # Initialize the orchestrator
    orchestrator = MainOrchestrator(jobs_base_url=base_url,
                                    log_file_name=log_filename,
                                    job_posting_max_workers=10,
                                    company_max_workers=2)

    # Run the job with the form data
    orchestrator.run_scraping_job(
        keywords=keywords,
        location=location,
        salary_range=salary_range,
        time_filter=time_filter,
        experience_level=experience_level,
        remote_modality=remote_modality,
        company_id=company_id
    )
    flash("Scraping started successfully!", 'success')
    return redirect(url_for('job_scrape.index'))

@job_scrape_bp.route('/log_stream/<filename>')
def log_stream(filename):
    def generate():
        with open(os.path.join(PROJECT_ROOT,filename, 'r')) as f:
            while True:
                where = f.tell()
                line = f.readline()
                if not line:
                    time.sleep(1)
                    f.seek(where)
                else:
                    yield line.replace('\n', '<br/>\n')
    return Response(generate(), mimetype='text/html')

@job_scrape_bp.route('/')
def index():
    # Render the main scraping page
    return render_template(JOB_SCRAPE_HTML,
                           user=current_user,
                           FilterTime=FilterTime,
                           FilterSalaryRange=FilterSalaryRange,
                           FilterExperienceLevel=FilterExperienceLevel,
                           FilterRemoteModality=FilterRemoteModality)
