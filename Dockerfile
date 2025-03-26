ARG PYTHON_VERSION=3.12.0
FROM python:${PYTHON_VERSION} AS base

ENV DOCKERIZED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/usr/lib/libreoffice/program

RUN apt-get update  \
    && apt-get install -y libreoffice python3-uno supervisor unoconv net-tools && rm -rf /var/lib/apt/lists/*

ENV UNO_PATH="/usr/lib/libreoffice/program"
ENV PYTHONPATH="/usr/lib/python3/dist-packages"

RUN useradd -ms /bin/bash admin
WORKDIR /usr/src/service
RUN mkdir -p uploads converted && chown -R admin:admin /usr/src/service

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code into the container.
COPY . .
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

RUN chmod +x /usr/bin/unoconv

# Expose the port that the application listens on.
EXPOSE 8080 2002

# Run the application.
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]