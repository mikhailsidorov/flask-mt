FROM python:3.7

RUN mkdir -p /data/app
WORKDIR /data/app
COPY pyproject.toml /data/app/pyproject.toml

RUN apt update
RUN apt upgrade 
RUN apt install -y vim postgresql-client gettext
RUN pip3 install --upgrade pip
RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | python3 -
ENV PATH="/root/.local/bin:$PATH"
RUN poetry config virtualenvs.create false
RUN poetry install

COPY . /data/app/
