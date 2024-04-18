from sqlalchemy import create_engine, Column, BigInteger, String, ForeignKey, Date, Text, ARRAY, DateTime, Integer
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, sessionmaker, declarative_base
from sqlalchemy.schema import CheckConstraint


from jobseeker.scraper.datatypes import CompanySize as CompanySizeEnum
from sqlalchemy import event


Base = declarative_base()

class CompanySize(Base):
    __tablename__ = 'company_sizes'
    id = Column(BigInteger, primary_key=True)
    text = Column(String)

class Person(Base):
    __tablename__ = 'persons'
    id = Column(BigInteger, primary_key=True)
    name = Column(String)
    url = Column(String)
    location = Column(String)
    about = Column(Text)
    email = Column(String)
    experiences = relationship("Experience", back_populates="person")
    educations = relationship("Education", back_populates="person")
    date_created = Column(DateTime, default=func.now())
    date_updated = Column(DateTime, default=func.now(), onupdate=func.now())

class Experience(Base):
    __tablename__ = 'experiences'
    id = Column(BigInteger, primary_key=True)
    institution_id = Column(BigInteger)
    person_id = Column(BigInteger, ForeignKey('persons.id'))
    position = Column(String)
    start_date = Column(Date)
    end_date = Column(Date, nullable=True)
    job_description = Column(Text)
    person = relationship("Person", back_populates="experiences")
    date_created = Column(DateTime, default=func.now())
    date_updated = Column(DateTime, default=func.now(), onupdate=func.now())

class Education(Base):
    __tablename__ = 'educations'
    id = Column(BigInteger, primary_key=True)
    institution = Column(String)
    person_id = Column(BigInteger, ForeignKey('persons.id'))
    degree = Column(String)
    start_date = Column(Date)
    end_date = Column(Date, nullable=True)
    description = Column(Text)
    person = relationship("Person", back_populates="educations")
    date_created = Column(DateTime, default=func.now())
    date_updated = Column(DateTime, default=func.now(), onupdate=func.now())

# JobPosting Model
class JobPosting(Base):
    __tablename__ = 'job_postings'
    id = Column(BigInteger, primary_key=True)
    job_id = Column(BigInteger)
    title = Column(String)
    seniority_level = Column(String)
    employment_type = Column(String)
    job_description = Column(Text)
    company = Column(String)
    company_url = Column(String)
    industries = Column(ARRAY(String))
    job_functions = Column(ARRAY(String))
    # foreign key to institutions table
    institution_id = Column(BigInteger, ForeignKey('institutions.id'), nullable=True)
    job_salary_range_max = Column(BigInteger, nullable=True)
    job_salary_range_min = Column(BigInteger, nullable=True)
    job_poster_profile_url = Column(String, nullable=True)
    job_poster_name = Column(String, nullable=True)
    skills = Column(ARRAY(String), nullable=True)
    date_created = Column(DateTime, default=func.now())
    date_updated = Column(DateTime, default=func.now(), onupdate=func.now())

    # Check that range_min is less than range_max if both are not None
    __table_args__ = (
        CheckConstraint('job_salary_range_min <= job_salary_range_max', name='salary_range_min_max_check'),
    )


class Institution(Base):
    __tablename__ = 'institutions'
    id = Column(BigInteger, primary_key=True)
    name = Column(String)
    url = Column(String)
    about = Column(Text)
    website = Column(String)
    industry = Column(String)
    size = Column(BigInteger)
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

class JobQuery(Base):
    __tablename__ = 'job_queries'
    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String)
    keywords = Column(String, nullable=True)
    location = Column(String, nullable=True)
    company_id = Column(Integer, nullable=True)

    # Set up foreign keys
    salary_range_id = Column(Integer, ForeignKey('filter_salary_range.id'), nullable=True)
    time_filter_id = Column(Integer, ForeignKey('filter_time.id'), nullable=True)
    experience_level_id = Column(Integer, ForeignKey('filter_experience_level.id'), nullable=True)
    remote_modality_id = Column(Integer, ForeignKey('filter_remote_modality.id'), nullable=True)

class JobQueryResult(Base):
    __tablename__ = 'job_query_results'
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_query_id = Column(Integer, ForeignKey('job_queries.id'))
    job_posting_id = Column(BigInteger, ForeignKey('job_postings.id'))
    
    
    