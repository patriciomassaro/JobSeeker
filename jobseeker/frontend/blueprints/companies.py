import os
from flask import Blueprint, render_template,url_for,redirect,request
from flask_login import login_required, current_user
from jobseeker.database import DatabaseManager
from jobseeker.database.models import Institution,JobPosting
from jobseeker.scraper.extractors.company_extractor import CompanyExtractor
from sqlalchemy import exists

db=DatabaseManager()

companies_bp = Blueprint('companies', __name__)

COMPANIES_PATH = 'companies'
COMPANIES_HMTL = os.path.join(COMPANIES_PATH, 'index.html')


@companies_bp.route('/', methods=['GET'])
@login_required
def index():
    company_filter = request.args.get('company', '')
    industry_filter = request.args.get('industry', '')
    with db as session:
        # Select the columns explicitly to avoid unpacking issues
        query = session.query(
            Institution.id,
            Institution.name,
            Institution.url,
            Institution.about,
            Institution.website,
            Institution.location,
        )
        if industry_filter:
            query = query.filter(Institution.industry.ilike(f'%{industry_filter}%'))
        if company_filter:
            query = query.filter(Institution.name.ilike(f'%{company_filter}%'))
        companies = query.all()
    return render_template(COMPANIES_HMTL, companies=companies,user=current_user)


@companies_bp.route('/scrape_companies', methods=['GET','POST'])
@login_required
def scrape_companies():
    with db as session:
        company_extractor = CompanyExtractor(search_page="https://www.google.com")
        query = session.query(JobPosting.company_url).filter(
            ~exists().where(Institution.url == JobPosting.company_url)
            )
        not_in_institutions = set([url[0] for url in query.all()])
        company_extractor.process_companies_parallel(not_in_institutions, max_workers=2)
    return redirect(url_for('companies.index'))


