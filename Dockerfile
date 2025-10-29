FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --root-user-action=ignore -r requirements.txt

COPY pyproject.toml .
COPY app ./app

RUN mkdir -p /app/app/db

ENV FLET_VIEW=web

EXPOSE 8550

CMD ["python", "-m", "app.main"]
