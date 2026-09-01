import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.base import Base, get_db
from main import app

# Set SQLite test database
os.environ["DATABASE_URL"] = "sqlite:///./test_crispr.db"
os.environ["REQUIRE_AUTH"] = "false"

TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///./test_crispr.db"
engine = create_engine(TEST_SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
