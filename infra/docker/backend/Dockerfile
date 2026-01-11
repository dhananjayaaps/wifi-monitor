# Backend Dockerfile (placeholder)
FROM python:3.11-slim
WORKDIR /app
COPY ../../backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY ../../backend /app
CMD ["gunicorn", "app.wsgi:app", "-b", "0.0.0.0:5000"]
