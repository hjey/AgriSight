// src/lib/api.ts
const baseApiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://backend:8000';
const API_URL = typeof window === 'undefined'
    ? baseApiUrl  // 서버 사이드에서는 원래 URL 사용
    : baseApiUrl.replace('backend', 'localhost');  // 클라이언트 사이드에서는 localhost로 변경

export async function fetchFromAPI<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${API_URL}${endpoint}`);
    if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
    }
    return await response.json() as T;
}