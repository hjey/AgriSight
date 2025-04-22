from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import os

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@postgres:5432/{POSTGRES_DB}"

engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=2,
    pool_timeout=10,
    pool_recycle=3600
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def check_postgres_connection():
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ PostgreSQL 연결 성공!")
        return True
    except SQLAlchemyError as e:
        print(f"❌ PostgreSQL 연결 실패: {e}")
        return False


def get_subtitles(video_id: str, language: str):
    session = SessionLocal()
    try:    
        result = session.execute(
            text("SELECT start_time, end_time, text FROM subtitles WHERE video_id = :video_id AND language = :language ORDER BY start_time"),
            {"video_id": video_id, "language": language}
        ).fetchall()
        return result if result else None
    except Exception as e:
        print(f"DB Error: {e}")
        return None
    finally:
        session.close()


def get_title(video_id: str):
    session = SessionLocal()
    try:
        result = session.execute(
            text("SELECT title FROM videos WHERE video_id = :video_id"), 
            {"video_id": video_id}
        ).fetchall()
        return result if result else None
    except Exception as e:
        print(f"DB Error: {e}")
        return None
    finally:
        session.close()    


def get_summary(video_id: str, language: str, model: str):
    session = SessionLocal()
    try:
        result = session.execute(
            text("SELECT summary FROM summaries WHERE video_id = :video_id AND language = :language"),
            {"video_id": video_id, "language": language}
        ).fetchone()
        return result[0] if result else None
    except Exception as e:
        print(f"DB Error: {e}")
        return None
    finally:
        session.close()        
    
def save_summary(video_id: str, language: str, model: str, summary: str):
    session = SessionLocal()
    try:
        session.execute(
            text('''
                INSERT INTO summaries (video_id, language, model, summary)
                VALUES (:video_id, :language, :model, :summary)
                ON CONFLICT (video_id, language) DO NOTHING
            '''),
            {"video_id": video_id, "language": language, "model": model, "summary": summary}
        )
        session.commit()
        session.close()
    except Exception as e:
        print(f"DB Error: {e}")
    finally:
        session.close()    
