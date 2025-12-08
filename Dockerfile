FROM python:3.12-slim

WORKDIR /app

COPY app/requirements.txt .
RUN pip install --no-cache-dir --timeout 1000 --retries 5 -r requirements.txt

COPY app/dashboard.py .

CMD ["python", "dashboard.py"]