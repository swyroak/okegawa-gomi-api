FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY okegawa_gomi_api.py .
EXPOSE 8000
CMD uvicorn okegawa_gomi_api:app --host 0.0.0.0 --port ${PORT:-8000}
