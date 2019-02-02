FROM python:3.7-alpine3.8

WORKDIR /app
COPY . /app

ENTRYPOINT ["python",  "resolvable.py"]
