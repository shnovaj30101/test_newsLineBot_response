
from sqlalchemy import create_engine
import sqlalchemy.schema
import sqlalchemy.orm
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from contextlib import contextmanager

engine = create_engine('mysql://{0}:{1}@{2}:{3}/{4}?charset={5}'.format('root', 'password', 'localhost', 3306, 'news_data', 'utf8'), echo=True)
metadata = sqlalchemy.schema.MetaData(engine)
print(metadata)
DBSession = sessionmaker(bind=engine)
db_session = DBSession()
Base = declarative_base()

@contextmanager
def session_wrapper(session=db_session):
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


