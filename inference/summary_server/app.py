# app.py

from fastapi import FastAPI, Request
from pydantic import BaseModel
from summary_model import load_model, summarize

app = FastAPI()
model, tokenizer = load_model()

class SummaryRequest(BaseModel):
    text: str

@app.post("/infer")
def infer(req: SummaryRequest):
    result = summarize(model, tokenizer, req.text)
    return {"summary": result}
