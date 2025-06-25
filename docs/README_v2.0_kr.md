# YouTube Subtitle Analyzer


## 개요
사용자가 업로드한 동영상과 자막 파일에서 요약과 키워드, 개체명 인식을 수행하는 머신러닝 웹 서비스.

Next.js 프론트엔드와 FastAPI 백엔드로 구성되며, 백엔드에서 ML 모델로 텍스트 요약과 NER, 키워드 추출을 처리함.


## 주요 기능
- 동영상과 자막 동시 송출
- 영상의 내용 요약, NER, 키워드 추출
- ML 모델을 이용한 자막 자동 생성  
- 생성된 자막 프론트엔드 실시간 표시  
- CORS 설정으로 안전한 API 호출  
- 정적 동영상 파일 프록시 지원


## 시스템 구성
- **Frontend (Next.js)**
사용자 인터페이스. 업로드, 결과 시각화 담당

- **Backend (FastAPI + Celery)**
요청 처리, 데이터 저장, 비동기 작업 분배

- **ML 추론 컨테이너**
사전 학습된 딥러닝 모델로 자막 요약, 키워드 추출, NER 수행


## 사용 기술
**웹 프레임워크:** Next.js, FastAPI

**비동기 처리:** Celery

**머신러닝 모델:**
- BART (요약)
- KeyBERT, spaCy (키워드)
- BERT (NER)

**기타:** Docker, Docker Compose, Python, Node.js, Poetry

## 프로젝트 구조
```
.
├── README.md
├── assets/                    # 데모 이미지 및 영상, ERD, 플로우차트
├── backend/                   # FastAPI 백엔드 및 Celery worker
├── data/                      # 비디오 및 자막 파일
├── docker/                    # 서비스별 Dockerfile
├── docker-compose.yml         # 전체 컨테이너 오케스트레이션
├── docs/                      # 문서 정리
├── frontend/                  # Next.js 프론트엔드
├── inference/                 # 추론 서버 코드
├── scripts/                   # 비디오 전처리 및 자막 생성 스크립트
├── sql/                       # DB 마이그레이션 SQL
└── makefile                   # 빌드 및 실행 단축 명령어
```

## 배포 및 실행
- CORS 정책은 localhost:3000으로 제한하여 보안 유지  
- Docker Compose로 모든 서비스 동시 실행 가능  
- 프론트엔드에서 오는 동영상 요청은 백엔드가 프록시 처리


## 실행 방법
1. 프론트엔드 디렉토리에서 `npm install` 실행 (모듈 설치)  
2. 프로젝트 루트에서 `docker-compose up --build` 실행  
3. 브라우저에서 `http://localhost:3000` 접속


## 플로우차트
![시스템 흐름도](./assets/flow2.png)


## DB 구조  
![DB 구조](./assets/erd.png)


## 시연 영상 및 이미지
![서비스 스크린샷](./assets/demo2.png)  
[Demo 영상 보기](./assets/demo2.mp4)


## 향후 계획
- 키워드 모델 삭제  
- 제목 앞에 분류 모델 결과 추가
- Nginx 적용
- 평가지표 분리

- 영상 내용 관련 챗봇 기능 도입
- ChromaDB 연동 예정


## 라이선스
MIT License
