#!/usr/bin/python3
import argparse
import os
import pkg_resources
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree
import xml.etree.ElementTree as ET
from glob import glob
from sys import exit
from pathlib import Path

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

    myFixPublicResourcesIds3(baseapkdir, splitapkpaths)

    # Walk the extracted APK directories and copy files and directories to the base APK
    copySplitApkFiles(baseapkdir, splitapkpaths)

    # # Fix public resource identifiers
    # myFixPublicResourcesIds2(baseapkdir, splitapkpaths)

    # # Hack: Delete duplicate style resource entries.
    if disableStylesHack == False:
        hackRemoveDuplicateStyleEntries(baseapkdir)

    # fixDuplicatePublicIds(baseapkdir)

    # # Disable APK splitting in the base AndroidManifest.xml file
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

    # Return the new APK path
    return os.path.join(baseapkdir, "dist", baseapkfilename)


def fixDuplicatePublicIds(baseapkdir):
    print("KZK", baseapkdir)

    baseXmlTree = xml.etree.ElementTree.parse(
        os.path.join(baseapkdir, "res", "values", "public.xml")
    )

    root = baseXmlTree.getroot()
    nodes = root.findall("./public")

    cache = {}
    to_remove = []
    for n in nodes:
        t = n.attrib["type"]
        name = n.attrib["name"]
        k = f"{t}--{name}"
        v = n.attrib["id"]

        if k in cache:
            print(f"FOUND! key: {k} v1: {v} v2: {cache[k]}")
            to_remove.append(n)
        else:
            cache[k] = v

    if to_remove:
        for n in to_remove:
            root.remove(n)

        baseXmlTree.write(
            os.path.join(baseapkdir, "res", "values", "public.xml"),
            encoding="utf-8",
            xml_declaration=True,
        )


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
                    ) and any(x in f.lower() for x in ["ids", "public", "styles", "drawables"]):
                        continue
                    dbgPrint("[+] Moving file to base APK: " + p[len(baseapkdir) :])
                    shutil.move(os.path.join(root, f), p)
    print("")

from dataclasses import dataclass

@dataclass
class DummyResource:
    dummyName: str
    res_type: str
    res_id: str
    realName: str = None

@dataclass
class RenameResource:
    res_name_from: str
    res_name_to: str
    res_type: str

class DummyResources:

    def __init__(self):
        self.store = []

    def addFromBase(self, dummyName, res_type, res_id):
        r = DummyResource(dummyName, res_type, res_id)
        self.store.append(r)

    def buildCacheById(self):
        self.cache_by_id = {f'{r.res_type}---{r.res_id}':r for r in self.store}

    def buildCacheByDummyName(self):
        self.cache_by_dummyName = {f'{r.res_type}---{r.dummyName}':r for r in self.store}


    def findById(self, res_type, res_id):
        if not hasattr(self, 'cache_by_id'):
            self.buildCacheById()

        return self.cache_by_id[f'{res_type}---{res_id}']

    def findByDummyName(self, res_type, dummyName):
        if not hasattr(self, 'cache_by_dummyName'):
            self.buildCacheByDummyName()

        return self.cache_by_dummyName.get(f'{res_type}---{dummyName}')

    def getItemsWithRealName(self):
        return [r for r in self.store if r.realName ]

