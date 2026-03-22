# Dockerfile for full reproducibility
FROM python:3.11-slim

WORKDIR /app

COPY backend/ ./backend/
COPY reproduce_all.sh ./

RUN pip install --upgrade pip && \
    pip install -r backend/requirements.txt

CMD ["bash", "./reproduce_all.sh"]
