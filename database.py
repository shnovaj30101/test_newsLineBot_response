
from sqlalchemy import create_engine, event
import sqlalchemy.schema
import sqlalchemy.orm
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import DisconnectionError
from contextlib import contextmanager

def checkout_listener(dbapi_con, con_record, con_proxy):
    try:
        try:
            dbapi_con.ping(False)
        except TypeError:
            dbapi_con.ping()
    except dbapi_con.OperationalError as exc:
        if exc.args[0] in (2006, 2013, 2014, 2045, 2055):
            raise DisconnectionError()
        else:
            raise

class DataBase:
    def __init__(self, args):
        self.engine = create_engine('mysql://{0}:{1}@{2}:{3}/{4}?charset={5}'.format(args.mysql_user, args.mysql_password, args.mysql_hostname, args.mysql_port, args.mysql_database, 'utf8'), echo=True)
        event.listen(self.engine, 'checkout', checkout_listener)
        metadata = sqlalchemy.schema.MetaData(self.engine)
        print(metadata)

    def __enter__(self):
        DBSession = sessionmaker(bind=self.engine)
        self.db_session = DBSession()
        print('db_session open')

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db_session.close()
        print('db_session close')

    @contextmanager
    def session_wrapper(self):
        try:
            yield self.db_session
            self.db_session.commit()
        except:
            self.db_session.rollback()
            raise

