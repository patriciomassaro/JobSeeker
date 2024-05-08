from sqlalchemy import Column, BigInteger, String, ForeignKey, Date, Text, ARRAY, DateTime, Integer, JSON
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, sessionmaker, declarative_base
from sqlalchemy.schema import CheckConstraint
from flask_login import UserMixin
import erdantic as erd


Base = declarative_base()

class CompanySize(Base):
    __tablename__ = 'company_sizes'
    id = Column(BigInteger, primary_key=True)
    text = Column(String)

class JobPosting(Base):
    __tablename__ = 'job_postings'
    id = Column(BigInteger, primary_key=True)
    title = Column(String)
    seniority_level = Column(String)
    employment_type = Column(String)
    job_description = Column(Text)
    company = Column(String)
    company_url = Column(String, nullable=True)
    industries = Column(ARRAY(String))
    job_functions = Column(ARRAY(String))
    job_salary_range_max = Column(BigInteger, nullable=True)
    job_salary_range_min = Column(BigInteger, nullable=True)
    job_poster_profile_url = Column(String, nullable=True)
    job_poster_name = Column(String, nullable=True)
    skills = Column(ARRAY(String), nullable=True)
    date_created = Column(DateTime, default=func.now())
    job_posting_summary = Column(JSON, nullable=True)
    date_updated = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # relationships
    institution = relationship("Institution", backref="job_postings", foreign_keys=[company_url], primaryjoin="JobPosting.company_url==Institution.url")
    user_job_comparisons = relationship("UserJobComparison", back_populates="job_posting")
    
    # Check that range_min is less than range_max if both are not None
    __table_args__ = (
        CheckConstraint('job_salary_range_min <= job_salary_range_max', name='salary_range_min_max_check'),
    )

class Institution(Base):
    __tablename__ = 'institutions'
    id = Column(BigInteger, primary_key=True)
    name = Column(String)
    # url must be unique
    url = Column(String, unique=True)
    about = Column(Text)
    website = Column(String)
    industry = Column(String)
    size = Column(Integer, ForeignKey('company_sizes.id',ondelete='CASCADE'))
    followers = Column(BigInteger)
    location = Column(String, nullable=True)
    specialties = Column(ARRAY(String), nullable=True)
    date_created = Column(DateTime, default=func.now())
    date_updated = Column(DateTime, default=func.now(), onupdate=func.now())

class FilterTime(Base):
    __tablename__ = 'filter_time'
    id = Column(Integer, primary_key=True)
    name = Column(String)

class FilterSalaryRange(Base):
    __tablename__ = 'filter_salary_range'
    id = Column(Integer, primary_key=True)
    name = Column(String)

class FilterExperienceLevel(Base):
    __tablename__ = 'filter_experience_level'
    id = Column(Integer, primary_key=True)
    name = Column(String)

class FilterRemoteModality(Base):
    __tablename__ = 'filter_remote_modality'
    id = Column(Integer, primary_key=True)
    name = Column(String)

class Users(Base,UserMixin):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String)
    name = Column(String)
    password = Column(String)
    resume = Column(BYTEA, nullable=True)
    parsed_personal = Column(JSON, nullable=True)
    parsed_work_experiences = Column(JSON, nullable=True)
    parsed_educations = Column(JSON, nullable=True)
    parsed_languages = Column(JSON, nullable=True)
    parsed_educations = Column(JSON, nullable=True)
    parsed_skills = Column(ARRAY(String), nullable=True)
    

    additional_info = Column(Text, nullable=True)
    date_created = Column(DateTime, default=func.now())
    date_updated = Column(DateTime, default=func.now(), onupdate=func.now())

    #relationship with the comparison
    user_job_comparisons = relationship("UserJobComparison", back_populates="user")

class JobQuery(Base):
    __tablename__ = 'job_queries'
    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String)
    keywords = Column(String, nullable=True)
    location = Column(String, nullable=True)
    company_id = Column(Integer, nullable=True)

    # Set up foreign keys
    salary_range_id = Column(Integer, ForeignKey('filter_salary_range.id',ondelete='CASCADE'), nullable=True)
    time_filter_id = Column(Integer, ForeignKey('filter_time.id',ondelete='CASCADE'), nullable=True)
    experience_level_id = Column(Integer, ForeignKey('filter_experience_level.id',ondelete='CASCADE'), nullable=True)
    remote_modality_id = Column(Integer, ForeignKey('filter_remote_modality.id',ondelete='CASCADE'), nullable=True)

