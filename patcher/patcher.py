import click
import tempfile
import subprocess
import xml.etree.ElementTree
from pathlib import Path

APK_TOOL_BASE = ["java", "-jar", "apktool_2.5.0.jar"]


def decompile(apk, workfolder):
    subprocess.run(APK_TOOL_BASE + ["d", "-f", "-o", workfolder, apk], check=True)


def rebuild(workfolder, output):
    subprocess.run(APK_TOOL_BASE + ["b", "-o", output, workfolder], check=True)


def get_pkg_name(workfolder):
    workfolder = Path(workfolder)
    AndroidManifestPath = workfolder / "AndroidManifest.xml"

    # Load AndroidManifest.xml
    tree = xml.etree.ElementTree.parse(AndroidManifestPath)

    manifest = tree.getroot()
    pkg = manifest.attrib["package"]

    return pkg


def patch_twitter(workfolder):
    patch = Path(__file__).parent / "patches" / "twitter_patch.smali"
    with patch.open(mode="r") as f:
        new_function = f.readlines()
    print(new_function)

    workfolder = Path(workfolder)
    files = list(workfolder.rglob("**/JsonTimelineEntry$$JsonObjectMapper.smali"))

    if len(files) != 1:
        raise Exception(f"issue finding file to patch {files}")

    file_to_patch = files[0]

    with file_to_patch.open(mode="r") as f:
        lines = f.readlines()

    start = [
        idx
        for idx, line in enumerate(lines)
        if ".method public parse(Lcom/fasterxml/jackson/core/g;)Lcom/twitter/model/json/timeline/urt/JsonTimelineEntry"
        in line
    ]

    if len(start) != 1:
        raise Exception(f"issue finding function patch")
    else:
        start = start[0]

    end = [
        idx for idx, line in enumerate(lines) if ".end method" in line and idx > start
    ][0]

    ## Removing function
    lines = [line for idx, line in enumerate(lines) if idx < start or idx > end]
    lines = lines + new_function
    lines = "\n".join(lines)

    with file_to_patch.open(mode="w") as f:
        f.write(lines)


    ## Patch resource (if not... the profile screen crashes...)
    # I think it's related to the fact we are not downloading the apk for my exact phone)
    f = workfolder / "res" / "layout" / "scrolling_header_activity.xml"
    with f.open() as f:
        data = f.read()
    data = data.replace("@dimen/pull_to_refresh_drawable_width", "0dp")
    with f.open(mode="w") as f:
        f.write(lines)

@click.command()
@click.argument("input", type=click.Path(exists=True))
@click.argument("output", type=click.Path(exists=False, dir_okay=False))
def patch(input, output):
    with tempfile.TemporaryDirectory() as tmpdirname:
        # tmpdirname = "/tmp/workfolder"
        print(f"temp dir is {tmpdirname}")
        decompile(input, tmpdirname)
        package = get_pkg_name(tmpdirname)

        if package == "com.twitter.android":
            patch_twitter(tmpdirname)

        rebuild(tmpdirname, output)


if __name__ == "__main__":
    patch()
