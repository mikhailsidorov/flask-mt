FROM alpine

RUN mkdir -p /data/app
WORKDIR /data/app
COPY requirements.txt /data/app/

RUN apk update \
    && apk upgrade \
    && apk add --update python3 python3-dev postgresql-client postgresql-dev build-base gettext \
    && pip3 install --upgrade pip \
    && pip3 install -r requirements.txt \
    && apk del -r python3-dev postgresql

COPY . /data/app/