class JobQueryResult(Base):
    __tablename__ = 'job_query_results'
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_query_id = Column(Integer, ForeignKey('job_queries.id',ondelete='CASCADE'))
    job_posting_id = Column(BigInteger, ForeignKey('job_postings.id',ondelete='CASCADE'))

class UserJobComparison(Base):
    __tablename__ = 'user_job_comparisons'
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_posting_id = Column(BigInteger, ForeignKey('job_postings.id',ondelete='CASCADE'))
    user_id = Column(BigInteger, ForeignKey('users.id',ondelete='CASCADE'))
    comparison = Column(JSON)
    cv_pdf = Column(BYTEA, nullable=True)
    cover_letter_pdf = Column(BYTEA, nullable=True)
    date_created = Column(DateTime, default=func.now())
    date_updated = Column(DateTime, default=func.now(), onupdate=func.now())

    #relationships
    user = relationship("Users", back_populates="user_job_comparisons")
    job_posting = relationship("JobPosting", back_populates="user_job_comparisons")
    cover_letter_paragraphs = relationship("CoverLetterParagraphs", back_populates="user_job_comparisons")
    work_experience_paragraphs = relationship("WorkExperienceParagraphs", back_populates="user_job_comparisons")
    cover_letter_paragraphs_examples = relationship("CoverLetterParagraphsExamples", back_populates="user_job_comparisons")
    work_experience_paragraphs_examples = relationship("WorkExperienceParagraphsExamples", back_populates="user_job_comparisons")


class CoverLetterParagraphs(Base):
    __tablename__ = 'cover_letter_paragraphs'
    id = Column(Integer, primary_key=True)
    comparison_id = Column(Integer, ForeignKey('user_job_comparisons.id',ondelete='CASCADE'))
    paragraph_number = Column(Integer)
    paragraph_text = Column(Text)

    __table_args__ = (
        CheckConstraint('paragraph_number > 0', name='paragraph_number_gt_0'),
        CheckConstraint('paragraph_number < 6', name='paragraph_number_lt_6'),
    )

    #relationships
    user_job_comparisons = relationship("UserJobComparison", back_populates="cover_letter_paragraphs")

class WorkExperienceParagraphs(Base):
    __tablename__ = 'work_experience_paragraphs'
    id = Column(Integer, primary_key=True)
    comparison_id = Column(Integer, ForeignKey('user_job_comparisons.id',ondelete='CASCADE'))
    start_year = Column(Integer)
    end_year = Column(Integer, nullable=True)
    title = Column(String)
    company = Column(String)
    accomplishments = Column(ARRAY(String))

    #relationships
    user_job_comparisons = relationship("UserJobComparison", back_populates="work_experience_paragraphs")

    __table_args__ = (
        CheckConstraint('start_year > 0', name='start_year_gt_0'),
        CheckConstraint('end_year > 0', name='end_year_gt_0'),
        # Check that end_year is greater than start_year if end_year is not None
        CheckConstraint('end_year > start_year', name='end_year_gt_start_year')
    )


class WorkExperienceParagraphsExamples(Base):
    __tablename__ = 'work_experience_paragraphs_examples'
    id = Column(Integer, primary_key=True)
    comparison_id = Column(Integer, ForeignKey('user_job_comparisons.id',ondelete='CASCADE'))
    original_title = Column(String)
    original_accomplishments = Column(ARRAY(String))
    edited_title = Column(String)
    edited_accomplishments = Column(ARRAY(String))

    #relationships
    user_job_comparisons = relationship("UserJobComparison", back_populates="work_experience_paragraphs_examples")



class CoverLetterParagraphsExamples(Base):
    __tablename__ = 'cover_letter_paragraphs_examples'
    id = Column(Integer, primary_key=True)
    comparison_id = Column(Integer, ForeignKey('user_job_comparisons.id',ondelete='CASCADE'))
    paragraph_number = Column(Integer)
    original_paragraph_text = Column(Text)
    edited_paragraph_text = Column(Text)

    # paragraph number must be greater than 0 and less than 6
    __table_args__ = (
        CheckConstraint('paragraph_number > 0', name='paragraph_number_gt_0'),
        CheckConstraint('paragraph_number < 6', name='paragraph_number_lt_6'),
    )

    #relationships
    user_job_comparisons = relationship("UserJobComparison", back_populates="cover_letter_paragraphs_examples")
    