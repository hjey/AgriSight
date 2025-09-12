from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
import io
from PIL import Image
import base64
import torch
import numpy as np
import torch.nn.functional as F
from transformers import SegformerImageProcessor
from model import _create_overlay_image
from config import baseline, optimized
import onnxruntime as ort

app = FastAPI()

baseline_model_path  = "/app/models/baseline.onnx"
optimized_model_path = "/app/models/optimized.onnx"

def get_model_config(model_type: str):
    return baseline if model_type == "baseline" else optimized

def load_onnx_model(model_path: str, device):
    """ONNX 모델 로딩"""
    # CPU에서만 실행 (ONNX Runtime GPU 설정이 복잡함)
    session = ort.InferenceSession(model_path, providers=['CPUExecutionProvider'])
    return session


@app.post("/segment")
async def segment_image(
    image: UploadFile = File(...),
    model_type: str = Form("baseline")
):
    try:
        if not image.content_type.startswith("image/"):
            return JSONResponse({"error": "업로드된 파일이 이미지가 아님"}, status_code=400)

        data = await image.read()
        pil_image = Image.open(io.BytesIO(data)).convert("RGB")

        processor = SegformerImageProcessor.from_pretrained(
            "nvidia/segformer-b0-finetuned-ade-512-512"
        )

        model_path = optimized_model_path if model_type=="optimized" else baseline_model_path
        session = load_onnx_model(model_path, device="cpu")  # ONNX는 CPU 사용

        inputs = processor(images=pil_image, return_tensors="pt")
        pixel_values = inputs['pixel_values']

        # 3채널을 4채널로 변환
        if pixel_values.shape[1] == 3:  # [1, 3, H, W]
            # 더미 채널 추가 (4번째 채널을 RGB 평균으로)
            dummy_channel = pixel_values.mean(dim=1, keepdim=True)  # [1, 1, H, W]
            pixel_values = torch.cat([pixel_values, dummy_channel], dim=1)  # [1, 4, H, W]

        # ONNX 추론
        input_name = session.get_inputs()[0].name
        onnx_output = session.run(None, {input_name: pixel_values.cpu().numpy()})[0]
        logits = torch.from_numpy(onnx_output)

        upsampled = F.interpolate(
            logits,
            size=(pil_image.height, pil_image.width),
            mode="bilinear",
            align_corners=False
        )
        preds_cpu = upsampled.squeeze(0).cpu()

        cfg = get_model_config(model_type)

        # 여기서 numpy 배열을 리스트로 변환
        label_categories = cfg['LABEL_CATEGORIES']
        if isinstance(label_categories, np.ndarray):
            label_categories = label_categories.tolist()

        # original도 원본 크기로 업샘플링
        original_upsampled = F.interpolate(
            pixel_values.squeeze(0)[:3].unsqueeze(0),  # [1, 3, 512, 512]
            size=(pil_image.height, pil_image.width),   # (469, 626)
            mode="bilinear",
            align_corners=False
        ).squeeze(0)  # [3, 469, 626]

        out_img = _create_overlay_image(
            original_upsampled,  # 이제 크기가 맞음
            preds_cpu,
            label_categories,
            alpha=0.5
        )

        buf = io.BytesIO()
        # PIL Image 객체이므로 직접 저장
        out_img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode()

        return {"success": True, "segmented_image": b64}

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)