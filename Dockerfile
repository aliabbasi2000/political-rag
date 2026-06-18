FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y git git-lfs && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN git lfs install

RUN mkdir -p models && git clone https://huggingface.co/Qwen/Qwen3-Embedding-0.6B models/Qwen3-Embedding-0.6B

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
