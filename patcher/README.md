# Patcher

Patches smali files to make apps do something slightly different :)

## How to use

1. build the image `docker build -t apk-patcher .`
2. use it `docker run -v $(pwd)/input:/input/ -v /tmp/output_apk:/output/ apk-patcher /input/app.apk /output/app.apk`
