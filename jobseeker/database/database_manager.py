from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import event
from jobseeker.database.models import Base, Person, Experience, Education, JobPosting, Institution,CompanySize,FilterTime,FilterSalaryRange,FilterExperienceLevel,FilterRemoteModality
from jobseeker.scraper.datatypes import CompanySize as CompanySizeEnum
from jobseeker.logger import Logger
from jobseeker.scraper.query_builder.filters import FilterTime as FilterTimeEnum
from jobseeker.scraper.query_builder.filters import FilterSalaryRange as FilterSalaryRangeEnum
from jobseeker.scraper.query_builder.filters import FilterExperienceLevel as FilterExperienceLevelEnum
from jobseeker.scraper.query_builder.filters import FilterRemoteModality as FilterRemoteModalityEnum


DB_TYPE="postgresql+psycopg2"
USERNAME="pmassaro"
PASSWORD="password"
HOST="localhost"
PORT="5433"
DB_NAME="jobseeker"


class DatabaseManager:
    def __init__(self):
        session = sessionmaker()
        self.engine = create_engine(self.create_url_from_parameters(DB_TYPE, USERNAME, PASSWORD, HOST, PORT, DB_NAME))
        self.Session = sessionmaker(bind=self.engine)
        self.logger = Logger(prefix="DatabaseManager").get_logger()


    def create_url_from_parameters(self, db_type, username, password, host, port, db_name):
        return f"{db_type}://{username}:{password}@{host}:{port}/{db_name}"

    def create_tables(self):
        try:
            self.logger.info("Creating tables")
            Base.metadata.create_all(self.engine)
        except Exception as e:
            self.logger.error(f"Error creating tables: {e}")
            raise e

    def populate_filters(self):
        session = self.get_session()
        filters_db = [FilterSalaryRange, FilterExperienceLevel, FilterRemoteModality, FilterTime]
        filters_enum = [FilterSalaryRangeEnum, FilterExperienceLevelEnum, FilterRemoteModalityEnum, FilterTimeEnum]
        for filter_db, filter_enum in zip(filters_db, filters_enum):
            try:
                if not session.query(filter_db).first():  # Check if table is already populated
                    for item in filter_enum:
                        if item.value is not None:  # Skip enums with None value
                            session.add(filter_db(id=item.value, name=item.name))
                    session.commit()
                    self.logger.info(f"Populated {filter_db.__tablename__} table successfully.")
            except Exception as e:
                session.rollback()
                self.logger.error(f"Error populating {filter_db.__tablename__} table: {e}")
            finally:
                session.close()


    def drop_tables(self):
        try:
            self.logger.info("Dropping tables")
            Base.metadata.drop_all(self.engine)
        except Exception as e:
            self.logger.error(f"Error dropping tables: {e}")
            raise e
    
    def recreate_tables(self):
        self.drop_tables()
        self.create_tables()
        self.populate_company_sizes()
        self.populate_filters()

    def populate_company_sizes(self):
        session = self.get_session()
        try:
            if not session.query(CompanySize).first():  # Check if table is already populated
                for size in CompanySizeEnum:
                    session.add(CompanySize(id=size.value[1], text=size.value[0]))
                session.commit()
                self.logger.info(f"Populated {CompanySize.__tablename__} table successfully.")
        except Exception as e:
            session.rollback()
            self.logger.error(f"Error populating {CompanySize.__tablename__} table: {e}")
        finally:
            session.close()


    def get_session(self):
        return self.Session()
    def add_object(self, obj):
        session = self.get_session()
        try:
            # log the object type that I want to add 
            session.add(obj)
            session.commit()
            self.logger.info(f"Added object successfully")
            return obj.id
        except Exception as e:
            session.rollback()
            self.logger.error(f"Error adding object: {e}")
            raise e
        finally:
            session.close()

    def update_object(self, obj):
        session = self.get_session()
        try:
            session.merge(obj)
            session.commit()
            self.logger.info(f"Updated object successfully")
        except Exception as e:
            session.rollback()
            self.logger.error(f"Error updating object: {e}")
            raise e
        finally:
            session.close()

    def upsert_object(self, model_instance, attributes:list[str]):
        """
        Upsert an object into the database. If the object already exists, update it. If it does not exist, insert it.\
        The attributes parameter is a list of attributes that will be used to check if the object already exists in the database.
        """
        session = self.get_session()
        try:
            # Construct a query based on the attributes
            query = session.query(model_instance.__class__)
            for attr in attributes:
                query = query.filter(getattr(model_instance.__class__, attr) == getattr(model_instance, attr))
            
            existing_row = query.first()
            
            if existing_row:
                #update all the attributes except the id and the attributes we looked up
                for attr in model_instance.__table__.columns.keys():
                    if attr not in attributes and attr not in ["id","date_created", "date_updated"]:
                        setattr(existing_row, attr, getattr(model_instance, attr))
                session.commit()
                session.close()
            else:
                # If the row does not exist, insert it using the add_object method
                session.close()
                self.add_object(model_instance)
            
        except Exception as e:
            session.rollback()
            self.logger.error(f"Error in upsert operation: {e}")
            raise e
        finally:
            session.close()