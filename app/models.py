import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class ErrorLog(Base):
    __tablename__ = 'error_logs'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    service_name = Column(String(100), nullable=False) # e.g. "Firecrawl", "Gemini", "Backend"
    level = Column(String(50), nullable=False) # "WARNING", "ERROR", "CRITICAL"
    message = Column(String(255), nullable=False) # brief headline
    raw_error = Column(Text, nullable=True) # Full stack trace
    ai_summary = Column(Text, nullable=True) # Gemini interpretation

class DailyStat(Base):
    __tablename__ = 'daily_stats'
    
    date_str = Column(String(20), primary_key=True) # "YYYY-MM-DD"
    emails_sent = Column(Integer, default=0)

engine = create_engine('sqlite:///monitor.db', connect_args={'check_same_thread': False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
