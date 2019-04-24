from flask import Flask
from flask import request
from flask import abort
import requests
import os
from stat import S_ISDIR
import sys
import json
import CacheUtils
from optparse import OptionParser

app = Flask(__name__)

def makeRequestToParentCache(encryption, filename):
    # get server config variables
    try:
        address = app.config.get("parentCacheAddress")
        cacheDir = app.config.get("cacheDir")
    except:
        abortAndPrintError(500, "Error accessing Flask config")

    # check if server has parent. If it's root, and this method was called, return 404 file not found
    if address == -1:
        abortAndPrintError(404, "File not found")

    # make request to parent cache
    try:
        getRequest = requests.get("http://{}/get/{}/{}".format(address, encryption, filename))
    except requests.exceptions.RequestException as error:
        abortAndPrintError(500, "Error making GET request to parent cache at address "+address+": "+str(error))

    if not getRequest.ok:
        abortAndPrintError(getRequest.status_code, "Request to parent cache not OK")

    # save file locally
    try:
        with open("{}/{}".format(cacheDir, filename), "wb") as f:
            f.write(getRequest.content)
    except IOError as error:
        abortAndPrintError(500, "Error saving cached file locally: "+str(error))

    # if all execution suceeded, return 0
    return 0

def get(encryption, filename):
    if encryption not in CacheUtils.supportedEncryptionAlgs():
        abortAndPrintError(400, "Unsuported encryption algorithm: "+str(encryption))

    # get cache directory
    try:
        cacheDir = app.config.get("cacheDir")
        app.logger.info(cacheDir)
    except:
        abortAndPrintError(500, "Error accessing Flask config")

    # Look for file on disk, if it's not there, get it from parent cache
    try:
        if filename not in os.listdir(cacheDir):
            makeRequestToParentCache(encryption, filename)
    except IOError as error:
        abortAndPrintError(500, error)

    # open file and return binary file contents
    try:
        with open("{}/{}".format(cacheDir, filename), "rb") as f:
            fileContents = f.read()
    except IOError as error:
        abortAndPrintError(500, error)

    return fileContents

def put(encryption, uploaded_files):
    if encryption not in CacheUtils.supportedEncryptionAlgs():
        abortAndPrintError(400, "Unsuported encryption algorithm: "+str(encryption))

    # get server config variables
    try:
        cacheDir = app.config.get("cacheDir")
    except:
        abortAndPrintError(500, "Error accessing Flask config")

    file_names = []
    for fileStorageObj in uploaded_files:
        binaryData = fileStorageObj.read()

        # get hash of file to use as filename
        filename = CacheUtils.calculate_binary_data_cksum(binaryData, encryption)

        # open file and save contents to it
        try:
            with open("{}/{}".format(cacheDir, filename), "wb") as f:
                f.write(binaryData)
            file_names.append(filename)
        except IOError as error:
            # abortAndPrintError(500, error)
            print "Could not PUT file "+fileStorageObj.filename+", error:"+str(error)
            file_names.append("NULL")

    # return hashed filename
    return str(file_names)

def push(encryption, filename):
    if encryption not in CacheUtils.supportedEncryptionAlgs():
        abortAndPrintError(400, "Unsuported encryption algorithm: "+str(encryption))

    # get server config variables
    try:
        cacheDir = app.config.get("cacheDir")
        address = app.config.get("parentCacheAddress")
    except:
        abortAndPrintError(500, "Error accessing Flask config")

    # check if server has parent, if not, return ok
    if address == -1:
        abortAndPrintError(200, "No parent to push to")

    # check that cache has file
    if not CacheUtils.doesFileExist(cacheDir, filename):
        abortAndPrintError(404, "No such file in cache: "+str(filename))

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
    if encryption not in CacheUtils.supportedEncryptionAlgs():
        abortAndPrintError(400, "Unsuported encryption algorithm: "+str(encryption))

    # get server config variables
    try:
        cacheDir = app.config.get("cacheDir")
    except:
        abortAndPrintError(500, "Error accessing Flask config")

    # get file info with os.stat()
    try:
        fileInfo = os.stat(cacheDir+filename)
    except OSError as error:
        if error.errno == 2:
            abortAndPrintError(404, "Not such file in cache: "+str(filename))
        else:
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
        uploaded_files = request.files.getlist("file")
    except:
        abortAndPrintError(500, "Error getting data from PUT request")
    return put(encryption, uploaded_files)

# Push file endpoint
@app.route("/push/<encryption>/<filename>", methods=['PUT'])
def pushEndpoint(encryption, filename):
    return push(encryption, filename)

# Info endpoint
@app.route("/info/<encryption>/<filename>", methods=['GET'])
def infoEndpoint(encryption, filename):
    return info(encryption, filename)

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("--port", dest="port", default="9999",
                        help="Specify a port for the server to run on [default: %default]")
    parser.add_option("--dir", dest="cachedir", default="/tmp/hashfs",
                        help="Specify a directory to be used as cache directory [default: %default]")
    parser.add_option("--parent-address", dest="parent", default="None",
                        help="Specify the address for a parent server [default: %default]")
    (options, args) = parser.parse_args()

    cacheDir = CacheUtils.validateDirectory(options.cachedir)
    if cacheDir == -1:
        print "Error validating directory "+str(options.cachedir)
        sys.exit(-1)

    app.config["parentCacheAddress"] = options.parent
    app.config["cacheDir"] = cacheDir
    app.run(host="0.0.0.0", port=options.port)
