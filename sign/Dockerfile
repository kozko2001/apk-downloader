FROM ubuntu:20.04
ENV DEBIAN_FRONTEND=noninteractive 

RUN apt-get update && apt-get install -y default-jdk

WORKDIR /app

COPY . /app/

ENTRYPOINT ["java", "-jar", "uber-apk-signer.jar", "--allowResign", "--overwrite", "-a" ]