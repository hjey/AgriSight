```

ERROR:
교차 출처 요청 차단: 동일 출처 정책으로 인해 http://backend:8000/title?video_id=UibfDUPJAEU에 있는 원격 리소스를 차단했습니다. (원인: CORS 요청이 성공하지 못함). 상태 코드: (null).

REASON:
컨테이너간 연결은 Localhost, 127.0.0.1으로 불가능. 모두 컨테이너명으로 교체해야 한다.
웹사이트에선 컨테아너명을 쓰면 안된다. 이 때는 또 localhost나 ip를 사용해야 한다.

tsx, ts 파일에 클라이언트 사이드에선 컨테이너명을 로컬호스트 등으로 교체한다. 

CODE TO CHANGE:
const baseApiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://backend:8000';
const API_URL = typeof window === 'undefined'
    ? baseApiUrl  // 서버 사이드에서는 원래 URL 사용
    : baseApiUrl.replace('backend', 'localhost');

```
