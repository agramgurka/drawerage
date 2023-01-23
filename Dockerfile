FROM python:3.11.2-alpine3.17
ENV PYTHONUNBUFFERED 1
WORKDIR /usr/src/drawesome
COPY requirements.txt .
RUN apk add --update --no-cache libpq zlib-dev libjpeg
RUN apk add --update --no-cache --virtual .tmp-build-deps \
    gcc libc-dev linux-headers postgresql-dev musl-dev libffi-dev
RUN python3 -m pip install -r requirements.txt
RUN apk del .tmp-build-deps
COPY application ./application
COPY Drawesome ./Drawesome
COPY manage.py .
EXPOSE 8000