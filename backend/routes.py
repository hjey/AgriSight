# # backend/routes.py

import httpx
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/backend")

INFERENCE_URL = "http://inference:8000/segment"

@router.post("/segment")
async def segment_image(file: UploadFile = File(...), model_type: str = Form("baseline")):
    try:
        print(f"Received file: {file.filename}, size: {file.size}, type: {file.content_type}")
        print(f"Model type: {model_type}")
        
        files = {"image": (file.filename, await file.read(), file.content_type)}
        data = {"model_type": model_type}
        
        print(f"Sending request to inference server: {INFERENCE_URL}")
        
        async with httpx.AsyncClient(timeout=60.0) as client:  # 타임아웃 늘림
            response = await client.post(INFERENCE_URL, files=files, data=data)
            print(f"Inference response status: {response.status_code}")
            
            response.raise_for_status()
            
            # 응답 내용 확인
            result = response.json()
            print(f"Inference result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            
            return result
            
    except httpx.HTTPStatusError as e:
        error_msg = f"Inference server error {e.response.status_code}"
        try:
            error_detail = e.response.json()
            error_msg += f": {error_detail}"
        except:
            error_msg += f": {e.response.text}"
            
        print(f"HTTPStatusError: {error_msg}")
        return JSONResponse({"error": error_msg}, status_code=500)
        
    except httpx.TimeoutException:
        print("Timeout error")
        return JSONResponse({"error": "Request timeout"}, status_code=500)
        
    except Exception as e:
        print(f"Unexpected error: {type(e).__name__}: {str(e)}")
        return JSONResponse({"error": f"Internal error: {str(e)}"}, status_code=500)