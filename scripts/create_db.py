import sqlite3
import whisper
import yt_dlp

# SQLite DB 설정
def create_db():
    conn = sqlite3.connect('data/subtitles.db')
    c = conn.cursor()

    # videos 테이블 생성
    c.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            video_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            url TEXT,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # subtitles 테이블 생성
    c.execute('''
        CREATE TABLE IF NOT EXISTS subtitles (
            subtitle_id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id TEXT NOT NULL,
            language TEXT NOT NULL,
            start_time REAL NOT NULL,
            end_time REAL NOT NULL,
            text TEXT NOT NULL,
            FOREIGN KEY (video_id) REFERENCES videos (video_id)
        )
    ''')

    # summaries 테이블 생성
    c.execute('''
    CREATE TABLE IF NOT EXISTS summaries (
        summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
        video_id TEXT NOT NULL,
        language TEXT NOT NULL,
        model TEXT NOT NULL,
        summary TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (video_id) REFERENCES subtitles(video_id)
    )
    ''')

    conn.commit()
    conn.close()

# YouTube 영상 정보 가져오기
def get_video_info(video_url):
    ydl_opts = {
        'quiet': True,
        'skip_download': True,  # 영상 다운로드 없이 메타데이터만 가져옴
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)
        return {
            "video_id": info.get("id"),
            "title": info.get("title"),
            "url": video_url
        }

# 비디오 정보 저장
def save_video_to_db(video_id, title, url):
    conn = sqlite3.connect('subtitles.db')
    c = conn.cursor()

    c.execute('''INSERT OR IGNORE INTO videos (video_id, title, url) 
                 VALUES (?, ?, ?)''', (video_id, title, url))

    conn.commit()
    conn.close()

# 자막 생성
def generate_subtitles(video_path):
    model = whisper.load_model("base")
    result = model.transcribe(video_path)
    return result['segments']

# 자막을 DB에 저장
def save_subtitles_to_db(subtitles, video_id, language):
    conn = sqlite3.connect('subtitles.db')
    c = conn.cursor()

    for segment in subtitles:
        start_time = segment['start']
        end_time = segment['end']
        text = segment['text']

        c.execute('''INSERT OR IGNORE INTO subtitles (video_id, language, start_time, end_time, text)
                     VALUES (?, ?, ?, ?, ?)''', (video_id, language, start_time, end_time, text))

    conn.commit()
    conn.close()

# 영상과 자막을 DB에 저장
def process_video_and_save_subtitles(video_path, video_url, language='en'):
    # YouTube 메타데이터 가져오기
    video_info = get_video_info(video_url)
    video_id = video_info["video_id"]
    video_title = video_info["title"]

    # 비디오 정보 저장
    save_video_to_db(video_id, video_title, video_url)

    # 자막 생성
    subtitles = generate_subtitles(video_path)

    # 자막 DB에 저장
    save_subtitles_to_db(subtitles, video_id, language)

# DB 생성
create_db()

# video_id = "UibfDUPJAEU"
# # 예제 실행
# video_url = f"https://www.youtube.com/watch?v={video_id}"
# process_video_and_save_subtitles(f'{video_id}_trimmed.mp4', video_url, 'en')
