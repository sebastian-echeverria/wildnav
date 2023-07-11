FROM python:3.10

# Trusted host configs used to avoid issues when running behind SSL proxies.
RUN pip config set global.trusted-host "pypi.org pypi.python.org files.pythonhosted.org"

# Install required opencv dependencies.
RUN apt-get update
RUN apt-get install -y libgl1 

# Dependencies.
WORKDIR /app
COPY requirements.txt /app/
RUN pip install -r requirements.txt

# Code.
COPY src/* /app/
COPY src/superglue_lib/ /app/superglue_lib/

ENTRYPOINT ["python3", "wildnav.py"]
#ENTRYPOINT ["bash"]
