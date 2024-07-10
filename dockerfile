FROM python:3.11

WORKDIR /code

COPY req.txt req.txt

RUN pip install --no-cache-dir -r req.txt

EXPOSE 8000

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-config=log_config.yml"]