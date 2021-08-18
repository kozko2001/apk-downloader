#!/usr/bin/python3
import argparse
import os
import pkg_resources
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree
from glob import glob
from sys import exit

####################
# Main()
####################

APK_TOOL = [
    "java",
    "-jar",
    "apktool-cli-all.jar",
]


def main():
    # Check that dependencies are available
    checkDependencies()

    # Grab argz
    args = getArgs()
    pkgname = args.pkgname

    apks = glob(f"{args.input_folder}/*.apk")

    if len(apks) == 0:
        raise Exception(f"No apk found in {args.input_folder}")
    elif len(apks) == 1:
        shutil.copy(apks[0], args.save_apk)
        exit(0)
    else:
        base = [apk for apk in apks if pkgname in apk]
        if len(base) != 1:
            raise Exception(f"found {len(base)} base apks... it should be just one")
        else:
            baseapk = base[0]
            apks.remove(baseapk)

    # Create a temp directory to work from
    with tempfile.TemporaryDirectory() as tmppath:
        # Get the APK to patch. Combine app bundles/split APKs into a single APK.
        apkfile = combineSplitAPKs(
            pkgname, baseapk, apks, tmppath, args.disable_styles_hack, args.save_apk
        )

        # Patch the target APK with objection
        # print("Patching " + apkfile.split(os.sep)[-1] + " with objection.")
        # ret = None
        # if getObjectionVersion() >= pkg_resources.parse_version("1.9.3"):
        # 	ret = subprocess.run(["objection", "patchapk", "--skip-resources", "--ignore-nativelibs", "-s", apkfile], stdout=getStdout())
        # else:
        # 	ret = subprocess.run(["objection", "patchapk", "--skip-resources", "-s", apkfile], stdout=getStdout())
        # if ret.returncode != 0:
        # 	print("Error: Failed to run 'objection patchapk --skip-resources -s " + apkfile + "'.\nRun with --debug-output for more information.")
        # 	sys.exit(1)
        # os.remove(apkfile)
        # shutil.move(apkfile[:-4] + ".objection.apk", apkfile)
        # print("")

        # #Enable support for user-installed CA certs (e.g. Burp Suite CA installed on device by user)
        # if args.no_enable_user_certs == False:
        # 	enableUserCerts(apkfile)

        # #Uninstall the original package from the device
        # print("Uninstalling the original package from the device.")
        # ret = subprocess.run(["adb", "uninstall", pkgname], stdout=getStdout())
        # if ret.returncode != 0:
        # 	print("Error: Failed to run 'adb uninstall " + pkgname + "'.\nRun with --debug-output for more information.")
        # 	sys.exit(1)
        # print("")

        # #Install the patched APK
        # print("Installing the patched APK to the device.")
        # ret = subprocess.run(["adb", "install", apkfile], stdout=getStdout())
        # if ret.returncode != 0:
        # 	print("Error: Failed to run 'adb install " + apkfile + "'.\nRun with --debug-output for more information.")
        # 	sys.exit(1)
        # print("")

        # #Done
        # print("Done, cleaning up temporary files.")


####################
# Check that required dependencies are present:
# -> Tools used
# -> Android device connected
# -> Keystore
####################
def checkDependencies():
    deps = ["java"]
    missing = []
    for dep in deps:
        if shutil.which(dep) is None:
            missing.append(dep)
    if len(missing) > 0:
        print(
            "Error, missing dependencies, ensure the following commands are available on the PATH: "
            + (", ".join(missing))
        )
        sys.exit(1)


