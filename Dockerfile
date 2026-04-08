FROM python:3.13-slim-bookworm

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV BUILD_ENV=production

WORKDIR /code

# Install the packages needed to build Yara
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uv/bin/uv
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y \
  automake libtool make gcc pkg-config libmagic1 wget \
  && addgroup --system mandolin \
  && adduser --system --ingroup mandolin mandolin

COPY --chown=mandolin:mandolin ./pyproject.toml /code/pyproject.toml
COPY --chown=mandolin:mandolin ./uv.lock /code/uv.lock

# Install Python packages and purge unecessary packages
RUN /uv/bin/uv sync --frozen --no-dev --no-editable \
  && apt-get purge -y automake libtool make gcc pkg-config \
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

# Copy Mandolin code
COPY --chown=mandolin:mandolin ./app /code/app
COPY --chown=mandolin:mandolin ./mandolin /code/mandolin
RUN chown mandolin:mandolin /code

USER mandolin
EXPOSE 8000/tcp
CMD ["/code/.venv/bin/fastapi", "run", "app/main.py", "--port", "8000", "--workers", "4", "--proxy-headers"]
