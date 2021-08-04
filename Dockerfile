FROM ubuntu
RUN apt-get update && apt-get install -y default-jdk

WORKDIR /app

COPY . /app/
RUN ./gradlew fatJar

ENTRYPOINT ["java", "-jar", "/app/build/libs/apkdownloader-1.0-SNAPSHOT-all.jar"]

# FROM openjdk:11 AS java_builder
# WORKDIR /app
# COPY . /app
# RUN ./gradlew fatJar

# FROM ubuntu
# RUN apt-get update; apt-get install -y default-jre
# WORKDIR /app
# COPY --from=java_builder /app/build/libs/apkdownloader-1.0-SNAPSHOT-all.jar /app/apkdownloader.jar
# ENTRYPOINT ["java", "jar", "apkdownloader.jar"]


