FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml README.md ./
COPY app ./app
COPY streamlit_app ./streamlit_app
COPY experiments ./experiments
COPY scripts ./scripts
COPY data ./data
COPY notebooks ./notebooks

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

ENV PYTHONPATH=/app
ENV MLFLOW_TRACKING_URI=file:/app/mlruns

EXPOSE 8000 8501 5000
