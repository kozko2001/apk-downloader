## F-Droid repository

### How to use

1. build the docker image `docker build -t repo .`
2. Initialize the repository `docker run -v $(pwd)/repo:/fdroid repo init`
3. Modify the `config.yml` (see https://gitlab.com/fdroid/fdroidserver/blob/2.0.3/examples/config.yml)

- I would add a `local_copy_dir: /public/fdroid`

4. Add your apks in `$(pwd)/repo/repo`
5. Update the metadata `docker run -v $(pwd)/repo:/fdroid repo update -c`
6. Deploy `docker run -v $(pwd)/repo:/fdroid -v $(pwd)/public:/public repo deploy -v`

Congrats, now you have your repository in `public` ready to be served by a simple nginx :)
