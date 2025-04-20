-- Adjust missing parts after migration from sqlite to postgresql

ALTER TABLE summaries
ADD CONSTRAINT summaries_video_id_fkey
FOREIGN KEY (video_id)
REFERENCES videos(video_id)
ON DELETE CASCADE;

commit;
