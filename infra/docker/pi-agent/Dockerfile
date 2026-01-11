# Pi Agent Dockerfile (placeholder)
FROM python:3.11-slim
WORKDIR /agent
COPY ../../pi-agent/requirements.txt /agent/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY ../../pi-agent /agent
CMD ["python", "src/main.py"]