def myFixPublicResourcesIds3(baseapkdir, splitapkpaths):
    basePublicXml = Path(baseapkdir) / "res" / "values" / "public.xml"

    ## cache ids in the public.xml of the base
    ids_in_base_public = {}
    baseXmlTree = xml.etree.ElementTree.parse(basePublicXml)
    for el in baseXmlTree.getroot():
        if "name" in el.attrib and "id" in el.attrib and "type" in el.attrib:
            ids_in_base_public[el.attrib['id']] = DummyResource(el.attrib['name'], el.attrib['type'], el.attrib['id'])


    base_renames = []
    for splitPath in splitapkpaths:
        print(f"Processing {splitPath}....")

        publicXml = Path(splitPath) / "res" / "values" / "public.xml"

        if not publicXml.exists():
            print(f"no public.xml found at {publicXml}")
            continue

        ## for the ones that doesn't exists in base, we should add it.
        to_add = []
        ## for the ones that does exist in base... we should change something
        to_modify = []
        to_not_modify = []

        baseXmlTree = xml.etree.ElementTree.parse(publicXml)
        for el in baseXmlTree.iter():
            if "id" in el.attrib and "name" in el.attrib and "type" in el.attrib:
                res_id = el.attrib['id']
                res_name = el.attrib['name']

                if res_id not in ids_in_base_public:
                    to_add.append(el)
                else:
                    res = ids_in_base_public[res_id]

                    if res.dummyName == res_name:
                        to_not_modify.append(el)
                    else:
                        to_modify.append(el)

        add_elements_to_base_public(basePublicXml, splitPath, to_add)

        split_rename = []

        ## Some validations...
        for el in to_modify:
            res_id = el.attrib['id']
            split_name = el.attrib['name']
            split_type = el.attrib['type']
            base_name = ids_in_base_public[res_id].dummyName
            base_type = ids_in_base_public[res_id].res_type

            if split_type != base_type:
                raise Exception("Assumption: internal ids are not shared between types")
            
            if "APKTOOL_DUMMY" not in split_name and "APKTOOL_DUMMY" not in base_name:
                raise Exception("Assumption: on of the resources name for the same id should not contain APKTOOL_DUMMY")
            if "APKTOOL_DUMMY" in split_name and "APKTOOL_DUMMY" in base_name:
                raise Exception("Assumption: Both resource rename cannot be dummies")
                
            # print(f"res_id {res_id} split: {split_type} {split_name} base: {base_type} {base_name}")

            
            if "APKTOOL_DUMMY" in split_name:
                split_rename.append(RenameResource(split_name, base_name, split_type))
            if "APKTOOL_DUMMY" in base_name:
                base_renames.append(RenameResource(base_name, split_name, base_type))



        print(f"added without modification {len(to_add)}")
        print(f"modified {len(to_modify)}")
        print(f"not added cause they are dupes {len(to_not_modify)}")

        print(f"Replacing in {splitPath} {len(split_rename)} changes")
        replace_in_path(Path(splitPath), split_rename)

    print(f"Replacing in {splitPath} {len(base_renames)} changes")
    replace_in_path(Path(baseapkdir), base_renames)

def replace_in_path(path, renames):
    if not renames:
        return

    rename_cache = {f"@{res_rename.res_type}/{res_rename.res_name_from}":res_rename.res_name_to for res_rename in renames}

    updated = 0
    files = path.rglob("res/**/*.xml")
    for f in files:
        try:
            # Load the XML
            dbgPrint(f"[~] Parsing {f}")
            tree = xml.etree.ElementTree.parse(f)

            # Register the namespaces and get the prefix for the "android" namespace
            namespaces = dict(
                [
                    node
                    for _, node in xml.etree.ElementTree.iterparse(
                        path / "AndroidManifest.xml",
                        events=["start-ns"],
                    )
                ]
            )
            for ns in namespaces:
                xml.etree.ElementTree.register_namespace(ns, namespaces[ns])
            ns = "{" + namespaces["android"] + "}"

            changed = False
            for el in tree.iter():
                for attr in el.attrib:
                    val = el.attrib[attr]

                    if (
                        val.startswith("@")
                        and "/" in val
                    ):
                        res_type = val.split("/")[0][1:]
                        dummyName = val.split("/")[1]
                        k = f"@{res_type}/{dummyName}"
                        
                        if k in rename_cache:
                            el.attrib[attr] = val.replace(dummyName, rename_cache[k])
                            updated += 1
                            changed = True

                    elif "type" in el.attrib:
                        res_type = el.attrib['type']
                        dummyName = val
                        k = f"@{res_type}/{dummyName}"

                        if k in rename_cache:
                            el.attrib[attr] = val.replace(dummyName, rename_cache[k])
                            updated += 1
                            changed = True
                        

                # Check for references to APKTOOL_DUMMY_XXX resources in the element text
                val = el.text
                if (
                    val is not None
                    and val.startswith("@")
                    and "/" in val
                    # and dummyNameToRealName[val.split("/")[1]] is not None
                ):
                    res_type = val.split("/")[0][1:]
                    dummyName = val.split("/")[1]
                    k = f"@{res_type}/{dummyName}"

                    if k in rename_cache:
                        el.text = val.replace(dummyName, rename_cache[k])
                        updated += 1
                        changed = True

            # Save the file if it was updated
            if changed == True:
                print(f"changed {f}")
                tree.write(
                    f,
                    encoding="utf-8",
                    xml_declaration=True,
                )
        except xml.etree.ElementTree.ParseError:
            print(
                "[-] XML parse error in "
                + f
                + ", skipping."
            )
    print(
        "[+] Updated "
        + str(updated)
        + " references to dummy resource names in the base APK."
    )
    print("")
 

