
FROM python:3.11

ENV PYTHONUNBUFFERED=1

RUN mkdir /bot

WORKDIR /bot

COPY requirements_bot.txt .

RUN pip install --no-cache-dir -r requirements_bot.txt

COPY bot/ bot/