####################
# Grab command line parameters
####################
def getArgs():
    # Only parse args once
    if not hasattr(getArgs, "parsed_args"):
        # Parse the command line
        parser = argparse.ArgumentParser(
            description="patch-apk - Merge split apks into single one."
        )
        parser.add_argument(
            "--disable-styles-hack",
            help="Disable the styles hack that removes duplicate entries from res/values/styles.xml.",
            action="store_true",
        )
        parser.add_argument(
            "--debug-output", help="Enable debug output.", action="store_true"
        )
        parser.add_argument(
            "pkgname",
            help="The name, or partial name, of the package to patch (e.g. com.foo.bar).",
        )

        parser.add_argument(
            "input_folder",
            help="folder with the apk's to merge",
        )

        parser.add_argument(
            "save_apk",
            help="Save a copy of the APK (or single APK) prior to patching for use with other tools.",
        )

        # Store the parsed args
        getArgs.parsed_args = parser.parse_args()

    # Return the parsed command line args
    return getArgs.parsed_args


####################
# Debug print
####################
def dbgPrint(msg):
    if getArgs().debug_output == True:
        print(msg)


####################
# Get the stdout target for subprocess calls. Set to DEVNULL unless debug output is enabled.
####################
def getStdout():
    if getArgs().debug_output == True:
        return None
    else:
        return subprocess.DEVNULL


####################
# Get apktool version
####################
def getApktoolVersion():
    proc = subprocess.run(APK_TOOL + ["-version"], stdout=subprocess.PIPE)
    return pkg_resources.parse_version(
        proc.stdout.decode("utf-8").strip().split("-")[0].strip()
    )


####################
# Wrapper to run apktool platform-independently, complete with a dirty hack to fix apktool's dirty hack.
####################
def runApkTool(params):
    _args = [] + APK_TOOL
    _args.extend(params)
    return subprocess.run(_args, stdout=getStdout())


