from sqlalchemy import create_engine, Column, BigInteger, String, ForeignKey, Date, Text, ARRAY

from sqlalchemy.orm import relationship, sessionmaker, declarative_base
from sqlalchemy.dialects.postgresql import ARRAY


Base = declarative_base()

## REQ CREATE THE DATABASE ( add to bash paths to use psql)






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

# JobPosting Model
class JobPosting(Base):
    __tablename__ = 'job_postings'
    job_id = Column(BigInteger, primary_key=True)
    title = Column(String)
    seniority_level = Column(String)
    employment_type = Column(String)
    job_description = Column(Text)
    company = Column(String)
    company_url = Column(String)
    industries = Column(ARRAY(String))
    job_functions = Column(ARRAY(String))
    job_poster_profile_url = Column(String, nullable=True)
    job_poster_name = Column(String, nullable=True)
    skills = Column(ARRAY(String), nullable=True)

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

engine = create_engine('postgresql+psycopg2://postgres:holaguada2@localhost/jobseeker')
Base.metadata.drop_all(engine)  # This drops all tables
Base.metadata.create_all(engine)