FROM python:3.9

RUN mkdir -p /app
WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt
EXPOSE 8080

USER 1000
ENTRYPOINT python3 api.py
