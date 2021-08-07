FROM ubuntu:20.04

## ANDROID_SDK_TOOLS_VERSION from https://developer.android.com/studio
ENV ANDROID_HOME="/opt/android-sdk" \
    ANDROID_SDK_TOOLS_VERSION="7583922" \ 
    ANDROID_SDK_HOME="/opt/android-sdk"

RUN apt-get update && apt-get install -y wget unzip openjdk-11-jdk

## Copied from https://github.com/mingchen/docker-android-build-box

# Install Android SDK
RUN echo "sdk tools ${ANDROID_SDK_TOOLS_VERSION}" && \
    wget --quiet --output-document=sdk-tools.zip \
    "https://dl.google.com/android/repository/commandlinetools-linux-${ANDROID_SDK_TOOLS_VERSION}_latest.zip" && \
    mkdir --parents "$ANDROID_HOME" && \
    unzip -q sdk-tools.zip -d "$ANDROID_HOME" && \
    rm --force sdk-tools.zip

# Install SDKs
# Please keep these in descending order!
# The `yes` is for accepting all non-standard tool licenses.

RUN mkdir --parents "$HOME/.android/" && \
    echo '### User Sources for Android SDK Manager' > \
    "$HOME/.android/repositories.cfg" && \
    yes | $ANDROID_HOME/cmdline-tools/bin/sdkmanager --licenses --sdk_root=${ANDROID_SDK_HOME}/> /dev/null

RUN echo "platforms" && \
    yes | "$ANDROID_HOME"/cmdline-tools/bin/sdkmanager --sdk_root=${ANDROID_SDK_HOME}/ \
    "platforms;android-30"

RUN echo "platforms" && \
    yes | "$ANDROID_HOME"/cmdline-tools/bin/sdkmanager --sdk_root=${ANDROID_SDK_HOME}/ \
    "platforms;android-30"

RUN echo "build tools 30" && \
    yes | "$ANDROID_HOME"/cmdline-tools/bin/sdkmanager --sdk_root=${ANDROID_SDK_HOME}/ \
    "build-tools;30.0.0"

## installing fdroidserver
ENV DEBIAN_FRONTEND=noninteractive 
RUN apt-get install -y python3.9 python3-pip git rsync
RUN pip install pipenv


WORKDIR /app
COPY Pipfile Pipfile.lock /app/

RUN pipenv install

WORKDIR /fdroid
ENV PIPENV_PIPFILE=/app/Pipfile

ENTRYPOINT [ "pipenv", "run", "fdroid" ]