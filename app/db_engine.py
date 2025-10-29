from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from settings import settings

engine = create_engine(url=settings.db.get_database_url())

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
