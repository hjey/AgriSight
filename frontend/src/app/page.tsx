'use client';
import { useState } from "react";
import MediaBox from "@/components/MediaBox";
import { segmentImageAPI } from "@/lib/api";

export default function ImageSegmentationPage() {
    const [selectedImage, setSelectedImage] = useState<string | null>(null);
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [segmentedImage, setSegmentedImage] = useState<string | null>(null);
    const [isModelRunning, setIsModelRunning] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [selectedModel, setSelectedModel] = useState("baseline");

    const handleImageSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (file && file.type.startsWith("image/")) {
            setSelectedFile(file);
            const reader = new FileReader();
            reader.onload = (e) => {
                setSelectedImage(e.target?.result as string);
                setSegmentedImage(null);
            };
            reader.readAsDataURL(file);
        }
    };

    const handleRunModel = async () => {
        if (!selectedFile) {
            alert('먼저 이미지를 선택해주세요!');
            return;
        }
        try {
            setIsModelRunning(true);
            setError(null);

            const result = await segmentImageAPI(selectedFile, selectedModel);

            if (result.segmented_image) {
                setSegmentedImage(`data:image/png;base64,${result.segmented_image}`);
            }
        } catch (err) {
            console.error('Model execution error:', err);
            setError(err instanceof Error ? err.message : '모델 실행 중 오류가 발생했습니다');
        } finally {
            setIsModelRunning(false);
        }
    };

    return (
        <>
            {/* 업로드 & 실행 버튼 */}
            <div className="mb-4 flex gap-4">
                <input
                    type="file"
                    accept="image/*"
                    onChange={handleImageSelect}
                    className="block w-[85%] text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                />
                <button
                    onClick={handleRunModel}
                    disabled={isModelRunning || !selectedFile}
                    className={`w-[15%] py-2 px-4 rounded-full text-white text-sm font-semibold transition-colors ${isModelRunning || !selectedFile
                        ? "bg-gray-400 cursor-not-allowed"
                        : "bg-green-400 hover:bg-green-500"
                        }`}
                >
                    {isModelRunning ? "실행중..." : "Run Model"}
                </button>
            </div>

            {/* 모델 선택 */}
            <div className="mb-4 flex gap-6 justify-end">
                {["baseline", "optimized"].map((model) => (
                    <label key={model} className="flex items-center cursor-pointer">
                        <input
                            type="radio"
                            name="model"
                            value={model}
                            checked={selectedModel === model}
                            onChange={(e) => setSelectedModel(e.target.value)}
                            className="mr-2 text-blue-600 focus:ring-blue-500"
                        />
                        <span className="text-sm text-gray-700">
                            {model === "baseline" ? "Baseline SegFormer" : "Optimized SegFormer"}
                        </span>
                    </label>
                ))}
            </div>

            {/* 에러 메시지 */}
            {error && (
                <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
                    {error}
                </div>
            )}

            {/* 시각화 영역 */}
            <div className="flex border border-gray-300 rounded-lg overflow-hidden h-[410px]">
                <MediaBox
                    src={selectedImage}
                    alt="Original Image"
                    title="Original Image"
                    fallback={<div className="text-gray-400 text-center">이미지를 선택하세요</div>}
                />
                <MediaBox
                    src={segmentedImage}
                    alt="Segmentation Result"
                    title="Segmentation Result"
                    fallback={
                        isModelRunning ? (
                            <div className="text-center">
                                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-400 mx-auto mb-2"></div>
                                <p className="text-gray-600">모델 실행 중...</p>
                            </div>
                        ) : (
                            <div className="text-gray-400 text-center">
                                <p>이미지를 선택하고</p>
                                <p>Run Model 버튼을 눌러</p>
                                <p>세그멘테이션 결과를 확인하세요</p>
                            </div>
                        )
                    }
                />
            </div>

            <div className="mt-2 p-1 px-4 rounded-lg border border-gray-300 w-[60%] mx-auto">
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
                    <div className="flex items-center space-x-2">
                        <div className="w-3 h-3 bg-red-500 rounded-sm"></div>
                        <span className="text-xs text-gray-600">구름 그림자</span>
                    </div>
                    <div className="flex items-center space-x-2">
                        <div className="w-3 h-3 bg-yellow-400 rounded-sm"></div>
                        <span className="text-xs text-gray-600">이중 식물</span>
                    </div>
                    <div className="flex items-center space-x-2">
                        <div className="w-3 h-3 bg-cyan-400 rounded-sm"></div>
                        <span className="text-xs text-gray-600">파종기 누락</span>
                    </div>
                    <div className="flex items-center space-x-2">
                        <div className="w-3 h-3 bg-purple-600 rounded-sm"></div>
                        <span className="text-xs text-gray-600">고인 물</span>
                    </div>
                    <div className="flex items-center space-x-2">
                        <div className="w-3 h-3 bg-orange-400 rounded-sm"></div>
                        <span className="text-xs text-gray-600">수로</span>
                    </div>
                    <div className="flex items-center space-x-2">
                        <div className="w-3 h-3 bg-fuchsia-500 rounded-sm"></div>
                        <span className="text-xs text-gray-600">잡초 무리</span>
                    </div>
                </div>
            </div>

        </>
    );
}