# AgriSight (v3 in progress)

## Overview

AgriSight is an AI-powered smart agriculture system under development.

* Currently, an EfficientNet-B0 model fine-tuned on the Kaggle new-plant-diseases-dataset is used to detect infected areas on crops.

* Using Hugging Face’s Agriculture-Plant-Diseases-QA-Pairs-Dataset (by YuvrajSingh9886), FAISS is applied to extract vector embeddings.
These vectors are integrated into an Ollama-based Mistral chatbot with RAG functionality to provide relevant information about plant diseases.