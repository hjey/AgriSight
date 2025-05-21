from celery import Celery
from keybert import KeyBERT
from transformers import pipeline
import re
import spacy
import evaluate
import requests

# Celery 인스턴스 생성
celery = Celery(
    "worker",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0"
)
celery.autodiscover_tasks(['worker'])


def call_summary_server(text: str):
    response = requests.post(
        "http://summary_server:8000/infer",
        json={"text": text}
    )
    return response.json()["summary"]


# Keyword
kw_model = KeyBERT(model="sentence-transformers/all-MiniLM-L6-v2")
# NER
nlp = spacy.load("en_core_web_sm")
ner_model = pipeline("ner", model="dslim/bert-base-NER")

# Matric
bertscore_metric = evaluate.load("bertscore")
rouge_metric = evaluate.load("rouge")
bleu_metric = evaluate.load("bleu")


def postprocess_ner(ner_result, source_text):
    merged_entities = []
    current_entity = None

    for entity in ner_result:
        word = entity["word"]
        label = entity["entity"]

        # ##이 붙은 토큰 정리
        if word.startswith("##"):
            if current_entity:
                current_entity["word"] += word[2:]
            continue
        # 같은 개체명(LOC, PER, ORG 등)이 연속되면 묶기
        if label.startswith("B-") or current_entity is None or label != current_entity["entity"]:
            if current_entity:
                merged_entities.append(current_entity)
            current_entity = {"word": word, "entity": label[2:]}  # B- 제거
        else:
            current_entity["word"] += " " + word
    if current_entity:
        merged_entities.append(current_entity)
    # 추가 후처리: 중복 및 포함관계 정리
    filtered_entities = []
    seen = set()

    for i, ent in enumerate(merged_entities):
        word, label = ent["word"], ent["entity"]
        if filtered_entities and filtered_entities[-1]["entity"] == label:
            filtered_entities[-1]["word"] += " " + word
            continue
        if len(word) <= 2 and word.lower() not in {"jr", "dc", "us"}:
            continue
        if any(word == e["word"] and label == e["entity"] for e in filtered_entities):
            continue
        if (word, label) not in seen:
            seen.add((word, label))
            filtered_entities.append(ent)
    filtered_entities = remove_hallucinated_entities(filtered_entities, source_text)
    filtered_entities = split_overlong_names(filtered_entities)
    return filtered_entities


def remove_hallucinated_entities(entities, source_text):
    cleaned = []
    source_text_lower = source_text.lower()

    for ent in entities:
        word = ent["word"].strip()
        if len(word) <= 2:
            continue  # 너무 짧은 건 제거
        if word.lower() not in source_text_lower:
            continue  # 자막 원문에 등장하지 않으면 제거
        cleaned.append(ent)
    return cleaned

def split_overlong_names(entities, max_words=3):
    result = []
    for ent in entities:
        words = ent["word"].split()
        if len(words) > max_words:
            for i in range(0, len(words), max_words):
                part = " ".join(words[i:i + max_words])
                result.append({"word": part, "entity": ent["entity"]})
        else:
            result.append(ent)
    return result


def clean_summary(text):
    # ". <n>" → "."
    text = re.sub(r"\.\s*<n>", ". ", text)
    # " <n>" → " "
    text = re.sub(r"\s*<n>", " ", text)
    return text.strip()

def compute_bertscore(prediction, reference):
    score = bertscore_metric.compute(
        predictions=[prediction],
        references=[reference],
        model_type="bert-base-uncased"
    )
    return score["f1"][0]

def compute_rouge(prediction, reference):
    score = rouge_metric.compute(
        predictions=[prediction],
        references=[reference]
    )
    return score["rougeL"]

def compute_bleu(prediction, reference):
    score = bleu_metric.compute(
        predictions=[prediction],
        references=[[reference]]
    )
    return score["bleu"]


def extract_keywords(text):
    return kw_model.extract_keywords(text, keyphrase_ngram_range=(1, 2), stop_words="english")


def process_ner(subtitles):
    text = " ".join([sub[2] for sub in subtitles])
    # 1. spaCy NER
    doc = nlp(text)
    spacy_ents = {
        (ent.text.strip(), ent.label_)
        for ent in doc.ents
        if ent.label_ in {"PERSON", "ORG", "GPE", "LOC"}
    }
    # 2. transformer 기반 NER
    raw_ner_result = ner_model(text)
    processed_ner_result = postprocess_ner(raw_ner_result, text)
    bert_ents = {
        (ent["word"].strip(), ent["entity"])
        for ent in processed_ner_result
    }
    # 3. 교집합 추출
    intersection = spacy_ents & bert_ents
    if len(intersection) <=3:
        result = [{"word": word, "entity": label} for word, label in spacy_ents]
    else:
    # 4. 결과 포맷
        result = [{"word": word, "entity": label} for word, label in intersection]
    return result


def process_summary(subtitles, video_id: str, language: str, max_input_len=1024, max_summary_len=130):
    text = " ".join([sub[2] for sub in subtitles])

    bart_summary = call_summary_server(text)    
    print('🪀 bart_summary: ', bart_summary)

    bart_scores = {
        "bertscore": compute_bertscore(bart_summary, text),
        "rouge": compute_rouge(bart_summary, text),
        "bleu": compute_bleu(bart_summary, text)
    }
    
    return {
        "final_summary": bart_summary,
        "model_used": 'bart',
        "scores": bart_scores,
    }
