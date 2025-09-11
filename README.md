# FastAPI Backend (Single File)

## Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run
```bash
uvicorn main:app --reload --port 8000
```

- Health: http://127.0.0.1:8000/health
- Ping: http://127.0.0.1:8000/ping
