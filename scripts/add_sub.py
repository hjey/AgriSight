import moviepy.editor as mp
import srt

video_id = "UibfDUPJAEU"

# 자막 파일 경로와 비디오 파일 경로
video_path = f'data/{video_id}_trimmed.mp4'
subtitle_path = f'data/{video_id}_trimmed_subtitles.srt'
output_video_path = f'data/{video_id}_trimmed_output.mp4'

# 비디오 파일과 오디오 로드
video = mp.VideoFileClip(video_path)
audio = video.audio

# 자막 로드
with open(subtitle_path, 'r', encoding='utf-8') as file:
    subtitles = list(srt.parse(file.read()))

# 자막을 화면에 오버레이하는 함수 정의
def generate_subtitle(clip, subtitles):
    txt_clips = []
    padding_y = 10  # 상하 패딩
    padding_x = 20  # 좌우 패딩

    for sub in subtitles:
        start_time = sub.start.total_seconds()  # 초 단위 변환
        end_time = sub.end.total_seconds()  # 초 단위 변환
        text = sub.content.strip().replace('\n', ' ')  # 줄바꿈을 공백으로 변경

        # 텍스트 클립 생성 (배경 포함)
        txt_clip = mp.TextClip(text, fontsize=20, color='white', font='Arial-Bold',
                               size=(clip.size[0] - 100, None), method='caption')

        # 텍스트 클립을 검은 배경 위에 올리기
        txt_clip = txt_clip.on_color(
            size=(txt_clip.w + 2 * padding_x, txt_clip.h + 2 * padding_y),
            color=(0, 0, 0), col_opacity=0.4  # 배경 투명도 설정
        )

        # 자막 위치 조정
        txt_clip = txt_clip.set_position(('center', clip.size[1] - 20 - txt_clip.h))  # 배경박스의 바닥을 기준으로 함, 높이 변화에도 상관 없음

        # 자막 시간 설정
        txt_clip = txt_clip.set_start(start_time).set_end(end_time)

        # 리스트에 추가
        txt_clips.append(txt_clip)

    # 비디오와 자막을 합성하여 리턴
    return mp.CompositeVideoClip([clip] + txt_clips)

# 자막 추가된 비디오 생성
final_video = generate_subtitle(video, subtitles)

# 오디오 추가
final_video = final_video.set_audio(audio)

# 결과를 새로운 파일로 저장
final_video.write_videofile(output_video_path, codec='libx264', audio_codec='aac')

print("비디오 처리 완료!")
