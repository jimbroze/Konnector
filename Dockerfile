FROM tiangolo/meinheld-gunicorn-flask:python3.9 as base

ENV PYTHONFAULTHANDLER=1 \
  PYTHONHASHSEED=random \
  PYTHONUNBUFFERED=1 \
  PIP_DEFAULT_TIMEOUT=100

RUN curl -sSL https://install.python-poetry.org | python3 -
# ENV PATH="${PATH}:/root/.poetry/bin"
ENV PATH="${PATH}:/root/.local/bin"

# WORKDIR /app

COPY ./poetry.lock ./pyproject.toml /
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi
# RUN mv main.py helloworld.py
COPY . .
# CMD ["./docker-entrypoint.sh"]