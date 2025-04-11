from celery import Celery
from keybert import KeyBERT
from transformers import pipeline
from transformers import BartForConditionalGeneration, BartTokenizer
from transformers import PegasusForConditionalGeneration, PegasusTokenizer

from db import save_summary

import torch
import re
import spacy
import evaluate


# Celery 인스턴스 생성
celery = Celery(
    "worker",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0"
)


# NER
nlp = spacy.load("en_core_web_sm")
ner_model = pipeline("ner", model="dslim/bert-base-NER")
# Summary-BART
bart_model = BartForConditionalGeneration.from_pretrained("facebook/bart-large-cnn")
bart_tokenizer = BartTokenizer.from_pretrained("facebook/bart-large-cnn")
# Summary-Pegasus
model_name = "google/pegasus-cnn_dailymail"
device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
pegasus_model = PegasusForConditionalGeneration.from_pretrained(
    model_name
).to(device)
pegasus_tokenizer = PegasusTokenizer.from_pretrained(model_name)


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
        # 1. 연속된 같은 라벨끼리 병합 (예: "John", "Quincy", "Adams" → "John Quincy Adams")
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
    bertscore_metric = evaluate.load("bertscore")
    score = bertscore_metric.compute(
        predictions=[prediction],
        references=[reference],
        model_type="bert-base-uncased"
    )
    return score["f1"][0]

def compute_rouge(prediction, reference):
    rouge_metric = evaluate.load("rouge")
    score = rouge_metric.compute(
        predictions=[prediction],
        references=[reference]
    )
    return score["rougeL"]

def compute_bleu(prediction, reference):
    bleu_metric = evaluate.load("bleu")
    score = bleu_metric.compute(
        predictions=[prediction.split()],
        references=[[reference.split()]]
    )
    return score["bleu"]


@celery.task(name="app.worker.extract_keywords")
def extract_keywords(text):
    # Keyword
    kw_model = KeyBERT(model="sentence-transformers/all-MiniLM-L6-v2")
    return kw_model.extract_keywords(text, keyphrase_ngram_range=(1, 2), stop_words="english")

@celery.task(name="app.worker.process_ner")
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
    # 4. 결과 포맷
    result = [{"word": word, "entity": label} for word, label in intersection]
    return result

@celery.task(name="app.worker.process_summary")
def process_summary(subtitles, max_input_len=1024, max_summary_len=130):
    # 자막을 하나의 텍스트로 결합
    text = " ".join([sub[2] for sub in subtitles])

    bart_tokens = bart_tokenizer.encode(text, return_tensors="pt", truncation=True, max_length=1024)
    bart_summary_ids = bart_model.generate(bart_tokens, max_length=150, min_length=30, num_beams=5)
    bart_summary = bart_tokenizer.decode(bart_summary_ids[0], skip_special_tokens=True)

    pegasus_tokens = pegasus_tokenizer.encode(text, return_tensors="pt", truncation=True, max_length=max_input_len)
    pegasus_summary_ids = pegasus_model.generate(
        pegasus_tokens,
        max_length=max_summary_len,
        min_length=40,
        num_beams=6,
        length_penalty=1.4,
        early_stopping=True
    )
    pegasus_summary = clean_summary(pegasus_tokenizer.decode(pegasus_summary_ids[0], skip_special_tokens=True))

    bart_scores = {
        "bertscore": compute_bertscore(bart_summary, text),
        "rouge": compute_rouge(bart_summary, text),
        "bleu": compute_bleu(bart_summary, text)
    }

    pegasus_scores = {
        "bertscore": compute_bertscore(pegasus_summary, text),
        "rouge": compute_rouge(pegasus_summary, text),
        "bleu": compute_bleu(pegasus_summary, text)
    }

    print('bart: ', bart_summary)
    print('pegasus: ', pegasus_summary)
    print('b, p scores: ', bart_scores, ', ', pegasus_scores)

    # 우선 기준은 BERTScore로 선택 (다른 기준으로 바꿀 수 있음)
    if bart_scores["bertscore"] >= pegasus_scores["bertscore"]:
        final_summary = bart_summary
        model_used = "BART"
        final_scores = bart_scores
    else:
        final_summary = pegasus_summary
        model_used = "Pegasus"
        final_scores = pegasus_scores

    save_summary(video_id, language, model_used, final_summary)

    return {
        "final_summary": final_summary,
        "model_used": model_used,
        "scores": final_scores,
        "segment_summaries": []
    }
