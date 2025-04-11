import sqlite3

DB_PATH = "/data/subtitles.db"

def get_subtitles(video_id: str, language: str):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT start_time, end_time, text FROM subtitles WHERE video_id = ? AND language = ? ORDER BY start_time",
            (video_id, language)
        )
        subtitles = cursor.fetchall()
        conn.close()
        if not subtitles:
            return None
        return subtitles

    except Exception as e:
        print(f"DB Error: {e}")
        return None


def get_title(video_id: str):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT title FROM videos WHERE video_id = ?",
            (video_id,)
        )
        title = cursor.fetchall()
        conn.close()

        return title if title else None

    except Exception as e:
        print(f"DB Error: {e}")
        return None


def get_summary(video_id: str, language: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT summary FROM summaries WHERE video_id = ? AND language = ?",
        (video_id, language)
    )
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def save_summary(video_id: str, language: str, model: str, summary: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        '''INSERT OR IGNORE INTO summaries (video_id, language, model, summary)
            VALUES (?, ?, ?, ?)''', (video_id, language, model, summary))
    conn.commit()
    conn.close()
