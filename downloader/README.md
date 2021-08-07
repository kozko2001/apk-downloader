## Apk Download

Utility to download apks from play store.

## How to use

1. You need to get the aas_token, to get, you should use this project https://github.com/whyorean/Authenticator
2. execute `./gradlew $MAIL $AAS_TOKEN $PACKAGE_NAME`
3. your apks should be now in the `output` library

## Docker way

1. build the image `docker build -t apk-downloader .`
2. use it `docker run -v $(pwd)/output:/output/ apk-downloader $MAIL $AAS_TOKEN $PACKAGE_NAME /output/app.apk`
