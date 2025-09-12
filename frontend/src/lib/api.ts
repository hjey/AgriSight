// src/lib/api.ts
export async function segmentImageAPI(file: File, modelType: string) {
    // 프론트 → 백엔드 호출
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    console.log('API Base URL:', baseUrl); // 디버깅용

    const formData = new FormData();
    formData.append("file", file);
    formData.append("model_type", modelType || "baseline");

    try {
        // 백엔드에서 프록시 처리하므로 추론 경로 없음, 백엔드 라우터 프리픽스 포함
        const response = await fetch(`${baseUrl}/backend/segment`, {
            method: "POST",
            body: formData,
        });

        if (!response.ok) {
            const text = await response.text().catch(() => "");
            throw new Error(`HTTP ${response.status} ${response.statusText} - ${text}`);
        }

        return await response.json();
    } catch (error) {
        console.error('API call failed:', error);
        throw error;
    }
}
