from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime
)

from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class Media(Base):

    __tablename__ = "media"

    id = Column(Integer, primary_key=True)

    conversation = Column(String(255), nullable=False)

    file_name = Column(String(255), nullable=False)

    file_hash = Column(String(64), unique=True)

    file_size = Column(Integer)

    media_type = Column(String(20))

    download_date = Column(DateTime, default=datetime.utcnow)

    status = Column(String(20))