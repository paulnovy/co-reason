from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 1. użyj prawidłowego dialektu
SQLALCHEMY_DATABASE_URL = (
    "postgresql+psycopg2://optimizer:optimizer_pass@localhost:5432/optimizer_db"
)

# 2. dodaj future=True / echo=True w dev (bardziej czytelne logi)
engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True, future=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()
