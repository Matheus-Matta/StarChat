####################################
# STAGE: builder
####################################
FROM python:3.11.4-slim-bullseye AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /usr/src/app

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      gcc \
      libpq-dev \
      libsqlite3-dev \
      python3-dev \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip wheel \
 && pip wheel --no-cache-dir --wheel-dir /usr/src/app/wheels -r requirements.txt

####################################
# STAGE: web (final)
####################################
FROM python:3.11.4-slim-bullseye AS web

RUN addgroup --system app && adduser --system --ingroup app app

RUN mkdir -p /home/app/web/staticfiles /home/app/web/media

ENV HOME=/home/app
ENV APP_HOME=/home/app/web
WORKDIR $APP_HOME

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      postgresql-client \
      sqlite3 \
      libsqlite3-dev \
 && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/src/app/wheels /wheels
COPY --from=builder /usr/src/app/requirements.txt .
RUN pip install --upgrade pip \
 && pip install --no-cache /wheels/*

# Copia TODO o projeto de uma vez (inclui entrypoint.sh)
COPY . .

# **Agora** remove CRLF e marca como executável (depois do COPY . .)
RUN sed -i 's/\r$//' /home/app/web/entrypoint.sh \
 && chmod +x /home/app/web/entrypoint.sh

RUN chown -R app:app $APP_HOME
USER app

# Use /bin/sh (não /bin/bash)
ENTRYPOINT ["/bin/sh", "/home/app/web/entrypoint.sh"]
