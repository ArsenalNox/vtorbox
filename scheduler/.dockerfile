
FROM python:3.11

ENV PYTHONUNBUFFERED=1

RUN mkdir /scheduler

WORKDIR /scheduler

COPY req_scheduler.txt .

RUN pip install --no-cache-dir -r req_scheduler.txt

COPY scheduler/ scheduler/