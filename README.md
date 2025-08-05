# 🌾 AgriSight
## SegFormer를 활용한 농지 위성 이미지 기반 이상 탐지 및 시각화

### 목표
농업용 위성 이미지에서 고르지 않은 작물 분포나 비정상 지역을 세분화하여 탐지하고, 이를 바탕으로 작업자의 농작업 의사결정을 지원하는 정밀 농업 시스템 개발

### 활용 목적
- 특정 질병 또는 생육 불량 지역을 조기 인지하여 수확 및 방제 계획 수립 시 작업자에게 보조 정보 제공
- 장비/시비 오류로 인한 파종 누락(Planter Skip), 이중 파종(Double Planting) 감지
- 농지 침수(Standing Water), 잡초 번식 지역(Weed Cluster) 식별을 통한 현장 경고 및 정밀 점검 우선순위 부여

---

## 데이터셋: Agriculture Vision

**데이터셋 개요:**
Agriculture-Vision은 미국 퍼듀대학교(Purdue University) 농업 및 생명공학과에서 정밀 농업 및 농업 자동화 연구를 위해 수집한 다중 스펙트럼 위성 영상 기반 시맨틱 세그멘테이션 데이터셋.

**데이터 구성:**
- 총 약 94,000개의 512x512 크기 이미지 패치
- 각 이미지: RGB + NIR (4채널 입력)
- 총 6개 이상 클래스:
  Cloud Shadow, Double Planting, Planter Skip, Standing Water, Waterway, Weed Cluster
- 클래스 간 불균형 심각 / 배경 비율이 90% 이상
- 학습 시 클래스 콜랩스, 편향된 예측 위험 → 손실 함수 조정 및 샘플링 전략 필요

<br><br>

![데이터셋 특성](./assets/agri_vision_dataset.png)  


**데이터 특성 시각화 설명:**

- 배경 픽셀 비율 압도적 우세 → 배경 과적합 위험
- 클래스 간 불균형 심각 → 일부 클래스는 매우 적은 수 존재
- 픽셀 단위로 보면 클래스 마스크 영역 매우 작음 → 실제 분포 매우 제한적
- 마스크 내부 클래스 분포도 편중 심함 → 정밀 분류 필요

---

## 모델 선정 이유

**SegFormer-B0**: Transformer 기반 경량 세그멘테이션 모델
- Mix Transformer 인코더 + Lightweight MLP 디코더
- 적은 파라미터로 높은 표현력, 장거리 의존성 인식 강점
- CNN 대비 경계 인식 우수, 잡음 많고 불균형한 농업 이미지 적합
- 클래스 불균형 상황에서 학습 안정적, 실제 적용 가능한 프로토타입

---

## 실험

### 적용 기술

- 환경 및 프레임워크

  장비: NVIDIA A100, T4, M3

  PyTorch + PyTorch Lightning, Jupyter Notebook

  로깅: TensorBoard, CSVLogger

- 하이퍼파라미터

  Batch Size: 64

  Image Size: 256×256

  Max Epochs: 30

  Learning Rate: 3e-4

  Optimizer: AdamW (Encoder lr ×0.1, Decoder lr 기본)

  LR Scheduler: Warmup + CosineAnnealing

  Mixed Precision, Gradient Accumulation, Clipping 적용

- 손실 함수 및 불균형 해결

  Combined Tversky (0.7) + Focal Loss (0.3)

  Tversky α=0.2, β=0.8 / Focal γ=2.5

  클래스별 동적 가중치 (중요도 × 역빈도), 0.8~2.2 범위 제한

- 모델 구성

  백본: nvidia/segformer-b0-finetuned-ade-512-512 (사전학습)

  입력 4채널(RGB+NIR) 확장

  6개 농업 이상 클래스 분류

<br>

---

## 결과 및 분석

### 평가 지표

  - mIoU, 클래스별 IoU

  - F1-Score (클래스별)

  - Threshold 0.5 기준

---


## 스킬 스택
Python, PyTorch, PyTorch Lightning, Albumentations, OpenCV, Transformers(HuggingFace), TorchMetrics, Matplotlib, Numpy, Jupyter Notebook
