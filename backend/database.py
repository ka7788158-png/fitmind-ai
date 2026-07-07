from sqlalchemy import create_engine, Column, String, Integer, Float, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

DATABASE_URL = "sqlite:///../gym_fitmind.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Member(Base):
    __tablename__ = "members"

    member_id     = Column(String, primary_key=True, index=True)
    name          = Column(String, nullable=False)
    email         = Column(String, default="")
    phone         = Column(String, default="")
    age           = Column(Integer)
    weight        = Column(Float)
    height        = Column(Float)
    goal          = Column(String)
    diet_type     = Column(String)
    injuries      = Column(String, default="None")
    experience    = Column(String)
    gender        = Column(String, default="male")
    plan          = Column(Text, default="")
    is_premium    = Column(Boolean, default=False)
    is_active     = Column(Boolean, default=True)
    joined_date   = Column(String, default=lambda: datetime.now().strftime("%Y-%m-%d"))
    expiry_date   = Column(String, default="")
    last_checkin  = Column(String, default="")
    total_checkins= Column(Integer, default=0)
    created_at    = Column(DateTime, default=datetime.utcnow)

class Payment(Base):
    __tablename__ = "payments"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    member_id     = Column(String, index=True)
    member_name   = Column(String)
    amount        = Column(Float)
    plan_type     = Column(String)  # monthly, quarterly, yearly
    payment_date  = Column(String)
    expiry_date   = Column(String)
    payment_mode  = Column(String, default="cash")  # cash, upi, card
    notes         = Column(String, default="")
    created_at    = Column(DateTime, default=datetime.utcnow)

class GymProfile(Base):
    __tablename__ = "gym_profile"

    id            = Column(Integer, primary_key=True)
    gym_name      = Column(String, default="My Gym")
    owner_name    = Column(String, default="Owner")
    phone         = Column(String, default="")
    email         = Column(String, default="")
    address       = Column(String, default="")
    password      = Column(String, default="admin123")
    monthly_fee   = Column(Float, default=1000)
    quarterly_fee = Column(Float, default=2500)
    yearly_fee    = Column(Float, default=8000)
    created_at    = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    # create default gym profile if not exists
    profile = db.query(GymProfile).first()
    if not profile:
        db.add(GymProfile())
        db.commit()
    db.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()