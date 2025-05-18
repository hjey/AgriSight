'use client';
import { useEffect, useState } from 'react';
import VideoPlayer from '@/components/VideoPlayer';
import FileSelect from '@/components/fileSelect';

export default function YouTubeAnalyzerPage() {
    const [videoId, setVideoId] = useState<string | undefined>(undefined);
    const [language, setLanguage] = useState('en');
    const [videoData, setVideoData] = useState({
        title: '',
        ner: '',
        keywords: '',
        summary: ''
    });
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const baseApiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://backend:8000';
    const API_BASE_URL = typeof window === 'undefined'
        ? baseApiUrl
        : baseApiUrl.replace('backend', 'localhost');

    useEffect(() => {
        const initApp = async () => {
            try {
                console.log('App initialized');
            } catch (error) {
                console.error('Error initializing app:', error);
            }
        };
        initApp();
    }, []);

    useEffect(() => {
        if (videoId) {
            fetchVideoData(videoId, language);
        }
    }, [videoId, language]);

    const fetchVideoData = async (id: string, lang: string) => {
        try {
            setIsLoading(true);
            setError(null);

            const [titleResponse, keywordsResponse, nerResponse, summaryResponse] = await Promise.all([
                fetch(`${API_BASE_URL}/title?video_id=${id}`),
                fetch(`${API_BASE_URL}/keyword?video_id=${id}&language=${lang}`),
                fetch(`${API_BASE_URL}/ner?video_id=${id}&language=${lang}`),
                fetch(`${API_BASE_URL}/summary?video_id=${id}&language=${lang}&model=bart`)
            ]);

            if (!titleResponse.ok) throw new Error('제목을 불러오는데 실패했습니다');
            if (!keywordsResponse.ok) throw new Error('키워드를 불러오는데 실패했습니다');
            if (!nerResponse.ok) throw new Error('개체명을 불러오는데 실패했습니다');
            if (!summaryResponse.ok) throw new Error('요약을 불러오는데 실패했습니다');

            const titleData = await titleResponse.json();
            const keywordsData = await keywordsResponse.json();
            const nerData = await nerResponse.json();
            const summaryData = await summaryResponse.json();


            setVideoData({
                title: titleData.title || '',
                keywords: keywordsData.keywords || [],
                ner: nerData.ner || [],
                summary: summaryData.summary || ''
            });

        } catch (error) {
            console.error('Error fetching data:', error);
            setError(error instanceof Error ? error.message : '데이터를 불러오는데 실패했습니다');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <>
            {/* 영상 선택 UI */}
            <FileSelect onSelect={(selectedId) => setVideoId(selectedId)} />

            {/* 산출물 시각화를 위한 하단 박스 */}
            <div className="flex flex-col border border-gray-300 rounded-lg h-[390px]">
                {/* 상단: 타이틀 표시 블럭 */}
                <div id="title_block" className="bg-gray-100 px-10 py-2 rounded-t-lg min-h-[40px] flex flex-row items-center gap-2">
                    <h2 className="text-lg font-semibold px-2">{videoData.title}</h2>
                </div>

                <div id='main_box' className="grid grid-cols-12 h-[350px]">
                    <div id='left_block' className="h-full p-4 rounded-lg flex items-center justify-center col-span-7">
                        <div className="aspect-video h-full w-auto overflow-hidden">
                            {videoId && <VideoPlayer videoId={videoId} />}
                        </div>
                    </div>

                    <div id="right_block" className="bg-gray-200 p-4 overflow-y-auto col-span-5 h-[347px]">
                        <div className="flex items-center gap-2 py-2">
                            <small>Keyword:</small>
                            <p id="keyword">
                                {Array.isArray(videoData.keywords)
                                    ? videoData.keywords.map(k => k[0]).join(', ')
                                    : ''}
                            </p>
                        </div>

                        <div className="flex items-center gap-2 py-2">
                            <small style={{ width: '70px' }}>NER:</small>
                            <p id="ner">
                                {Array.isArray(videoData.ner)
                                    ? videoData.ner.map((item, index) => (
                                        <span key={index}>{item.word}, </span>
                                    ))
                                    : ''}
                            </p>
                        </div>

                        <div className="flex items-center gap-2 py-2">
                            <small>Summary:</small>
                            <p id="summary">{videoData.summary}</p>
                        </div>
                    </div>
                </div>
            </div>
        </>
    );
}