def add_elements_to_base_public(basePublicXml, apk_path, elements_to_add):
    baseXmlTree = xml.etree.ElementTree.parse(basePublicXml)
    rootXml = baseXmlTree.getroot()

    for el in elements_to_add:
        name = el.attrib['name']
        res_type = el.attrib['type']
        res_id = el.attrib['id']

        element = ET.Element("public")
        element.attrib['name'] = name
        element.attrib['id'] = res_id
        element.attrib['type'] = res_type
        element.attrib['f'] = apk_path
        element.tail = "\n"                      # Edit the element's tail

        rootXml.insert(0, element)

    baseXmlTree.write(basePublicXml,encoding="utf-8", xml_declaration=True)
        


def fmyFixPublicResourcesIds2(baseapkdir, splitapkpaths):
    """JUST MERGE XML... not changing names"""

    basePublicXml = Path(baseapkdir) / "res" / "values" / "public.xml"
    ## check if there are duplicates
    paths = splitapkpaths + [baseapkdir]

    def getKeyFromElem(el):
        return f"{el.attrib['name']}---{el.attrib['type']}###{el.attrib['id']}"

    def x(p):
        p = Path(p)
        publicXml = p / "res" / "values" / "public.xml"    
        keys = []
        if not publicXml.exists():
            return []

        baseXmlTree = xml.etree.ElementTree.parse(publicXml)
        for el in baseXmlTree.getroot():
            if "name" in el.attrib and "id" in el.attrib and "type" in el.attrib:
                keys.append(getKeyFromElem(el))
        return keys

    ppp = list(map(x, paths))
    for i, p in enumerate(paths):
        print(f"path: {p} elems {len(ppp[i])}" )

    base = ppp[-1]
    base_no_id = [p.split("###")[0] for p in base]
    others = ppp[0:-1]

    for i, o in enumerate(others):
        inBoth = set(base) & set(o)
        onlyInOther = set(o) - set(base)
        print(f"path {paths[i]}  inBoth = {len(inBoth)}  onlyinOther= {len(onlyInOther)}")

    
        o_no_id = [p.split("###")[0] for p in o]

        inBoth_no_id = set(base_no_id) & set(o_no_id)
        onlyInOther_no_id = set(o_no_id) - set(base_no_id)
        print(f" NO IDDS path {paths[i]}  inBoth = {len(inBoth_no_id)}  onlyinOther= {len(onlyInOther_no_id)}")

        baseXmlTree = xml.etree.ElementTree.parse(basePublicXml)
        rootXml = baseXmlTree.getroot()

        for s in onlyInOther:
            print(s)
            name = s.split("---")[0]
            res_type = s.split("---")[1].split("###")[0]
            res_id = s.split("###")[1]

            

            element = ET.Element("public")
            element.attrib['name'] = name
            element.attrib['id'] = res_id
            element.attrib['type'] = res_type
            element.attrib['f'] = paths[i]
            element.tail = "\n"                      # Edit the element's tail

            rootXml.insert(0, element)

        baseXmlTree.write(basePublicXml,encoding="utf-8", xml_declaration=True)
        
    ## Find duplicate ids
    baseXmlTree = xml.etree.ElementTree.parse(basePublicXml)

    ids = {}
    for el in baseXmlTree.iter():
        if "id" in el.attrib:
            res_id = el.attrib["id"]

            if res_id in ids:
                ids[res_id].append(el)
            else:
                ids[res_id] = [el]

    count = 0
    for k, v in ids.items():
        if len(v) > 1:
            res_types = [el.attrib['type'] for el in v]
            res_name =  [el.attrib['name'] for el in v]
            print(f"found id {k} with {len(v)} elements {res_name} {res_types}")
            count = count + 1
    print(f"found {count} duplicates")