####################
# Combine app bundles/split APKs into a single APK for patching.
####################
def combineSplitAPKs(pkgname, baseapk, configapks, tmppath, disableStylesHack, dest):
    print("App bundle/split APK detected, rebuilding as a single APK.")
    print("")

    # Extract the individual APKs
    print("Extracting individual APKs with apktool.")
    baseapkfilename = baseapk
    splitapkpaths = []
    localapks = configapks + [baseapk]
    for apkpath in localapks:
        apkdir = apkpath[:-4]
        print("[+] Extracting: " + apkpath + " to " + apkdir)
        ret = runApkTool(
            [
                "d",
                "-f",
                "-o",
                apkdir,
                apkpath,
            ]
        )
        if ret.returncode != 0:
            print(
                "Error: Failed to run 'apktool d "
                + apkpath
                + " -o "
                + apkdir
                + "'.\nRun with --debug-output for more information."
            )
            sys.exit(1)

        # Record the destination paths of all but the base APK
        if apkpath != baseapk:
            splitapkpaths.append(apkdir)
        else:
            baseapkdir = apkdir

        # Check for ProGuard/AndResGuard - this might b0rk decompile/recompile
        if detectProGuard(apkdir):
            print(
                "\n[~] WARNING: Detected ProGuard/AndResGuard, decompile/recompile may not succeed.\n"
            )
    print("")
    # Walk the extracted APK directories and copy files and directories to the base APK
    copySplitApkFiles(baseapkdir, splitapkpaths)

    # Fix public resource identifiers
    fixPublicResourceIDs(baseapkdir, splitapkpaths)

    # Hack: Delete duplicate style resource entries.
    if disableStylesHack == False:
        hackRemoveDuplicateStyleEntries(baseapkdir)

    # Disable APK splitting in the base AndroidManifest.xml file
    disableApkSplitting(baseapkdir)

    # Rebuild the base APK
    print("Rebuilding as a single APK.")
    if os.path.exists(os.path.join(baseapkdir, "res", "navigation")) == True:
        print(
            "[+] Found res/navigation directory, rebuilding with 'apktool --use-aapt2'."
        )
        ret = runApkTool(["b", "--use-aapt2", "-o", dest, baseapkdir])
        if ret.returncode != 0:
            print(
                "Error: Failed to run 'apktool b "
                + baseapkdir
                + "'.\nRun with --debug-output for more information."
            )
            sys.exit(1)
    elif getApktoolVersion() > pkg_resources.parse_version("2.4.2"):
        print(
            "[+] Found apktool version > 2.4.2, rebuilding with 'apktool --use-aapt2'."
        )
        ret = runApkTool(["b", "--use-aapt2", "-o", dest, baseapkdir])
        if ret.returncode != 0:
            print(
                "Error: Failed to run 'apktool b "
                + baseapkdir
                + "'.\nRun with --debug-output for more information."
            )
            sys.exit(1)
    else:
        print("[+] Building APK with apktool.")
        ret = runApkTool(["b", "-o", dest, baseapkdir])
        if ret.returncode != 0:
            print(
                "Error: Failed to run 'apktool b "
                + baseapkdir
                + "'.\nRun with --debug-output for more information."
            )
            sys.exit(1)

    # # Sign the new APK
    # print("[+] Signing new APK.")
    # ret = subprocess.run(
    #     [
    #         "jarsigner",
    #         "-sigalg",
    #         "SHA1withRSA",
    #         "-digestalg",
    #         "SHA1",
    #         "-keystore",
    #         os.path.realpath(
    #             os.path.join(
    #                 os.path.realpath(__file__), "..", "data", "patch-apk.keystore"
    #             )
    #         ),
    #         "-storepass",
    #         "patch-apk",
    #         os.path.join(baseapkdir, "dist", baseapkfilename),
    #         "patch-apk-key",
    #     ],
    #     stdout=getStdout(),
    # )
    # if ret.returncode != 0:
    #     print(
    #         "Error: Failed to run 'jarsigner -sigalg SHA1withRSA -digestalg SHA1 -keystore "
    #         + os.path.realpath(
    #             os.path.join(
    #                 os.path.realpath(__file__), "..", "data", "patch-apk.keystore"
    #             )
    #         )
    #         + "-storepass patch-apk "
    #         + os.path.join(baseapkdir, "dist", baseapkfilename)
    #         + " patch-apk-key'.\nRun with --debug-output for more information."
    #     )
    #     sys.exit(1)

    # # Zip align the new APK
    # print("[+] Zip aligning new APK.")
    # ret = subprocess.run(
    #     [
    #         "zipalign",
    #         "-f",
    #         "4",
    #         os.path.join(baseapkdir, "dist", baseapkfilename),
    #         os.path.join(baseapkdir, "dist", baseapkfilename[:-4] + "-aligned.apk"),
    #     ],
    #     stdout=getStdout(),
    # )
    # if ret.returncode != 0:
    #     print(
    #         "Error: Failed to run 'zipalign -f 4 "
    #         + os.path.join(baseapkdir, "dist", baseapkfilename)
    #         + " "
    #         + os.path.join(baseapkdir, "dist", baseapkfilename[:-4] + "-aligned.apk")
    #         + "'.\nRun with --debug-output for more information."
    #     )
    #     sys.exit(1)
    # shutil.move(
    #     os.path.join(baseapkdir, "dist", baseapkfilename[:-4] + "-aligned.apk"),
    #     os.path.join(baseapkdir, "dist", baseapkfilename),
    # )
    # print("")

    # Return the new APK path
    return os.path.join(baseapkdir, "dist", baseapkfilename)


####################
# Attempt to detect ProGuard/AndResGuard.
####################
def detectProGuard(extractedPath):
    if (
        os.path.exists(os.path.join(extractedPath, "original", "META-INF", "proguard"))
        == True
    ):
        return True
    if (
        os.path.exists(
            os.path.join(extractedPath, "original", "META-INF", "MANIFEST.MF")
        )
        == True
    ):
        fh = open(os.path.join(extractedPath, "original", "META-INF", "MANIFEST.MF"))
        d = fh.read()
        fh.close()
        if "proguard" in d.lower():
            return True
    return False


