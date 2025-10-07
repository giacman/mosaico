FROM python:3.12
LABEL authors="Niccolò Guiducci"

WORKDIR /ai_core

COPY Pipfile* ./

RUN pip install --no-cache-dir pipenv && \
    pipenv install --system --deploy --clear

COPY config ./config
COPY models ./models
COPY utils ./utils
COPY server.py ./