import whisper
import datetime
import moviepy.editor as mp
import subprocess
import re

video_id = 'UibfDUPJAEU'

# 비디오 파일 경로
video_path = f"{video_id}_trimmed.mp4"
video = mp.VideoFileClip(video_path)
print(f"잘린 영상 길이: {video.duration}초")

# 초반 공백, 자막 시작 지점 계산
def get_silence_end(video_path):
    cmd = ["ffmpeg", "-i", video_path, "-af", "silencedetect=noise=-30dB:d=0.5", "-f", "null", "-"]
    result = subprocess.run(cmd, stderr=subprocess.PIPE, text=True)
    matches = re.findall(r"silence_end: (\d+\.\d+)", result.stderr)
    return float(matches[0]) if matches else 0.0  # 첫 번째 silence_end 값 사용

# STT
def generate_subtitles(video_path):
    model = whisper.load_model("medium")
    result = model.transcribe(video_path, language='en')
    return result["segments"]

# save to srt file of res of whisper
def save_subtitles_to_srt(subtitles, output_filename=f"{video_id}_trimmed_subtitles.srt"):
    if not subtitles:
        return  # 자막이 없으면 함수 종료

    max_duration = subtitles[-1]["end"]

    with open(output_filename, "w", encoding="utf-8") as f:
        for idx, segment in enumerate(subtitles):
            if segment["start"] > max_duration:
                break

            start_time = str(datetime.timedelta(seconds=segment["start"]))
            end_time = str(datetime.timedelta(seconds=segment["end"]))

            start_time = start_time.split(".")[0]
            end_time = end_time.split(".")[0]

            start_time = ":".join([s.zfill(2) for s in start_time.split(":")])
            end_time = ":".join([s.zfill(2) for s in end_time.split(":")])

            start_time += "." + str(int((segment["start"] % 1) * 1000)).zfill(3)
            end_time += "." + str(int((segment["end"] % 1) * 1000)).zfill(3)

            f.write(f"{idx + 1}\n{start_time} --> {end_time}\n{segment['text']}\n\n")


# Whisper로 자막 생성
subtitles = generate_subtitles(video_path)

# ffmpeg로 silence_end 값 가져오기
silence_offset = get_silence_end(video_path)

# 첫 번째 자막만 silence_end로 보정
if subtitles:
    first_subtitle_start = subtitles[0]["start"]

    time_shift = silence_offset - first_subtitle_start

    if time_shift > 0:  # silence_end가 첫 자막보다 크면 이동
        subtitles[0]["start"] = silence_offset

        # 첫 번째 자막의 종료 시간을 두 번째 자막의 시작 시간과 맞춤
        if len(subtitles) > 1:
            subtitles[0]["end"] = subtitles[1]["start"]

# 보정된 자막을 SRT로 저장
save_subtitles_to_srt(subtitles)
