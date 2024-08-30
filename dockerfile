FROM python:3.11

WORKDIR /code

COPY req.txt req.txt

RUN rm -rf /etc/localtime
RUN ln -s /usr/share/zoneinfo/Europe/Moscow /etc/localtime
RUN echo "Europe/Moscow" > /etc/timezone

RUN pip install --no-cache-dir -r req.txt

EXPOSE 8000

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-config=log_config.yml", "--ssl-keyfile=bot.vtorbox.ru_2024-08-08-11-33_05.key", "--ssl-certfile=bot.vtorbox.ru_2024-08-08-11-33_05.crt"]
