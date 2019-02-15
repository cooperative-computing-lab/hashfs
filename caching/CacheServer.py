from flask import Flask
from flask import request
import requests
import os
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

def put(filename, binaryData):
    try:
        cacheDir = app.config.get("cacheDir")
    except:
        print "Error accessing Flask config"
        return formatPutResponse(500, "Error accessing Flask config")

    # open file and save contents to it
    try:
        f = open(cacheDir+filename, "wb")
        f.write(binaryData)
        f.close()
    except IOError as error:
        print "Error saving file from PUT request: "+str(error)
        return formatPutResponse(500, error)

    return formatPutResponse(200, "")

# Get file endpoint
@app.route("/get/<filename>", methods=['GET'])
def getFileEndpoint(filename):
    return get(filename)

# Put file endpoint
@app.route("/put/<filename>", methods=['PUT'])
def putFileEndpoint(filename):
    try:
        binaryData = request.get_data()
    except:
        print "Error getting data from PUT request"
        return formatPutResponse(500, "")

    return put(filename, binaryData)

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