FROM python:3.12-slim

WORKDIR /app

# CPU-only PyTorch (veel kleiner dan de standaard CUDA-versie)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY rag.py server.py index.html ./

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]