####################
# Copy files and directories from split APKs into the base APK directory.
####################
def copySplitApkFiles(baseapkdir, splitapkpaths):
    print("Copying files and directories from split APKs into base APK.")
    for apkdir in splitapkpaths:
        for (root, dirs, files) in os.walk(apkdir):
            print(root, dirs, files)
            # Skip the original files directory
            if root.startswith(os.path.join(apkdir, "original")) == False:
                # Create any missing directories
                for d in dirs:
                    # Translate directory path to base APK path and create the directory if it doesn't exist
                    p = baseapkdir + os.path.join(root, d)[len(apkdir) :]
                    if os.path.exists(p) == False:
                        dbgPrint(
                            "[+] Creating directory in base APK: "
                            + p[len(baseapkdir) :]
                        )
                        os.mkdir(p)

                # Copy files into the base APK
                for f in files:
                    # Skip the AndroidManifest.xml and apktool.yml in the APK root directory
                    if apkdir == root and (
                        f == "AndroidManifest.xml" or f == "apktool.yml"
                    ):
                        continue

                    # Translate path to base APK
                    p = baseapkdir + os.path.join(root, f)[len(apkdir) :]

                    # Copy files into the base APK, except for XML files in the res directory
                    if f.lower().endswith(".xml") and p.startswith(
                        os.path.join(baseapkdir, "res")
                    ):
                        continue
                    dbgPrint("[+] Moving file to base APK: " + p[len(baseapkdir) :])
                    shutil.move(os.path.join(root, f), p)
    print("")


