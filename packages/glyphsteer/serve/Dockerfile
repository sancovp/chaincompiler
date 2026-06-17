# glyphsteer-serve — ONNX embedding sidecar (no torch)
FROM python:3.11-slim

WORKDIR /app

# fastembed uses onnxruntime; no build toolchain needed for the slim wheels
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# Default model; override at build or run with --build-arg / -e GLYPHSTEER_MODEL=...
ARG GLYPHSTEER_MODEL=BAAI/bge-small-en-v1.5
ENV GLYPHSTEER_MODEL=${GLYPHSTEER_MODEL}

# Pre-fetch the model weights at build time → fast first request, works offline.
RUN python -c "from fastembed import TextEmbedding; import os; \
    TextEmbedding(os.environ['GLYPHSTEER_MODEL']); print('cached', os.environ['GLYPHSTEER_MODEL'])"

EXPOSE 8088
HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8088/health').status==200 else 1)"

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8088"]
