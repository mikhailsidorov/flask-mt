FROM python:3.6-alpine

RUN adduser -D microblog

WORKDIR /home/microblog

COPY requirements.txt requirements.txt

RUN apk update \
    && apk add postgresql-dev gcc python3-dev musl-dev \
    && python -m venv venv \
    && pip install -r requirements.txt \
    && apk del gcc python3-dev postgresql-dev 

COPY ./ ./
RUN chmod +x boot.sh \
    && chown -R microblog:microblog ./

ENV FLASK_APP microblog.py 

USER microblog

EXPOSE 5000
ENTRYPOINT ["./boot.sh"]