####################
# Fix public resource identifiers that are shared across split APKs.
# Maps all APKTOOL_DUMMY_ resource IDs in the base APK to the proper resource names from the
# split APKs, then updates references in other resource files in the base APK to use proper
# resource names.
####################
def fixPublicResourceIDs(baseapkdir, splitapkpaths):
    # Bail if the base APK does not have a public.xml
    if os.path.exists(os.path.join(baseapkdir, "res", "values", "public.xml")) == False:
        return
    print(
        "Found public.xml in the base APK, fixing resource identifiers across split APKs."
    )

    # Mappings of resource IDs and names
    idToDummyName = {}
    dummyNameToRealName = {}

    # Step 1) Find all resource IDs that apktool has assigned a name of APKTOOL_DUMMY_XXX to.
    #        Load these into the lookup tables ready to resolve the real resource names from
    #        the split APKs in step 2 below.
    baseXmlTree = xml.etree.ElementTree.parse(
        os.path.join(baseapkdir, "res", "values", "public.xml")
    )
    for el in baseXmlTree.getroot():
        if "name" in el.attrib and "id" in el.attrib:
            if (
                el.attrib["name"].startswith("APKTOOL_DUMMY_")
                and el.attrib["name"] not in idToDummyName
            ):
                idToDummyName[el.attrib["id"]] = el.attrib["name"]
                dummyNameToRealName[el.attrib["name"]] = None
    print("[+] Resolving " + str(len(idToDummyName)) + " resource identifiers.")

    # Step 2) Parse the public.xml file from each split APK in search of resource IDs matching
    #        those loaded during step 1. Each match gives the true resource name allowing us to
    #        replace all APKTOOL_DUMMY_XXX resource names with the true resource names back in
    #        the base APK.
    found = 0
    for splitdir in splitapkpaths:
        if os.path.exists(os.path.join(splitdir, "res", "values", "public.xml")):
            tree = xml.etree.ElementTree.parse(
                os.path.join(splitdir, "res", "values", "public.xml")
            )
            for el in tree.getroot():
                if "name" in el.attrib and "id" in el.attrib:
                    if el.attrib["id"] in idToDummyName:
                        dummyNameToRealName[idToDummyName[el.attrib["id"]]] = el.attrib[
                            "name"
                        ]
                        found += 1
    print("[+] Located " + str(found) + " true resource names.")

    # Step 3) Update the base APK to replace all APKTOOL_DUMMY_XXX resource names with the true
    #        resource name.
    updated = 0
    for el in baseXmlTree.getroot():
        if "name" in el.attrib and "id" in el.attrib:
            if (
                el.attrib["name"] in dummyNameToRealName
                and dummyNameToRealName[el.attrib["name"]] is not None
            ):
                el.attrib["name"] = dummyNameToRealName[el.attrib["name"]]
                updated += 1
    baseXmlTree.write(
        os.path.join(baseapkdir, "res", "values", "public.xml"),
        encoding="utf-8",
        xml_declaration=True,
    )
    print(
        "[+] Updated "
        + str(updated)
        + " dummy resource names with true names in the base APK."
    )

    # Step 4) Find all references to APKTOOL_DUMMY_XXX resources within other XML resource files
    #        in the base APK and update them to refer to the true resource name.
    updated = 0
    for (root, dirs, files) in os.walk(os.path.join(baseapkdir, "res")):
        for f in files:
            if f.lower().endswith(".xml"):
                try:
                    # Load the XML
                    dbgPrint("[~] Parsing " + os.path.join(root, f))
                    tree = xml.etree.ElementTree.parse(os.path.join(root, f))

                    # Register the namespaces and get the prefix for the "android" namespace
                    namespaces = dict(
                        [
                            node
                            for _, node in xml.etree.ElementTree.iterparse(
                                os.path.join(baseapkdir, "AndroidManifest.xml"),
                                events=["start-ns"],
                            )
                        ]
                    )
                    for ns in namespaces:
                        xml.etree.ElementTree.register_namespace(ns, namespaces[ns])
                    ns = "{" + namespaces["android"] + "}"

                    # Update references to APKTOOL_DUMMY_XXX resources
                    changed = False
                    for el in tree.iter():
                        # Check for references to APKTOOL_DUMMY_XXX resources in attributes of this element
                        for attr in el.attrib:
                            val = el.attrib[attr]
                            if (
                                val.startswith("@")
                                and "/" in val
                                and val.split("/")[1].startswith("APKTOOL_DUMMY_")
                                and dummyNameToRealName[val.split("/")[1]] is not None
                            ):
                                el.attrib[attr] = (
                                    val.split("/")[0]
                                    + "/"
                                    + dummyNameToRealName[val.split("/")[1]]
                                )
                                updated += 1
                                changed = True
                            elif (
                                val.startswith("APKTOOL_DUMMY_")
                                and dummyNameToRealName[val] is not None
                            ):
                                el.attrib[attr] = dummyNameToRealName[val]
                                updated += 1
                                changed = True

                        # Check for references to APKTOOL_DUMMY_XXX resources in the element text
                        val = el.text
                        if (
                            val is not None
                            and val.startswith("@")
                            and "/" in val
                            and val.split("/")[1].startswith("APKTOOL_DUMMY_")
                            and dummyNameToRealName[val.split("/")[1]] is not None
                        ):
                            el.text = (
                                val.split("/")[0]
                                + "/"
                                + dummyNameToRealName[val.split("/")[1]]
                            )
                            updated += 1
                            changed = True

                    # Save the file if it was updated
                    if changed == True:
                        tree.write(
                            os.path.join(root, f),
                            encoding="utf-8",
                            xml_declaration=True,
                        )
                except xml.etree.ElementTree.ParseError:
                    print(
                        "[-] XML parse error in "
                        + os.path.join(root, f)
                        + ", skipping."
                    )
    print(
        "[+] Updated "
        + str(updated)
        + " references to dummy resource names in the base APK."
    )
    print("")


