import logging

from sqlalchemy import Column, DateTime, Float, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DB_NAME = "sqlite:///sensor_readings.db"
Base = declarative_base()
logger = logging.getLogger(__name__)


class SensorReading(Base):
    __tablename__ = "SensorReading"

    id = Column(Integer, primary_key=True)
    timestamp = Column(String(100))
    sensor_id = Column(Integer)
    reading_value = Column(Float)


class SQLite:
    def __init__(self, echo=False):
        engine = create_engine(DB_NAME, echo=echo)
        Base.metadata.create_all(bind=engine)
        Session = sessionmaker(engine)
        self._session = Session()

    def store(self, item):
        with self._session as session:
            session.add(item)
            session.commit()

        logger.info("Value correctly stored into DB")
