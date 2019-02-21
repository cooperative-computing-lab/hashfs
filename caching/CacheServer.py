from flask import Flask
from flask import request
from flask import abort
import requests
import os
from stat import S_ISDIR
import sys
import json
import CacheUtils

app = Flask(__name__)

def makeRequestToParentCache(filename):
    # get server config variables
    try:
        address = app.config.get("parentCacheAddress")
        cacheDir = app.config.get("cacheDir")
    except:
        abortAndPrintError(500, "Error accessing Flask config")

    # make request to parent cache
    try:
        getRequest = requests.get("http://"+address+"/get/"+filename)
    except requests.exceptions.RequestException as error:
        abortAndPrintError(500, "Error making GET request to parent cache at address "+address+": "+str(error))

    if not getRequest.ok:
        abortAndPrintError(getRequest.status_code, "Request to parent cache not OK")

    # save file locally
    try:
        with open(cacheDir+filename, "wb") as f:
            f.write(getRequest.content)
    except IOError as error:
        abortAndPrintError(500, "Error saving cached file locally: "+str(error))

    # if all execution suceeded, return 0
    return 0

def get(encryption, filename):
    if encryption != "sha256":
        abortAndPrintError(400, "Can only use sha256 hashing algorithm\n")

    # get cache directory
    try:
        cacheDir = app.config.get("cacheDir")
    except:
        abortAndPrintError(500, "Error accessing Flask config")

    # Look for file on disk, if it's not there, get it from parent cache
    try:
        if filename not in os.listdir(cacheDir):
            makeRequestToParentCache(filename)
    except IOError as error:
        abortAndPrintError(500, error)

    # open file and return binary file contents
    try:
        with open(cacheDir+filename, "rb") as f:
            fileContents = f.read()
    except IOError as error:
        abortAndPrintError(500, error)

    return fileContents

def put(encryption, binaryData):
    # get server config variables
    try:
        cacheDir = app.config.get("cacheDir")
    except:
        abortAndPrintError(500, "Error accessing Flask config")

    if encryption == "sha256":
        # get hash of file to use as filename
        filename = CacheUtils.calculate_binary_data_cksum(binaryData)
    else:
        print "Can only use sha256 as hashing algorithm"
        abortAndPrintError(400, "Can only use sha256 as hashing algorithm")

    # open file and save contents to it
    try:
        with open(cacheDir+filename, "wb") as f:
            f.write(binaryData)
    except IOError as error:
        abortAndPrintError(500, error)

    # return hashed filename
    return filename

def push(encryption, filename):
    if encryption != "sha256":
        return "Can only use sha256 hashing algorithm\n"

    # get server config variables
    try:
        cacheDir = app.config.get("cacheDir")
        address = app.config.get("parentCacheAddress")
    except:
        abortAndPrintError(500, "Error accessing Flask config")

    # check that cache has file
    if not CacheUtils.doesFileExist(cacheDir, filename):
        abortAndPrintError(400, "No such file in cache: "+str(filename))

    # open file
    try:
        with open(cacheDir+filename, "rb") as f:
            fileData = f.read()
    except IOError as error:
        abortAndPrintError(500, error)

    # make put request to parent
    try:
        putReq = requests.put("http://"+address+"/put/"+encryption, data=fileData)
    except requests.exceptions.RequestException as error:
        abortAndPrintError(500, "Error making PUT request to parent cache at address "+address+": "+str(error))

    return "success\n"

def info(encryption, filename):
    if encryption != "sha256":
        return "Can only use sha256 hashing algorithm\n"

    # get server config variables
    try:
        cacheDir = app.config.get("cacheDir")
        address = app.config.get("parentCacheAddress")
    except:
        abortAndPrintError(500, "Error accessing Flask config")

    # get file info with os.stat()
    try:
        fileInfo = os.stat(cacheDir+filename)
    except OSError as error:
        abortAndPrintError(500, error)

    try:
        jsonFileInfo = {}
        if S_ISDIR(fileInfo.st_mode):
            jsonFileInfo["is_dir"] = True
        else:
            jsonFileInfo["is_dir"] = False

        jsonFileInfo["size"] = fileInfo.st_size
        jsonFileInfo["atime"] = fileInfo.st_atime
        jsonFileInfo["mtime"] = fileInfo.st_mtime
    except:
        abortAndPrintError(500, "Error constructing json file info")

    return json.dumps(jsonFileInfo)+"\n"

def abortAndPrintError(statusCode, error):
    print str(error)
    abort(statusCode, str(error))

# Get file endpoint
@app.route("/get/<encryption>/<filename>", methods=['GET'])
def getFileEndpoint(encryption, filename):
    return get(encryption, filename)

# Put file endpoint
@app.route("/put/<encryption>", methods=['PUT'])
def putFileEndpoint(encryption):
    try:
        binaryData = request.get_data()
    except:
        abortAndPrintError(500, "Error getting data from PUT request")
    return put(encryption, binaryData)

# Push file endpoint
@app.route("/push/<encryption>/<filename>", methods=['PUT'])
def pushEndpoint(encryption, filename):
    return push(encryption, filename)

# Info endpoint
@app.route("/info/<encryption>/<filename>", methods=['GET'])
def infoEndpoint(encryption, filename):
    return info(encryption, filename)

if __name__ == '__main__':
    # parse -port, -parent_address, -cache_dir
    usageMsg = "Usage: CacheServer.py --port portNum --parent-address address --dir path"
    portNum = None
    parentAddress = None
    cacheDir = None
    if len(sys.argv) < 4:
        print usageMsg
        sys.exit(-1)
    else:
        try:
            for i in range(len(sys.argv)):
                arg = sys.argv[i]
                if arg[0] == "-":
                    if "port" in arg:
                        portNum = int(sys.argv[i+1])
                    elif "parent-address" in arg:
                        parentAddress = sys.argv[i+1]
                    elif "dir" in arg:
                        cacheDir = CacheUtils.validateDirectory(sys.argv[i+1])
                        if cacheDir == -1:
                            print usageMsg
                            sys.exit(-1)
        except:
            print usageMsg
            sys.exit(-1)

    if portNum != None and parentAddress != None and cacheDir != None:
        app.config["parentCacheAddress"] = parentAddress
        app.config["cacheDir"] = cacheDir
        app.run(host="", port=portNum)
    else:
        print usageMsg
        sys.exit(-1)