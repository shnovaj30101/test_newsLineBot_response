
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

from sqlalchemy import Column, Index
from sqlalchemy.types import Integer, Text, String, DateTime, Date


class News(Base):
    __tablename__ = 'news_table'

    news_id = Column(String(64), primary_key=True)
    title = Column(String(128), nullable=False)
    source = Column(String(32), nullable=False, index=True)
    url = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    post_time = Column(Date, nullable=False, index=True)
    image_url = Column(Text)
    image_text = Column(Text)
    created_time = Column(DateTime, index=True, default=datetime.now)
    updated_time = Column(DateTime, index=True, default=datetime.now, onupdate=datetime.now)
