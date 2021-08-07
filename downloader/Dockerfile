FROM ubuntu:20.04
ENV DEBIAN_FRONTEND=noninteractive 

RUN apt-get update && apt-get install -y default-jdk python3.9 python3-pip
RUN pip install pipenv

WORKDIR /app

COPY . /app/
RUN ./gradlew fatJar; mkdir output

ENV PIPENV_PIPFILE=/app/python/Pipfile

RUN pipenv install
ENTRYPOINT ["pipenv", "run", "python", "python/entrypoint.py"]