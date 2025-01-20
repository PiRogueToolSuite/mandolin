FROM python:3.13-slim-bookworm

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV BUILD_ENV=production

WORKDIR /code

# Install the packages needed to build Yara
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y \
  automake libtool make gcc pkg-config libmagic1

RUN addgroup --system mandolin \
    && adduser --system --ingroup mandolin mandolin

# Copy Mandolin code
COPY --chown=mandolin:mandolin ./requirements.txt /code/requirements.txt
COPY --chown=mandolin:mandolin ./app /code/app
COPY --chown=mandolin:mandolin ./mandolin /code/mandolin

# Install Python packages
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Purge unecessary packages
RUN apt-get purge -y automake libtool make gcc pkg-config
RUN apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false
RUN rm -rf /var/lib/apt/lists/*

RUN chown mandolin:mandolin /code

USER mandolin
EXPOSE 8000/tcp
CMD ["fastapi", "run", "app/main.py", "--port", "8000", "--workers", "4"]
