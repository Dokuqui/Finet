FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY pyproject.toml .
COPY app ./app

RUN mkdir -p /app/app/db

EXPOSE 8550

CMD ["python", "-m", "app.main"]