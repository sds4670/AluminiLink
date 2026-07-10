FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# CPU-only torch wheel (~200MB) instead of the default CUDA build (~750MB+) —
# this backend has no GPU, and the smaller download is far less prone to
# timing out on constrained network connections.
RUN pip install --no-cache-dir --prefer-binary --timeout 180 --retries 10 \
    torch==2.1.0 --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir --prefer-binary --timeout 180 --retries 10 \
    -r requirements.txt

COPY . .

# Train the Module 6 predictive models at build time so the image ships with
# them ready to go. Best-effort: never fail the build over this (e.g. if the
# training data shape ever changes) — app.services.ml.predict will just 404
# clearly at request time instead of silently degrading like the moderation
# fallback does.
RUN python -m app.scripts.train_models 2>/dev/null || true

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
