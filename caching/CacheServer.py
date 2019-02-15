from flask import Flask
from flask import request
import requests
import os
from stat import S_ISDIR
import sys
import json
import CacheUtils

app = Flask(__name__)

def makeRequestToParentCache(filename):

    address = app.config.get("parentCacheAddress")

    # make request to parent cache
    try:
        getRequest = requests.get("http://"+address+"/get/"+filename)
    except requests.exceptions.RequestException as error:
        errorMsg = "Error making GET request to parent cache at address "+address+": "+str(error)
        print errorMsg
        return formatGetResponse(500, errorMsg)

    if not getRequest.ok:
        print "Error making GET request to parent cache, returned status code "+str(getRequest.status_code)
        return formatGetResponse(getRequest.status_code, "GET request to parent cache returned status code "+str(getRequest.status_code))

    # load response from parent cache
    try:
        binaryData = getRequest.content
    except ValueError as error:
        print "Error loading json response from parent cache: "+str(error)
        return formatGetResponse(500, error)

    try:
        cacheDir = app.config.get("cacheDir")
    except:
        print "Error accessing Flask config"
        return formatGetResponse(500, "Error accessing Flask config")

    # save file locally
    try:
        f = open(cacheDir+filename, "wb")
        f.write(binaryData)
        f.close()
    except IOError as error:
        print "Error saving cached file locally: "+str(error)
        return formatGetResponse(500, str(error))

    # if all execution suceeded, return 0
    return 0

def get(filename):

    # get directory acting as cache
    try:
        cacheDir = app.config.get("cacheDir")
    except:
        print "Error accessing Flask config"
        return formatGetResponse(500, "Error accessing Flask config")

    # Look for file on disk, if it's not there, get it from parent cache
    try:
        if filename not in os.listdir(cacheDir):
            # if return status == 0, file will have been saved locally
            status = makeRequestToParentCache(filename)
            if status != 0:
                return formatGetResponse(500, status)
    except IOError as error:
        print error
        return formatGetResponse(500, error)

    try:
        f = open(cacheDir+filename, "rb")
        fileContents = f.read()
        f.close()
    except IOError as error:
        print error
        return formatGetResponse(500, error)

    return fileContents

def formatGetResponse(statusCode, errors):
    return json.dumps({"status":statusCode, "errors":str(errors)})+"\n"

def formatPutResponse(statusCode, errors):
    return json.dumps({"status":statusCode, "errors":str(errors)})+"\n"

def put(encryption, binaryData):
    try:
        cacheDir = app.config.get("cacheDir")
    except:
        print "Error accessing Flask config"
        return formatPutResponse(500, "Error accessing Flask config")

    if encryption == "sha256":
        # get hash of file to use as filename
        filename = CacheUtils.calculate_binary_data_cksum(binaryData)
    else:
        print "Can only use sha256 as hashing algorithm"
        return formatPutResponse(200, "Can only use sha256 as hashing algorithm")

    # open file and save contents to it
    try:
        f = open(cacheDir+filename, "wb")
        f.write(binaryData)
        f.close()
    except IOError as error:
        print "Error saving file from PUT request: "+str(error)
        return formatPutResponse(500, error)

    # check that filename matches hashed file contents
    checksum = CacheUtils.calculate_file_cksum((cacheDir+filename))
    if checksum != filename:
        print "File checksum and hash filename do not match, returning checksum"
        return checksum+"\n"

    # return hashed filename
    return filename+"\n"

def push(encryption, filename):
    if encryption != "sha256":
        return "Can only use sha256 hashing algorithm\n"

    try:
        cacheDir = app.config.get("cacheDir")
        address = app.config.get("parentCacheAddress")
    except:
        print "Error accessing Flask config"
        return formatPutResponse(500, "Error accessing Flask config")

    # check that cache has file
    if not CacheUtils.doesFileExist(cacheDir, filename):
        print "Error during push, no such file in cache: "+str(filename)
        return "Error during push, no such file in cache: "+str(filename)+"\n"

    # open file
    try:
        f = open(cacheDir+filename, "rb")
        fileData = f.read()
        f.close()
    except IOError as error:
        print "Error opening file: "+str(error)

    # make put request to parent
    try:
        putReq = requests.put("http://"+address+"/put/"+encryption, data=fileData)
    except requests.exceptions.RequestException as error:
        errorMsg = "Error making PUT request to parent cache at address "+address+": "+str(error)
        print errorMsg
        return formatGetResponse(500, errorMsg)

    # make push request to parent?
    '''try:
        pushRequest = requests.put("http://"+address+"/push/"+filename)
    except requests.exceptions.RequestException as error:
        errorMsg = "Error making GET request to parent cache at address "+address+": "+str(error)
        print errorMsg
        return formatGetResponse(500, errorMsg)'''

    return "success\n"

def info(encryption, filename):
    if encryption != "sha256":
        return "Can only use sha256 hashing algorithm\n"

    try:
        cacheDir = app.config.get("cacheDir")
        address = app.config.get("parentCacheAddress")
    except:
        print "Error accessing Flask config"
        return formatPutResponse(500, "Error accessing Flask config")

    # get file info with os.stat()
    try:
        fileInfo = os.stat(cacheDir+filename)
    except OSError as error:
        print "Error getting file info: "+str(error)
        return "Error getting file info: "+str(error)+"\n"

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
        print "Error constructing json file info"
        return "Error constructing json file info\n"

    return json.dumps(jsonFileInfo)+"\n"

# Get file endpoint
@app.route("/get/<filename>", methods=['GET'])
def getFileEndpoint(filename):
    return get(filename)

# Put file endpoint
@app.route("/put/<encryption>", methods=['PUT'])
def putFileEndpoint(encryption):
    try:
        binaryData = request.get_data()
    except:
        print "Error getting data from PUT request"
        return formatPutResponse(500, "")
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