import subprocess
import yt_dlp


def download_youtube_video(url, output_path='npfQcvUcQYM.mp4'):  # data경로는 읽기 전용
    ydl_opts = {
        'format': 'best',
        'outtmpl': output_path
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    print(f"Downloaded video: {output_path}")

def cut_video(input_path, output_path, start_time, duration):
    cmd = [
        "ffmpeg",
        "-i", input_path,
        "-ss", str(start_time),
        "-t", str(duration),
        "-c", "copy",
        output_path
    ]
    subprocess.run(cmd, check=True)


# download_youtube_video('https://www.youtube.com/watch?v=npfQcvUcQYM')

# cut_video("video.mp4", f"video_segment_1.mp4", start_time=0, duration=60)
# ffmpeg -i data/UibfDUPJAEU.mp4 -ss 00:03:20 -t 60 -c copy data/UibfDUPJAEU_trimmed.mp4