####################
# Hack to remove duplicate style resource entries before rebuilding.
#
# Possibly a bug in apktool affecting the Uber app (com.ubercab)
# -> res/values/styles.xml has <style> elements where two child <item> elements had the same name e.g.
#        <item name="borderWarning">@color/ub__ui_core_v2_orange200</item>
#        <item name="borderWarning">@color/ub__ui_core_v2_orange400</item>
# --> Doing an "apktool d com.ubercab.apk" then "apktool b com.ubercab" fails, so not a bug with patch-apk.py.
# --> See: https://github.com/iBotPeaches/Apktool/issues/2240
#
# This hack parses res/values/styles.xml, finds all offending elements, removes them, then saves the result.
####################
def hackRemoveDuplicateStyleEntries(baseapkdir):
    # Bail if there is no styles.xml
    if os.path.exists(os.path.join(baseapkdir, "res", "values", "styles.xml")) == False:
        return
    print(
        "Found styles.xml in the base APK, checking for duplicate <style> -> <item> elements and removing."
    )
    print(
        "[~] Warning: this is a complete hack and may impact the visuals of the app, disable with --disable-styles-hack."
    )

    # Duplicates
    dupes = []

    # Parse styles.xml and find all <item> elements with duplicate names
    tree = xml.etree.ElementTree.parse(
        os.path.join(baseapkdir, "res", "values", "styles.xml")
    )
    for styleEl in tree.getroot().findall("style"):
        itemNames = []
        for itemEl in styleEl:
            if "name" in itemEl.attrib and itemEl.attrib["name"] in itemNames:
                dupes.append([styleEl, itemEl])
            else:
                itemNames.append(itemEl.attrib["name"])

    # Delete all duplicates from the tree
    for dupe in dupes:
        dupe[0].remove(dupe[1])

    # Save the result if any duplicates were found and removed
    if len(dupes) > 0:
        tree.write(
            os.path.join(baseapkdir, "res", "values", "styles.xml"),
            encoding="utf-8",
            xml_declaration=True,
        )
        print("[+] Removed " + str(len(dupes)) + " duplicate entries from styles.xml.")
    print("")


####################
# Update AndroidManifest.xml to disable APK splitting.
# -> Removes the "isSplitRequired" attribute of the "application" element.
# -> Sets the "extractNativeLibs" attribute of the "application" element.
# -> Removes meta-data elements with the name "com.android.vending.splits" or "com.android.vending.splits.required"
####################
def disableApkSplitting(baseapkdir):
    print("Disabling APK splitting in AndroidManifest.xml of base APK.")

    # Load AndroidManifest.xml
    tree = xml.etree.ElementTree.parse(os.path.join(baseapkdir, "AndroidManifest.xml"))

    # Register the namespaces and get the prefix for the "android" namespace
    namespaces = dict(
        [
            node
            for _, node in xml.etree.ElementTree.iterparse(
                os.path.join(baseapkdir, "AndroidManifest.xml"), events=["start-ns"]
            )
        ]
    )
    for ns in namespaces:
        xml.etree.ElementTree.register_namespace(ns, namespaces[ns])
    ns = "{" + namespaces["android"] + "}"

    # Disable APK splitting
    appEl = None
    elsToRemove = []
    for el in tree.iter():
        if el.tag == "application":
            appEl = el
            if ns + "isSplitRequired" in el.attrib:
                del el.attrib[ns + "isSplitRequired"]
            if ns + "extractNativeLibs" in el.attrib:
                el.attrib[ns + "extractNativeLibs"] = "true"
            if ns + "logo" in el.attrib:
                if "DUMMY" in el.attrib[ns + "logo"]:
                    el.attrib[ns + "logo"] = el.attrib[ns + "icon"]
        elif appEl is not None and el.tag == "meta-data":
            if ns + "name" in el.attrib:
                if el.attrib[ns + "name"] == "com.android.vending.splits.required":
                    elsToRemove.append(el)
                elif el.attrib[ns + "name"] == "com.android.vending.splits":
                    elsToRemove.append(el)
    for el in elsToRemove:
        appEl.remove(el)

    # Save the updated AndroidManifest.xml
    tree.write(
        os.path.join(baseapkdir, "AndroidManifest.xml"),
        encoding="utf-8",
        xml_declaration=True,
    )
    print("")


####################
# Main
####################
if __name__ == "__main__":
    main()
