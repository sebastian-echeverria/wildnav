FROM python:3.10

# Trusted host configs used to avoid issues when running behind SSL proxies.
RUN pip config set global.trusted-host "pypi.org pypi.python.org files.pythonhosted.org"

# Install required opencv dependencies.
RUN apt-get update && apt-get install -y libgl1 libpq-dev gdal-bin libgdal-dev

# Dependencies.
WORKDIR /app
COPY requirements.txt /app/
RUN pip --default-timeout=1000 install -r requirements.txt
RUN pip --default-timeout=1000 install gdal=="`gdal-config --version`.*"

# Code.
COPY src/* /app/
COPY src/superglue_lib/ /app/superglue_lib/

#ENTRYPOINT ["bash"]
ENTRYPOINT ["python3"]
