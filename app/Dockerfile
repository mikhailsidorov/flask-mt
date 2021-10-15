FROM alpine:3.14.2

RUN mkdir -p /data/app
WORKDIR /data/app
COPY requirements /data/app/requirements

RUN apk update
RUN apk upgrade
RUN apk add --update python3 python3-dev py3-pip postgresql-client postgresql-dev build-base gettext
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements/prod.txt
# && apk del -r python3-dev postgresql

COPY . /data/app/
