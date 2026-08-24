import os
import time 
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres_admin:secure_vector_password@postgres-db:5432/doc_intelligence"
)

# Engine setup with connection pool
engine = create_engine(DATABASE_URL,pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def init_db():
    """pgvector extension going to enable and create tables ."""
    retries=10
    for attempt in range(1, retries +1):
        try:
            with engine.connect() as conn:
                    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector; "))
                    conn.commit()
            Base.metadata.create_all(bind=engine)
            print(" PostgreSQL and pgvector initialized successfully!")
            return
        except Exception as e:
             print(f" Waiting for DB (Attempt {attempt}/{retries})... Error: {e})")
             time.sleep(2)
             
    raise RuntimeError("Failed to connect to PostgreSQL database.")

def get_db():
    """FastAPI dependency for DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()