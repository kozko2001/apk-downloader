FROM ubuntu:20.04
ENV DEBIAN_FRONTEND=noninteractive 

RUN apt-get update && apt-get install -y default-jdk python3.9 python3-pip
RUN pip install pipenv

WORKDIR /app

COPY . /app/

RUN pipenv install
ENTRYPOINT ["pipenv", "run", "python", "patcher.py"]