import os
from flask import Blueprint, render_template,url_for,redirect,request
from flask_login import login_required, current_user
from jobseeker.database import DatabaseManager
from jobseeker.database.models import CoverLetterParagraphs,UserJobComparison,JobPosting,CoverLetterParagraphsExamples

db=DatabaseManager()

cover_letter_feedback_bp = Blueprint('cover_letter_feedback', __name__)

COVER_LETTER_FEEDBACK_PATH = 'cover_letter_feedback'
COVER_LETTER_FEEDBACK_HTML = os.path.join(COVER_LETTER_FEEDBACK_PATH, 'index.html')
COVER_LETTER_EDIT_PARAGRAPH_HTML = os.path.join(COVER_LETTER_FEEDBACK_PATH, 'edit_paragraph.html')


@cover_letter_feedback_bp.route('/', methods=['GET'])
@login_required
def index():
    title_filter = request.args.get('title', '')
    company_filter = request.args.get('company', '')
    with db as session:
        # Select the columns explicitly to avoid unpacking issues
        query = session.query(
            CoverLetterParagraphs.id,
            CoverLetterParagraphs.paragraph_number,
            CoverLetterParagraphs.paragraph_text,
            JobPosting.title,
            JobPosting.company,
            # Add UserJobComparison id to the query with another name
            UserJobComparison.id.label('comparison_id')
        ).join(
            UserJobComparison, CoverLetterParagraphs.comparison_id == UserJobComparison.id
        ).join(
            JobPosting, UserJobComparison.job_posting_id == JobPosting.id
        ).filter(
            UserJobComparison.user_id == current_user.id
        )
        if title_filter:
            query = query.filter(JobPosting.title.ilike(f'%{title_filter}%'))
        if company_filter:
            query = query.filter(JobPosting.company.ilike(f'%{company_filter}%'))
        paragraphs = query.all()
    return render_template(COVER_LETTER_FEEDBACK_HTML, paragraphs=paragraphs,user=current_user, title_filter=title_filter, company_filter=company_filter)


@cover_letter_feedback_bp.route('/edit_paragraph/<int:paragraph_id>/<int:comparison_id>', methods=['GET', 'POST'])
@login_required
def edit_paragraph(paragraph_id,comparison_id):
    with db as session:
        paragraph = session.query(CoverLetterParagraphs).filter_by(id=paragraph_id).first()
        
        comparison = session.query(
            UserJobComparison.comparison,
            JobPosting.job_posting_summary,
        ).join(
            JobPosting, UserJobComparison.job_posting_id == JobPosting.id
        ).filter(
            (UserJobComparison.id == comparison_id) & (UserJobComparison.user_id == current_user.id)
        ).first()

        
        paragraphs = session.query(CoverLetterParagraphs).filter_by(comparison_id=comparison_id).order_by(CoverLetterParagraphs.paragraph_number).all()
        text = '\n\n'.join([p.paragraph_text for p in paragraphs])

        if request.method == 'POST':
            original_paragraph = paragraph.paragraph_text
            paragraph.paragraph_text = request.form['paragraph_text']
            # create an example instance and add it to the database
            example = CoverLetterParagraphsExamples(
                comparison_id=comparison_id,
                paragraph_number=paragraph.paragraph_number,
                original_paragraph_text=original_paragraph,
                edited_paragraph_text=paragraph.paragraph_text
            )
            session.add(example)
            session.commit()
            
            
            return redirect(url_for('cover_letter_feedback.index'))

    return render_template(COVER_LETTER_EDIT_PARAGRAPH_HTML,
                           paragraph=paragraph,
                           comparison=comparison,
                           text=text,
                           user=current_user)
