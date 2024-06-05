
FROM python:3.11

ENV PYTHONUNBUFFERED=1

RUN mkdir /scheduler

WORKDIR /scheduler

COPY req_scheduler.txt .

RUN rm -rf /etc/localtime
RUN ln -s /usr/share/zoneinfo/Europe/Moscow /etc/localtime
RUN echo "Europe/Moscow" > /etc/timezone

RUN pip install --no-cache-dir -r req_scheduler.txt

COPY scheduler/ scheduler/