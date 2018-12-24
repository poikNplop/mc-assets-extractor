#!/usr/bin/python3
# -*- encoding: utf-8 -*-

import argparse
import os, sys
import re
import glob
import json

parser = argparse.ArgumentParser(description="Extracts assets from hashed format")
parser.add_argument("mcfolder",
                    help="Minecraft data location - must contain assets/indexes and assets/objects")
parser.add_argument("-t", "--table", dest="table", default="latest",
                    help="Version of table to read - defaults to latest")
parser.add_argument("-o", "--output", dest="loc", default="./assets/",
                    help="Folder to write files to - defaults to './assets/'")
parser.add_argument("-r", "--re", "--regex", dest="regex", default=None,
                    help="Regular expression of which files to write")

verbosity = parser.add_mutually_exclusive_group()
verbosity.add_argument("-v", "--verbose", dest="debug", action="count",
                       default=0, help="Increase debug level")
verbosity.add_argument("-q", "--quiet", dest="debug", action="store_const",
                       const=-1, help="Only output errors, not warnings")

def printdebug(level, *text):
    if DEBUG >= level:
        print(*text)
def printwarn(*text):
    if DEBUG >= 0:
        print(*text, file=sys.stderr)

def expandpath(path):
    return(os.path.abspath(os.path.expandvars(os.path.expanduser(path))))

if __name__ == "__main__":
    args = parser.parse_args()

    mcfolder = args.mcfolder
    tablename = args.table
    outputfolder = args.loc
    regexmatch = args.regex
    DEBUG = args.debug

    mcfolder = expandpath(mcfolder)
    if not os.path.exists(mcfolder):
        raise OSError(f"Folder {mcfolder} does not exist")
    if not os.path.exists(f"{mcfolder}/assets"):
        raise OSError(f"Folder {mcfolder}/assets does not exist")
    if not os.path.exists(f"{mcfolder}/assets/objects"):
        raise OSError(f"Folder {mcfolder}/assets/objects does not exist")

    if tablename.lower() == "latest":
        if not os.path.exists(f"{mcfolder}/assets/indexes"):
            raise OSError(f"Folder {mcfolder}/assets/indexes does not exist")
        g = glob.glob(f"{mcfolder}/assets/indexes/*.json")
        new_g = []
        for i in g:
            try: new_g.append(list(map(int, os.path.abspath(i).split("\\")[-1].split(".")[:-1])))
            except ValueError: continue
        try:
            i = max(new_g)
        except ValueError:
            raise OSError("No index tables") 
        i = ".".join(map(str, i))
        table_json = f"{mcfolder}/assets/indexes/{i}.json"
    elif os.path.exists(expandpath(f"{mcfolder}/assets/indexes/{tablename}.json")):
        table_json = expandpath(f"{mcfolder}/assets/indexes/{tablename}.json")
    elif os.path.exists(expandpath(f"{mcfolder}/assets/indexes/{tablename}")):
        table_json = expandpath(f"{mcfolder}/assets/indexes/{tablename}")
    elif os.path.exists(expandpath(tablename)):
        table_json = expandpath(tablename)
    else:
        raise OSError("No index table")
    printdebug(1, f"JSON file address generated: {table_json}")

    outputfolder = expandpath(outputfolder)
    if not os.path.exists(outputfolder):
        printwarn(f"{outputfolder} not found - creating")
        os.makedirs(outputfolder)

    if regexmatch is not None:
        try:
            regexmatch = re.compile(regexmatch)
            printdebug(1, f"Compiled regex: {regexmatch}")
        except re.error as reerror:
            printwarn(f"Invalid regex {regexmatch}: {reerror}")
            regexmatch = None

    with open(table_json, mode="r") as f:
        try:
            json_data = json.load(f)
        except json.decoder.JSONDecodeError as jsonerror:
            raise
        printdebug(1, f"Read json from {table_json}")

    printdebug(1, f"Starting write: {len(json_data['objects'])} items (non-filtered)")
    for k, v in json_data["objects"].items():
        if regexmatch is None or regexmatch.fullmatch(k):
            printdebug(2, f"Matched {k}")
            h = v["hash"]
            printdebug(2, f"Reading hash {h}")
            if os.path.exists(f"{mcfolder}/assets/objects/{h[:2]}/{h}"):
                with open(f"{mcfolder}/assets/objects/{h[:2]}/{h}", mode="rb") as f:
                    data = f.read()
                printdebug(3, f"Read data")
                if not os.path.exists(f"{outputfolder}/{os.path.split(k)[0]}"):
                    os.makedirs(f"{outputfolder}/{os.path.split(k)[0]}")
                if os.path.exists(f"{outputfolder}/{k}"):
                    printwarn(f"{outputfolder}/{k} already exists - overwriting")
                with open(f"{outputfolder}/{k}", mode="wb") as f:
                    f.write(data)
                printdebug(3, f"Wrote data")
            else:
                printwarn("Can't find hash {h}")
        else:
            printdebug(3, f"Failed to match {k}")
    printdebug(1, "Finished write")

    printdebug(0, "Finished.")
    sys.exit()