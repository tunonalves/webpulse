FROM mcr.microsoft.com/playwright/python:v1.61.0-noble
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY worker.py .
CMD ["python", "-u", "worker.py"]
