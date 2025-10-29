FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --root-user-action=ignore -r requirements.txt

COPY app ./app
COPY pyproject.toml .

ENV FLET_VIEW=web

EXPOSE 8550

CMD ["python", "-m", "app.main"]