def myFixPublicResourcesIds(baseapkdir, splitapkpaths):
    baseapkdir = Path(baseapkdir)

    basePublicXml = baseapkdir / "res" / "values" / "public.xml"

    if not basePublicXml.exists():
        return

    resources = DummyResources()

    baseXmlTree = xml.etree.ElementTree.parse(basePublicXml)
    for el in baseXmlTree.getroot():
        if "name" in el.attrib and "id" in el.attrib and "type" in el.attrib:
            resources.addFromBase(el.attrib['name'], el.attrib['type'], el.attrib['id'])
            
    print(f"[+] KZK Resolving {len(resources.store)} resource identifiers.")


    for splitdir in splitapkpaths:
        publicXml = Path(splitdir) / "res" / "values" / "public.xml"
        if publicXml.exists():
            tree = xml.etree.ElementTree.parse(publicXml)
            for el in tree.getroot():
                if "name" in el.attrib and "id" in el.attrib and "type" in el.attrib:
                    r = resources.findById(el.attrib['type'], el.attrib['id'])
                    r.realName = el.attrib["name"]

    print(f"[+] KZK Located {len(resources.getItemsWithRealName())} true resource names.")
    
    updated = 0
    for el in baseXmlTree.getroot():
        if "name" in el.attrib and "id" in el.attrib and "type" in el.attrib:
            r = resources.findByDummyName(el.attrib['type'], el.attrib['name'])
            if r.realName:
                el.attrib["name"] = r.realName
                updated += 1
    baseXmlTree.write(basePublicXml,encoding="utf-8", xml_declaration=True,
    )
    print(
        "[+] KZK Updated "
        + str(updated)
        + " dummy resource names with true names in the base APK."
    )

    updated = 0
    files = baseapkdir.rglob("res/**/*.xml")
    # for (root, dirs, files) in os.walk(os.path.join(baseapkdir, "res")):
    for f in files:
            # if f.lower().endswith(".xml"):
        try:
            # Load the XML
            dbgPrint(f"[~] Parsing {f}")
            tree = xml.etree.ElementTree.parse(f)

            # Register the namespaces and get the prefix for the "android" namespace
            namespaces = dict(
                [
                    node
                    for _, node in xml.etree.ElementTree.iterparse(
                        baseapkdir / "AndroidManifest.xml",
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
                    ):
                        res_type = val.split("/")[0][1:]
                        dummyName = val.split("/")[1]

                        r = resources.findByDummyName(res_type, dummyName)

                        if r and r.realName:
                            el.attrib[attr] = val.replace(dummyName, r.realName)
                            updated += 1
                            changed = True
                    elif val.startswith("APKTOOL_DUMMY_") and "type" in el.attrib:
                        res_type = el.attrib['type']
                        dummyName = val

                        r = resources.findByDummyName(res_type, dummyName)

                        if r and r.realName:
                            el.attrib[attr] = val.replace(dummyName, r.realName)
                            updated += 1
                            changed = True
                    elif (
                        val.startswith("APKTOOL_DUMMY_")
                    ):
                        print(f"[KZK] WARNING I DONT KNOW THE TYPE HERE {val} {attr}")
                        

                # Check for references to APKTOOL_DUMMY_XXX resources in the element text
                val = el.text
                if (
                    val is not None
                    and val.startswith("@")
                    and "/" in val
                    and val.split("/")[1].startswith("APKTOOL_DUMMY_")
                    # and dummyNameToRealName[val.split("/")[1]] is not None
                ):
                    res_type = val.split("/")[0][1:]
                    dummyName = val.split("/")[1]

                    r = resources.findByDummyName(res_type, dummyName)

                    if r and r.realName:
                        el.text = val.replace(dummyName, r.realName)
                        updated += 1
                        changed = True

            # Save the file if it was updated
            if changed == True:
                tree.write(
                    f,
                    encoding="utf-8",
                    xml_declaration=True,
                )
        except xml.etree.ElementTree.ParseError:
            print(
                "[-] XML parse error in "
                + f
                + ", skipping."
            )
    print(
        "[+] Updated "
        + str(updated)
        + " references to dummy resource names in the base APK."
    )
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

    # # Step 3) Update the base APK to replace all APKTOOL_DUMMY_XXX resource names with the true
    # #        resource name.
    # updated = 0
    # for el in baseXmlTree.getroot():
    #     if "name" in el.attrib and "id" in el.attrib:
    #         if (
    #             el.attrib["name"] in dummyNameToRealName
    #             and dummyNameToRealName[el.attrib["name"]] is not None
    #         ):
    #             el.attrib["name"] = dummyNameToRealName[el.attrib["name"]]
    #             updated += 1
    # baseXmlTree.write(
    #     os.path.join(baseapkdir, "res", "values", "public.xml"),
    #     encoding="utf-8",
    #     xml_declaration=True,
    # )
    # print(
    #     "[+] Updated "
    #     + str(updated)
    #     + " dummy resource names with true names in the base APK."
    # )

    # # Step 4) Find all references to APKTOOL_DUMMY_XXX resources within other XML resource files
    # #        in the base APK and update them to refer to the true resource name.
    # updated = 0
    # for (root, dirs, files) in os.walk(os.path.join(baseapkdir, "res")):
    #     for f in files:
    #         if f.lower().endswith(".xml"):
    #             try:
    #                 # Load the XML
    #                 dbgPrint("[~] Parsing " + os.path.join(root, f))
    #                 tree = xml.etree.ElementTree.parse(os.path.join(root, f))

    #                 # Register the namespaces and get the prefix for the "android" namespace
    #                 namespaces = dict(
    #                     [
    #                         node
    #                         for _, node in xml.etree.ElementTree.iterparse(
    #                             os.path.join(baseapkdir, "AndroidManifest.xml"),
    #                             events=["start-ns"],
    #                         )
    #                     ]
    #                 )
    #                 for ns in namespaces:
    #                     xml.etree.ElementTree.register_namespace(ns, namespaces[ns])
    #                 ns = "{" + namespaces["android"] + "}"

    #                 # Update references to APKTOOL_DUMMY_XXX resources
    #                 changed = False
    #                 for el in tree.iter():
    #                     # Check for references to APKTOOL_DUMMY_XXX resources in attributes of this element
    #                     for attr in el.attrib:
    #                         val = el.attrib[attr]
    #                         if (
    #                             val.startswith("@")
    #                             and "/" in val
    #                             and val.split("/")[1].startswith("APKTOOL_DUMMY_")
    #                             and dummyNameToRealName[val.split("/")[1]] is not None
    #                         ):
    #                             el.attrib[attr] = (
    #                                 val.split("/")[0]
    #                                 + "/"
    #                                 + dummyNameToRealName[val.split("/")[1]]
    #                             )
    #                             updated += 1
    #                             changed = True
    #                         elif (
    #                             val.startswith("APKTOOL_DUMMY_")
    #                             and dummyNameToRealName[val] is not None
    #                         ):
    #                             el.attrib[attr] = dummyNameToRealName[val]
    #                             updated += 1
    #                             changed = True

    #                     # Check for references to APKTOOL_DUMMY_XXX resources in the element text
    #                     val = el.text
    #                     if (
    #                         val is not None
    #                         and val.startswith("@")
    #                         and "/" in val
    #                         and val.split("/")[1].startswith("APKTOOL_DUMMY_")
    #                         and dummyNameToRealName[val.split("/")[1]] is not None
    #                     ):
    #                         el.text = (
    #                             val.split("/")[0]
    #                             + "/"
    #                             + dummyNameToRealName[val.split("/")[1]]
    #                         )
    #                         updated += 1
    #                         changed = True

    #                 # Save the file if it was updated
    #                 if changed == True:
    #                     tree.write(
    #                         os.path.join(root, f),
    #                         encoding="utf-8",
    #                         xml_declaration=True,
    #                     )
    #             except xml.etree.ElementTree.ParseError:
    #                 print(
    #                     "[-] XML parse error in "
    #                     + os.path.join(root, f)
    #                     + ", skipping."
    #                 )
    # print(
    #     "[+] Updated "
    #     + str(updated)
    #     + " references to dummy resource names in the base APK."
    # )
    # print("")


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
