FROM python:3.13-slim-bookworm

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV BUILD_ENV=production

WORKDIR /code

# Install the packages needed to build Yara
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y \
  automake libtool make gcc pkg-config libmagic1 wget \
  && addgroup --system mandolin \
  && adduser --system --ingroup mandolin mandolin

COPY --chown=mandolin:mandolin ./requirements.txt /code/requirements.txt

# Install Python packages and purge unecessary packages
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt \
  && rm -rf /root/.cache/pip \
  && apt-get purge -y automake libtool make gcc pkg-config \
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

# Copy Mandolin code
COPY --chown=mandolin:mandolin ./app /code/app
COPY --chown=mandolin:mandolin ./mandolin /code/mandolin
RUN chown mandolin:mandolin /code

USER mandolin
EXPOSE 8000/tcp
CMD ["fastapi", "run", "app/main.py", "--port", "8000", "--workers", "4", "--proxy-headers"]
