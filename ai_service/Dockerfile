FROM python:3.10-slim

WORKDIR /app

# 1. התקנת גרסת CPU של PyTorch בנפרד (מונע הורדה של דרייברים ענקיים של NVIDIA)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# 2. העתקת שאר התלויות והתקנתן
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. העתקת הקוד
COPY . ./ai_service

# 4. הגדרות סביבה והרצה
ENV PYTHONPATH=/app
EXPOSE 8002

CMD ["uvicorn", "ai_service.main:app", "--host", "0.0.0.0", "--port", "8002"]