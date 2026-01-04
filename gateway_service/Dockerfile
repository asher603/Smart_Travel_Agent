FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

# Install dependencies (fastapi, uvicorn, httpx, python-dotenv)
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# --- FIX: Ensure this says 8000, NOT 8001 ---
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]