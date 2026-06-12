# RAG Playground

A learning project for building a Retrieval-Augmented Generation (RAG) pipeline Ollama

---


## Requirement

For Windows machine:

- **WSL2** with Ubuntu
- **Docker Desktop** with WSL2 integration enabled 

## Installation

### Terminal A — Set up Ollama and keep it running

```bash
curl -fsSL https://ollama.com/install.sh | sh

ollama pull qwen3:0.6b
ollama pull nomic-embed-text

ollama serve
```

To verify the models are loaded:
```bash
ollama run qwen3:0.6b
```

### Terminal B — Clone and set up the project

```bash
git clone 
cd rag-playground

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```


---

## Running the Project

### Option 1 — Run locally

```bash
source .venv/bin/activate 
python3 main.py
```

### Option 2 — Run inside Docker

```bash
docker compose up --build
```

---

## Development Loop

```
1. Edit your .py files locally
         ↓
2. Test quickly with local Python
   python3 main.py
         ↓
3. When it works, run in Docker
   docker compose up --build
```