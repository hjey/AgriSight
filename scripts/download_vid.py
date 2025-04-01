import yt_dlp

def download_youtube_video(url, output_path='npfQcvUcQYM.mp4'): #data경로는 읽기 전용
    ydl_opts = {
        'format': 'best',
        'outtmpl': output_path
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    print(f"Downloaded video: {output_path}")

download_youtube_video('https://www.youtube.com/watch?v=npfQcvUcQYM')
