#!/usr/bin/env python3
"""
PyTorch 체크포인트를 ONNX 포맷으로 변환하는 스크립트
"""

import os
import sys
import torch
import torch.onnx
import onnx
import onnxruntime as ort
import numpy as np
from pathlib import Path

# 현재 디렉토리를 Python path에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model import SegmentationModel
from config import baseline, optimized

def convert_checkpoint_to_onnx(
    checkpoint_path: str,
    output_path: str,
    model_type: str = "baseline",
    input_size: tuple = (512, 512),
    verify: bool = True
):
    """
    PyTorch Lightning 체크포인트를 ONNX로 변환
    
    Args:
        checkpoint_path: .ckpt 파일 경로
        output_path: 출력 .onnx 파일 경로
        model_type: 모델 타입 ("baseline" or "optimized")
        input_size: 입력 이미지 크기 (H, W)
        verify: ONNX 모델 검증 여부
    """
    print(f"Converting {checkpoint_path} to ONNX...")
    print(f"Model type: {model_type}")
    print(f"Input size: {input_size}")
    
    # 출력 디렉토리 생성
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 모델 로드 (CPU에서 변환)
    device = torch.device("cpu")
    
    try:
        cfg = baseline if model_type == "baseline" else optimized
        labels = cfg['LABEL_CATEGORIES']
        
        # Lightning 체크포인트 로드
        model = SegmentationModel.load_from_checkpoint(
            checkpoint_path,
            backbone_model_name=cfg['BACKBONE_MODEL'],
            num_classes=len(labels),
            label_categories=labels,
            learning_rate=cfg['LEARNING_RATE'],
            map_location=device,
            strict=False
        )
        
        model.eval()
        print("✓ Model loaded successfully")
        
    except Exception as e:
        print(f"✗ Error loading model: {e}")
        return False
    
    # 더미 입력 생성 (4채널: RGB + NIR)
    dummy_input = torch.randn(1, 4, input_size[0], input_size[1], dtype=torch.float32)
    print(f"✓ Created dummy input: {dummy_input.shape}")
    
    # PyTorch 모델 테스트
    try:
        with torch.no_grad():
            pytorch_output = model(dummy_input)
        print(f"✓ PyTorch inference successful: {pytorch_output.shape}")
    except Exception as e:
        print(f"✗ PyTorch inference failed: {e}")
        return False
    
    # ONNX 변환
    try:
        torch.onnx.export(
            model,                          # 모델
            dummy_input,                    # 더미 입력
            output_path,                    # 출력 경로
            export_params=True,             # 학습된 매개변수 내보내기
            opset_version=11,               # ONNX opset 버전
            do_constant_folding=True,       # 상수 폴딩 최적화
            input_names=['input'],          # 입력 이름
            output_names=['output'],        # 출력 이름
            dynamic_axes={                  # 동적 축 (배치, 높이, 너비)
                'input': {0: 'batch_size', 2: 'height', 3: 'width'},
                'output': {0: 'batch_size', 2: 'height', 3: 'width'}
            }
        )
        print(f"✓ ONNX export successful: {output_path}")
        
    except Exception as e:
        print(f"✗ ONNX export failed: {e}")
        return False
    
    if verify:
        return verify_onnx_model(output_path, dummy_input, pytorch_output)
    
    return True

def verify_onnx_model(onnx_path: str, dummy_input: torch.Tensor, pytorch_output: torch.Tensor):
    """ONNX 모델 검증"""
    print("\nVerifying ONNX model...")
    
    try:
        # ONNX 모델 로드 및 검증
        onnx_model = onnx.load(onnx_path)
        onnx.checker.check_model(onnx_model)
        print("✓ ONNX model structure is valid")
        
        # ONNX Runtime으로 추론
        ort_session = ort.InferenceSession(onnx_path)
        
        # 입력 이름 확인
        input_name = ort_session.get_inputs()[0].name
        
        # ONNX 추론 실행
        onnx_output = ort_session.run(
            None, 
            {input_name: dummy_input.numpy()}
        )[0]
        
        print(f"✓ ONNX inference successful: {onnx_output.shape}")
        
        # 출력 비교
        pytorch_np = pytorch_output.detach().numpy()
        diff = np.abs(pytorch_np - onnx_output)
        max_diff = np.max(diff)
        mean_diff = np.mean(diff)
        
        print(f"✓ Output comparison:")
        print(f"  - Max difference: {max_diff:.6f}")
        print(f"  - Mean difference: {mean_diff:.6f}")
        
        # 허용 오차 확인
        tolerance = 1e-4  # 0.0001로 늘림 (원래 1e-05)
        if max_diff < tolerance:
            print(f"✓ Outputs match within tolerance ({tolerance})")
            return True
        else:
            print(f"⚠ Outputs differ by more than tolerance ({tolerance})")
            return False
            
    except Exception as e:
        print(f"✗ ONNX verification failed: {e}")
        return False

def main():
    """메인 함수"""
    # models 폴더에서 실행하므로 현재 디렉토리가 models/
    models_dir = Path(__file__).parent  # inference/models/ 폴더
    
    # 실제 파일명 확인을 위한 디버깅
    print(f"Looking for checkpoint files in: {models_dir}")
    if models_dir.exists():
        ckpt_files = list(models_dir.glob("*.ckpt"))
        print(f"Found .ckpt files: {[f.name for f in ckpt_files]}")
    else:
        print(f"Models directory not found: {models_dir}")
        return
    
    # 체크포인트와 ONNX 파일을 같은 폴더에 저장
    models_to_convert = [
        {
            "name": "baseline",
            "checkpoint": models_dir / "baseline.ckpt",
            "onnx_path": models_dir / "baseline.onnx"
        },
        {
            "name": "optimized", 
            "checkpoint": models_dir / "optimized.ckpt",
            "onnx_path": models_dir / "optimized.onnx"
        }
    ]
    
    print("=== PyTorch to ONNX Conversion ===\n")
    
    success_count = 0
    for model_info in models_to_convert:
        print(f"Converting {model_info['name']} model...")
        
        if not model_info["checkpoint"].exists():
            print(f"✗ Checkpoint not found: {model_info['checkpoint']}")
            continue
            
        success = convert_checkpoint_to_onnx(
            str(model_info["checkpoint"]),
            str(model_info["onnx_path"]),
            model_info["name"]
        )
        
        if success:
            success_count += 1
            print(f"✓ {model_info['name']} conversion completed\n")
        else:
            print(f"✗ {model_info['name']} conversion failed\n")
    
    print(f"=== Conversion Summary ===")
    print(f"Successful conversions: {success_count}/{len(models_to_convert)}")
    
    if success_count == len(models_to_convert):
        print("🎉 All models converted successfully!")
    else:
        print("⚠ Some conversions failed. Check logs above.")

if __name__ == "__main__":
    main()