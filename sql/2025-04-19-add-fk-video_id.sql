-- sqlite에서 postgresql로 마이그레이션 진행 후 누락 사항 조정

ALTER TABLE summaries
ADD CONSTRAINT summaries_video_id_fkey
FOREIGN KEY (video_id)
REFERENCES videos(video_id)
ON DELETE CASCADE;

commit;
