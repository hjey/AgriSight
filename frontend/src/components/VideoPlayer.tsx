// components/VideoPlayer.tsx 수정
'use client';

import { useEffect, useRef } from "react";
import "./videoPlayer.css";

export default function VideoPlayer({ videoId }: { videoId: string }) {
    const videoRef = useRef<HTMLVideoElement>(null);

    useEffect(() => {
        const video = videoRef.current;
        if (!video) return;

        // 비디오 로드 완료 후 자막 트랙 활성화
        const handleLoadedMetadata = () => {
            const tracks = video.textTracks;
            console.log("Available text tracks:", tracks.length);

            if (tracks && tracks.length > 0) {
                for (let i = 0; i < tracks.length; i++) {
                    console.log(`Track ${i}:`, tracks[i].label, tracks[i].kind);
                    tracks[i].mode = 'showing';
                }
            }
        };

        video.addEventListener('loadedmetadata', handleLoadedMetadata);

        // 자막 로드 상태 확인
        setTimeout(() => {
            const tracks = video.textTracks;
            console.log("Tracks after timeout:", tracks.length);
            if (tracks.length > 0) {
                tracks[0].mode = 'showing';
            }
        }, 1000);

        return () => {
            video.removeEventListener('loadedmetadata', handleLoadedMetadata);
        };
    }, []);

    return (
        <div id="video-container" className="flex items-center justify-center h-full w-full">
            <video
                ref={videoRef}
                src={`/videos/${videoId}_trimmed.mp4`}
                controls
                autoPlay
                className="block max-h-full max-w-full object-contain"
            >
                <track
                    src={`/videos/${videoId}_trimmed_subtitles.vtt`}
                    kind="subtitles"
                    srcLang="en"
                    label="English"
                    default
                />
            </video>
        </div>
    );
}