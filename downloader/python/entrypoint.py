import click
import subprocess
import tempfile

def run_downloader(mail, aastoken, packagename):
    print("[*] Downloading apks from playstore")
    CMD = ["java", "-jar", "build/libs/apkdownloader-1.0-SNAPSHOT-all.jar", mail, aastoken, packagename]
    subprocess.run(CMD, check=True)

def run_merger(packagename, dest):
    print("[*] merging split apks")
    CMD = ["python3", "merge_apk.py", "--debug-output", packagename, "../output/", dest]
    subprocess.run(CMD, cwd="python/", check=True)

@click.command()
@click.argument('mail')
@click.argument('aastoken')
@click.argument('packagename')
@click.argument('dest')
def download(mail, aastoken, packagename, dest):
    run_downloader(mail, aastoken, packagename)

    run_merger(packagename, dest)

if __name__ == '__main__':
    download()