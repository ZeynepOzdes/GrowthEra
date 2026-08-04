from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings


connection_url = URL.create(
    "mssql+pyodbc",
    username=settings.DB_USER,
    password=settings.DB_PASSWORD,
    host=settings.DB_SERVER,
    port=settings.DB_PORT,
    database=settings.DB_NAME,
    query={
        "driver": settings.DB_DRIVER,
        "Encrypt": "yes",
        "TrustServerCertificate": "yes",
    },
)

engine = create_engine(
    connection_url,
    echo=True,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()