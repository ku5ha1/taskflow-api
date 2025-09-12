from dotenv import load_dotenv  
import os 
from sqlalchemy import create_engine 
from sqlalchemy.orm import sessionmaker 
from sqlalchemy.ext.declarative import declarative_base 

load_dotenv() 

DATABASE_URL = os.getenv("DATABASE_URL") 
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found")

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base() 

from dotenv import load_dotenv  
import os 
from sqlalchemy import create_engine 
from sqlalchemy.orm import sessionmaker 
from sqlalchemy.ext.declarative import declarative_base 

load_dotenv() 

DATABASE_URL = os.getenv("DATABASE_URL") 
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found")

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base() 

async def get_db():
    db = SessionLocal()
    try:
        print("Yielding database session")
        yield db
    except Exception as e:
        print(f"Database exception: {e}")
        db.close()
        raise e
    finally:
        print("Closing database session")
        db.close()