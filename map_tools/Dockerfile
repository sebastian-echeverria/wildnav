FROM python:3.10

# Trusted host configs used to avoid issues when running behind SSL proxies.
RUN pip config set global.trusted-host "pypi.org pypi.python.org files.pythonhosted.org"

# Install required opencv dependencies.
RUN apt-get update
RUN apt-get install -y libgl1 libpq-dev gdal-bin libgdal-dev

# Set up certificates for any proxies that can get in the middle of curl/wget commands during the build
# NOTE: put any CA certificates needed for a proxy in the ./certs folder in the root of this repo, in PEM format
# but with a .crt extensions, so they can be loaded into the container and used for SSL connections properly.
RUN apt-get install -y ca-certificates
RUN mkdir /certs
COPY ./certs/*.crt /certs/
RUN if [ -n "$(ls -A /certs/*.crt)" ]; then \
      cp -rf /certs/*.crt /usr/local/share/ca-certificates/; \
      update-ca-certificates; \
    fi

# Dependencies.
WORKDIR /app
COPY requirements.txt /app/
RUN pip --default-timeout=1000 install -r requirements.txt
RUN pip --default-timeout=1000 install gdal=="`gdal-config --version`.*"

# Code.
COPY ./ /app/

ENTRYPOINT ["python", "-m"]
