from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from worker import extract_keywords, process_ner, process_summary
from db import get_subtitles, get_title, get_summary


router = APIRouter()


# 영상 제목
@router.get("/title")
async def title_api(video_id: str = Query(...)):
    title = get_title(video_id)
    if not title:
        return JSONResponse(content={"message": "No title found"}, status_code=404)
    return {"title": title[0][0]}


# 영상 내용의 키워드
@router.get("/keyword")
async def keyword_api(video_id: str = Query(...), language: str = Query(...)):
    subtitles = get_subtitles(video_id, language)
    if not subtitles:
        return {"error": "No subtitles found"}
    text = " ".join([sub[2] for sub in subtitles])
    keywords = extract_keywords(text)
    return {"keywords": keywords}


# 영상 내용의 NER
@router.get("/ner")
async def ner_api(video_id: str = Query(...), language: str = Query(...)):
    subtitles = get_subtitles(video_id, language)
    if not subtitles:
        return {"error": "No subtitles found"}
    ner_result = process_ner(subtitles)
    return {"ner": ner_result}


# 영상 내용의 요약본
@router.get("/summary")
async def summary_api(video_id: str, language: str, model: str = 'bart'):
    # 먼저 DB에 요약이 있는지 확인
    cached = get_summary(video_id, language, model) # from DB
    if cached:
        return {"summary": cached}
    else:
        subtitles = get_subtitles(video_id, language)
        if not subtitles:
            return {"error": "No subtitles found"}    
        task = process_summary(subtitles, video_id, language, model)
        return {"summary": task['final_summary']}
